# Sábio e Feliz · @sabioefeliz

Pipeline automatizado de Reels diários de Provérbios, isolado dos outros canais.

> Um provérbio. Uma decisão melhor. Todos os dias.

## Como este projeto funciona

O GitHub **não inventa interpretação nenhuma**. Ele seleciona conteúdo já
revisado, renderiza, valida, publica e registra. A automação executa decisões
editoriais aprovadas — nunca as toma.

São dois momentos separados, de propósito:

**1. Estúdio (sob demanda)** — workflow `Produzir Reels (estúdio)`
Pega os episódios da fila, gera a narração, desenha o Sábio quadro a quadro,
monta o MP4 1080x1920 e devolve o arquivo para você aprovar.

**2. Publicação (todo dia às 9h)** — workflow `Publicar provérbio do dia`
Escolhe o próximo episódio **aprovado**, confere o arquivo, publica pelo
Instagram Graph API e registra no histórico. Não renderiza nada na hora da
postagem: publica um MP4 que já passou por você.

```
fila.json (aprovado) -> confere sha256 -> ffprobe -> raw URL
   -> container REELS -> aguarda FINISHED -> media_publish
   -> publicados.json -> métricas em 24h e 72h
```

## Estrutura

| Pasta | O que é |
|---|---|
| `conteudo/proverbios.json` | Base integral: 31 capítulos, 915 versículos, Almeida em domínio público |
| `conteudo/fila.json` | Fila editorial: roteiro, formato, status e arquivo de cada episódio |
| `conteudo/publicados.json` | Histórico auditável: media_id, horário, commit e métricas |
| `reels/` | Os MP4 aprovados, servidos por raw URL para a Meta baixar |
| `src/` | Publicação: seleção, validação, cliente da Meta, ledger e métricas |
| `estudio/` | Produção: roteiro, voz, personagem, cenário, legenda e render |
| `tests/` | Testes que rodam a cada push |

## Status de um episódio

`rascunho` → `em_revisao` (já tem MP4) → `aprovado` (você assinou) → `publicado`

Só `aprovado` entra no ar. E a aprovação é amarrada ao **sha256 do MP4**: se o
arquivo mudar depois que você aprovou, a publicação para sozinha.

## Aprovar um episódio

Abra `conteudo/fila.json` pelo GitHub, ache o episódio e mude três campos:

```json
"status": "aprovado",
"aprovado_por": "Pablo",
"aprovado_em": "2026-09-08"
```

## Travas de segurança

- `PUBLICAR_ATIVO` começa em `false`. Enquanto estiver assim, nada vai ao ar.
- `DRY_RUN` liga o ensaio: valida tudo e para antes de falar com a Meta.
- Uma publicação por dia, no máximo.
- Antes de publicar, o robô confere o `username` da conta de destino. Se o token
  apontar para outra conta, ele aborta e chama de incidente.
- Nenhum token aparece em log: as respostas de erro passam por um filtro.
- `concurrency: sabioefeliz-producao` — grupo exclusivo, não encosta nos
  workflows do canal de previsão do tempo.

## Segredos e variáveis (Settings → Secrets and variables → Actions)

Secrets:

| Nome | O que é |
|---|---|
| `IG_USER_ID_SABIO` | ID numérico da conta @sabioefeliz |
| `IG_ACCESS_TOKEN_SABIO` | Token de longa duração com permissão de publicação |

Variables:

| Nome | Valor |
|---|---|
| `RAW_BASE_URL` | `https://raw.githubusercontent.com/SEU-USUARIO/sabio-e-feliz/main` |
| `GRAPH_API_VERSION` | `v22.0` |
| `PUBLICAR_ATIVO` | `false` até o primeiro teste controlado dar certo |

Nomes propositalmente diferentes dos do canal de previsão do tempo: um token
trocado por engano não consegue publicar na conta errada.

## Rodar localmente

```bash
pip install -r requirements.txt
python -m src.conferir                     # confere a fila
python -m estudio.produzir --id EP-001     # produz um Reel
python -m estudio.produzir --id EP-001 --mudo   # só o visual, sem rede
DRY_RUN=true python -m src.main            # ensaio de publicação
pytest -q
```

## Voz

Narração neural local com **Kokoro** (`pm_alex`), a mesma família de voz dos
outros canais. Roda dentro do próprio runner: sem chave, sem cota e sem
depender de serviço de terceiro no ar. Serviços de TTS na nuvem foram
descartados porque bloqueiam chamadas vindas de datacenter — o runner do
GitHub leva 403.

O modelo (330 MB) fica em cache entre as execuções e não é versionado.

A legenda karaokê acerta porque a narração é sintetizada **frase a frase**:
o começo e o fim de cada frase são medidos no áudio de verdade, e só dentro
da frase as palavras são distribuídas por tamanho.

## Fonte do texto bíblico

João Ferreira de Almeida, arquivo `por-almeida.usfx.xml`, declarado domínio
público pelo projeto Open Bibles. **A relação com a edição Almeida 1911 não está
confirmada** — não identificar como Almeida 1911. A contagem estrutural (915
versículos) não equivale a revisão textual: cada episódio ainda passa pela
curadoria antes de virar vídeo.

## O que o robô nunca faz

- Prometer prosperidade, cura, castigo ou previsão de acontecimentos.
- Pedir curtida, comentário, seguida e compartilhamento na mesma respiração.
- Mandar alguém marcar "quem precisa aprender". Compartilhar é cuidado, não acusação.
