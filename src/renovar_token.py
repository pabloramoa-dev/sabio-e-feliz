"""Renovação automática da credencial do Instagram.

A credencial de longa duração vale 60 dias. Sem renovar, o canal para sozinho
— e como não existe mais ninguém aprovando post a post, ninguém perceberia
até a publicação falhar. Por isso a renovação é automática e roda toda semana.

Fluxo:
  1. GET graph.instagram.com/refresh_access_token  -> credencial nova, +60 dias
  2. grava o valor novo no Secret IG_ACCESS_TOKEN_SABIO pela API do GitHub,
     criptografado com a chave pública do repositório, como a API exige

O passo 2 precisa de um PAT no Secret GH_PAT com permissão de escrita em
Secrets. Sem ele o script NÃO imprime o valor novo — isso vazaria a
credencial no log público do Actions. Ele falha avisando que a troca precisa
ser feita à mão pela tela de Secrets.

    python -m src.renovar_token
    python -m src.renovar_token --so-conferir    # só diz quantos dias faltam
"""
from __future__ import annotations

import json
import os
import sys
from base64 import b64encode

import requests

from src import config

TIMEOUT = 30
NOME_SECRET = "IG_ACCESS_TOKEN_SABIO"


def renovar(credencial: str) -> dict:
    """Pede à Meta uma credencial nova com validade estendida."""
    r = requests.get(
        "https://graph.instagram.com/refresh_access_token",
        params={"grant_type": "ig_refresh_token", "access_token": credencial},
        timeout=TIMEOUT,
    )
    if r.status_code >= 400:
        raise RuntimeError(
            f"renovação recusada: HTTP {r.status_code} {config.esconder(r.text)[:300]}")
    dados = r.json()
    if "access_token" not in dados:
        raise RuntimeError("a Meta respondeu sem o campo esperado")
    return dados


def gravar_secret(repo: str, pat: str, valor: str) -> None:
    """Grava o Secret já criptografado — a API do GitHub não aceita texto puro."""
    from nacl import encoding, public   # só é preciso na hora de gravar

    cabecalho = {"Authorization": f"Bearer {pat}",
                 "Accept": "application/vnd.github+json"}

    resposta = requests.get(
        f"https://api.github.com/repos/{repo}/actions/secrets/public-key",
        headers=cabecalho, timeout=TIMEOUT,
    )
    resposta.raise_for_status()
    chave = resposta.json()

    caixa = public.SealedBox(
        public.PublicKey(chave["key"].encode(), encoding.Base64Encoder()))
    cifrado = b64encode(caixa.encrypt(valor.encode())).decode()

    r = requests.put(
        f"https://api.github.com/repos/{repo}/actions/secrets/{NOME_SECRET}",
        headers=cabecalho, timeout=TIMEOUT,
        json={"encrypted_value": cifrado, "key_id": chave["key_id"]},
    )
    if r.status_code >= 300:
        raise RuntimeError(f"não consegui gravar o Secret: HTTP {r.status_code}")


def main() -> int:
    cfg = config.carregar(exigir_credenciais=True)

    try:
        dados = renovar(cfg.ig_token)
    except Exception as erro:
        print(json.dumps({"ok": False, "erro": config.esconder(str(erro))},
                         ensure_ascii=False, indent=2))
        return 1

    dias = int(dados.get("expires_in", 0)) // 86400
    saida = {"ok": True, "validade_dias": dias, "secret_atualizado": False}

    if "--so-conferir" in sys.argv:
        print(json.dumps(saida, ensure_ascii=False, indent=2))
        return 0

    pat = os.getenv("GH_PAT", "")
    repo = os.getenv("GITHUB_REPOSITORY", "")
    if not pat or not repo:
        saida.update({
            "ok": False,
            "erro": ("credencial renovada na Meta, mas não há GH_PAT para gravar o "
                     "Secret. O valor novo NÃO foi impresso, de propósito. "
                     "Atualize o Secret pela tela de Settings."),
        })
        print(json.dumps(saida, ensure_ascii=False, indent=2))
        return 1

    try:
        gravar_secret(repo, pat, dados["access_token"])
    except Exception as erro:
        saida.update({"ok": False, "erro": config.esconder(str(erro))})
        print(json.dumps(saida, ensure_ascii=False, indent=2))
        return 1

    saida["secret_atualizado"] = True
    print(json.dumps(saida, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
