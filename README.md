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
| `estudio/` | Produção: roteiro, voz Kokoro, cena Manim e render |
| `estudio/previsao_lib.py` · `dvh_lib.py` | Bibliotecas do @previsaosulflu, trazidas sem alteração |
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
pip install -r requirements.txt -r requirements-estudio.txt
python -m src.conferir                     # confere a fila
python -m estudio.produzir --id EP-001     # produz um Reel
python -m estudio.produzir --id EP-001 --mudo   # só o visual, sem rede
DRY_RUN=true python -m src.main            # ensaio de publicação
pytest -q
```

## Personagem e voz

Quem apresenta é o **Seu Ranzinza** — exatamente o mesmo personagem do
@previsaosulflu. Os dois arquivos dele, `previsao_lib.py` e `dvh_lib.py`,
foram trazidos para `estudio/` sem alteração nenhuma: mesmo traço, mesmo
mundo visual, mesma família de canais. Ele entra no humor **"desconfiado"**,
não no "bravo" — aqui ele não está reclamando do tempo.

O que muda é o lugar: em vez da varanda, uma manhã com janela, mesa, planta
e caneca. O canal de provérbios tem o cenário dele.

O vídeo é renderizado em **Manim**. A boca abre e fecha pela amplitude do
áudio, e o updater fica pendurado num Dot invisível, nunca no personagem —
animar um submobjeto tira o grupo de `scene.mobjects` e mata todos os
updaters dele, sem erro nenhum. A posição da boca aberta é medida a partir
da boca do próprio personagem, então o mesmo código serve para o Ranzinza e
para a Dona Maria sem número mágico.

### A voz

Narração neural local com **Kokoro**, sem chave e sem cota. Serviços de TTS
na nuvem foram descartados porque bloqueiam chamada vinda de datacenter — o
runner do GitHub leva 403.

A voz do canal é uma **mistura**: `pm_alex+im_nicola`, meio a meio. O sinal
de mais combina os dois vetores de estilo e cria uma voz que não existe
solta no modelo — masculina e grave, com o corpo do italiano e a dicção da
portuguesa. Para mexer no equilíbrio basta mudar a string:
`pm_alex:0.7+im_nicola:0.3`.

Velocidade em **0,94**. Esse número entra ANTES da síntese, na hora em que o
modelo decide quanto dura cada som: ele fala mais devagar de verdade, com
vogal longa e pausa que respira. Não é o áudio esticado depois, que soa
como fita arrastada.

A legenda karaokê acerta porque a narração é sintetizada **por bloco de
ideia** — nunca frase por frase, que reinicia a entonação a cada respiro e é
o que mais soa robótico. Dentro do bloco, cada fronteira de frase é estimada
pelo tamanho do texto e depois puxada para o silêncio real mais próximo.

A referência bíblica é expandida antes de falar: "Provérbios 15:1" vira
"Provérbios, capítulo quinze, versículo um". Sem isso o fonetizador lê
"quinze:um" grudado e sai "quinzum".

O modelo (330 MB) fica em cache entre execuções e não é versionado.

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
