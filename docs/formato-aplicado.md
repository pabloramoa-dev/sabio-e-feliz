# Formato padrão de Reel: Provérbio aplicado à vida real

Aprovado em 11/11/2026 a partir do piloto de Provérbios 15:1. **Somente Reels**, os carrosséis continuam independentes.

## Regra editorial (quatro falas)

1. **Passagem**: ler literalmente um versículo único do banco `conteudo/proverbios.json`. Ele já é a primeira fala (sem introdução ou título narrado).
2. **Exemplo**: contar uma situação cotidiana concreta. Não apenas uma interpretação abstrata.
3. **Aplicação**: dar uma orientação simples que a pessoa possa colocar em prática.
4. **Convite**: uma única frase de envio ligada ao tema. Nada de pedir vários engajamentos.

O texto da legenda mantém a referência bíblica e identifica a interpretação como paráfrase. Não inventar promessas de prosperidade, curas ou punição.

## Motor

- `conteudo/cenas_aplicadas.json`: banco editorial de 42 situações e ações, duas variações para cada um dos 21 versículos já revisados. O JSON pode ser expandido manualmente.
- `estudio/aplicado.py`: transforma um modelo editorial em item `estilo=aplicado_v1`; valida a correspondência literal com a base bíblica e alterna variações.
- `estudio/reserva.py`: repõe episódios usando apenas modelos existentes e cenas previamente escritas. **Não criar um Reel sem um exemplo revisado**.
- `estudio/roteiro.py`: quatro segmentos (`passagem`, `reflexao`, `aplicacao`, `cta`) nessa ordem, sem `gancho` ou `abertura` narrados.
- `estudio/voz.py`: mistura Kokoro original, velocidade 0,94, sem encurtar ou remover explicações.
- `estudio/hyperframes.py` e `estudio/hf_sabio.py`: continuam responsáveis pela animação e pela composição.
- `src/fila.py`: bloqueia publicação de novos vídeos fora do padrão; a guarda de integridade dos MP4 e os limites de uma publicação por dia permanecem.
- `src/reabastecer.py`: considera reserva apenas os Reels no formato aplicado.

## Migração da fila

EP-071 a EP-091 ainda não foram publicados; foram atualizados para o novo roteiro e voltaram a `rascunho`. Seus hashes e aprovações anteriores foram invalidados. O workflow de reabastecimento renderiza, valida e reapresenta/autoaprova conforme as regras existentes. **Nenhum episódio com MP4 antigo entra no ar**.

EP-001 a EP-070 estão publicados; não alteramos nem republicamos suas mídias e históricos. Os carrosséis das 18h não mudaram.

## Verificação

```bash
pytest -q tests/test_aplicado.py tests/test_base.py tests/test_selecao.py
python -m src.conferir
python -m estudio.reserva --reels 1 --semente regressao  # modifica a fila; use apenas em clone descartável
```

O workflow `Reabastecer o canal (piloto automático)` pode renderizar até três Reels pendentes por execução e continua sem publicar diretamente. A publicação permanece separada às 9h, com suas credenciais e travas anteriores.

Se os exemplos começarem a se repetir, acrescente mais casos revisados ao JSON, com aplicações concretas e compatíveis com o sentido do versículo. Não permita fallback para leitura pura.
