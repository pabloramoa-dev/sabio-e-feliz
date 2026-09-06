"""Cliente da Instagram Graph API — Reels e carrosséis.

Reel: POST /media (media_type=REELS) -> aguardar FINISHED -> POST /media_publish.
Carrossel: um POST /media por imagem (is_carousel_item) -> POST /media com
media_type=CAROUSEL e a lista de filhos -> POST /media_publish.

Nada é publicado com PUBLICAR_ATIVO desligado.
"""
from __future__ import annotations

import time

import requests

from src.config import Config, esconder

TIMEOUT = 30
ESPERA_ENTRE_TENTATIVAS = 10
MAX_TENTATIVAS_CONTAINER = 36  # ~6 minutos


class ErroInstagram(RuntimeError):
    pass


class Publicador:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    # -- diagnóstico ---------------------------------------------------------
    def conferir_conta(self) -> dict:
        r = requests.get(
            self.cfg.base_conta,
            params={"fields": "id,username,media_count", "access_token": self.cfg.ig_token},
            timeout=TIMEOUT,
        )
        self._checar(r)
        return r.json()

    # -- publicação ----------------------------------------------------------
    def criar_container(self, url_video: str, legenda: str) -> str:
        r = requests.post(
            f"{self.cfg.base_conta}/media",
            data={
                "media_type": "REELS",
                "video_url": url_video,
                "caption": legenda,
                "share_to_feed": "true",
                "access_token": self.cfg.ig_token,
            },
            timeout=TIMEOUT,
        )
        self._checar(r)
        return r.json()["id"]

    # -- carrossel -----------------------------------------------------------
    def criar_item_carrossel(self, url_imagem: str) -> str:
        """Cada imagem vira um container filho, sem legenda própria."""
        r = requests.post(
            f"{self.cfg.base_conta}/media",
            data={
                "image_url": url_imagem,
                "is_carousel_item": "true",
                "access_token": self.cfg.ig_token,
            },
            timeout=TIMEOUT,
        )
        self._checar(r)
        return r.json()["id"]

    def criar_container_carrossel(self, filhos: list[str], legenda: str) -> str:
        """O container-pai: é ele que carrega a legenda e a ordem dos slides."""
        if not 2 <= len(filhos) <= 10:
            raise ErroInstagram(
                f"carrossel precisa de 2 a 10 imagens, recebeu {len(filhos)}")
        r = requests.post(
            f"{self.cfg.base_conta}/media",
            data={
                "media_type": "CAROUSEL",
                "children": ",".join(filhos),
                "caption": legenda,
                "access_token": self.cfg.ig_token,
            },
            timeout=TIMEOUT,
        )
        self._checar(r)
        return r.json()["id"]

    def aguardar_pronto(self, container_id: str) -> None:
        for tentativa in range(MAX_TENTATIVAS_CONTAINER):
            r = requests.get(
                f"{self.cfg.base_graph}/{container_id}",
                params={"fields": "status_code,status", "access_token": self.cfg.ig_token},
                timeout=TIMEOUT,
            )
            self._checar(r)
            estado = r.json().get("status_code")
            if estado == "FINISHED":
                return
            if estado in {"ERROR", "EXPIRED"}:
                raise ErroInstagram(f"container {container_id} terminou em {estado}: {r.json().get('status')}")
            time.sleep(ESPERA_ENTRE_TENTATIVAS)
        raise TimeoutError(f"container {container_id} não ficou pronto a tempo")

    def publicar(self, container_id: str) -> str:
        r = requests.post(
            f"{self.cfg.base_conta}/media_publish",
            data={"creation_id": container_id, "access_token": self.cfg.ig_token},
            timeout=TIMEOUT,
        )
        self._checar(r)
        return r.json()["id"]

    def reconciliar(self, container_id: str) -> str | None:
        """Depois de um timeout na publicação: descobre se o Reel entrou mesmo.

        Evita o pior cenário do plano (publicação duplicada): procura nas
        mídias recentes da conta uma que tenha nascido deste container.
        """
        r = requests.get(
            f"{self.cfg.base_conta}/media",
            params={"fields": "id,caption,timestamp", "limit": 5, "access_token": self.cfg.ig_token},
            timeout=TIMEOUT,
        )
        self._checar(r)
        itens = r.json().get("data", [])
        return itens[0]["id"] if itens else None

    def metricas(self, media_id: str) -> dict:
        r = requests.get(
            f"{self.cfg.base_graph}/{media_id}/insights",
            params={
                "metric": "reach,shares,saved,comments,likes,total_interactions,ig_reels_avg_watch_time,ig_reels_video_view_total_time",
                "access_token": self.cfg.ig_token,
            },
            timeout=TIMEOUT,
        )
        if r.status_code >= 400:
            # métrica ausente é "não disponível", nunca zero (Seção 9.3)
            return {"erro": esconder(r.text)[:300]}
        return {m["name"]: m["values"][0].get("value") for m in r.json().get("data", [])}

    # -- interno -------------------------------------------------------------
    @staticmethod
    def _checar(r: requests.Response) -> None:
        if r.status_code >= 400:
            raise ErroInstagram(f"HTTP {r.status_code}: {esconder(r.text)[:500]}")
