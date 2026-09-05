"""Configuração do pipeline @sabioefeliz.

Regra de ouro: nada de segredo em código. Tudo vem de variável de ambiente,
alimentada pelos Secrets/Variables do GitHub Actions.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# --- Caminhos do projeto -----------------------------------------------------
CONTEUDO = RAIZ / "conteudo"
PROVERBIOS_JSON = CONTEUDO / "proverbios.json"
FILA_JSON = CONTEUDO / "fila.json"
PUBLICADOS_JSON = CONTEUDO / "publicados.json"
REELS = RAIZ / "reels"
SAIDA = RAIZ / "output"

# --- Limites operacionais (Seção 15.1 do plano mestre) -----------------------
MAX_PUBLICACOES_POR_DIA = 1
RESERVA_MINIMA = 3          # abaixo disso o vigia-fila abre alerta
DURACAO_MIN_S = 10.0
DURACAO_MAX_S = 90.0
LARGURA = 1080
ALTURA = 1920


@dataclass(frozen=True)
class Config:
    ig_user_id: str
    ig_token: str
    raw_base_url: str
    graph_version: str
    publicar_ativo: bool
    dry_run: bool

    @property
    def base_conta(self) -> str:
        return f"https://graph.facebook.com/{self.graph_version}/{self.ig_user_id}"

    @property
    def base_graph(self) -> str:
        return f"https://graph.facebook.com/{self.graph_version}"


def _flag(nome: str, padrao: str = "false") -> bool:
    return os.getenv(nome, padrao).strip().lower() in {"1", "true", "yes", "sim"}


def carregar(exigir_credenciais: bool = True) -> Config:
    obrigatorias = ["IG_USER_ID_SABIO", "IG_ACCESS_TOKEN_SABIO", "RAW_BASE_URL"]
    if exigir_credenciais:
        faltando = [k for k in obrigatorias if not os.getenv(k)]
        if faltando:
            raise RuntimeError(f"Variáveis obrigatórias ausentes: {faltando}")

    return Config(
        ig_user_id=os.getenv("IG_USER_ID_SABIO", ""),
        ig_token=os.getenv("IG_ACCESS_TOKEN_SABIO", ""),
        raw_base_url=os.getenv("RAW_BASE_URL", "").rstrip("/"),
        graph_version=os.getenv("GRAPH_API_VERSION", "v22.0"),
        publicar_ativo=_flag("PUBLICAR_ATIVO", "false"),
        dry_run=_flag("DRY_RUN", "true"),
    )


def esconder(texto: str) -> str:
    """Nunca deixar token vazar em log."""
    tok = os.getenv("IG_ACCESS_TOKEN_SABIO", "")
    if tok and len(tok) > 8:
        texto = texto.replace(tok, "***TOKEN***")
    return texto
