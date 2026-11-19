# Piloto — Provérbio aplicado à vida real

**Objetivo:** testar um Reel novo sem modificar a rotina diária do canal.

**Referência:** Provérbios 15:1 (texto lido diretamente de `conteudo/proverbios.json`).

**Falas, nesta ordem:**
1. O Sábio lê o versículo completo, sem apresentação.
2. Mostra um exemplo concreto: alguém em casa fala irritado e a pessoa quase responde no mesmo tom.
3. Oferece uma ação prática: conversar calmamente e estabelecer limites sem ofender.
4. Um único convite de envio, contextualizado.

**Visual e áudio:** motores existentes `estudio/voz.py`, `estudio/hyperframes.py`, `estudio/hf_sabio.py`, `estudio/sabio_vivo.py` com a voz original `pm_alex+im_nicola`.

## Como testar

```bash
python -m pilotos.proverbio_aplicacao --roteiro
python -m pilotos.proverbio_aplicacao
```

O arquivo é gerado em `output/pilotos/proverbio-aplicacao/sabio-proverbio-aplicado-15-1.mp4`.
No GitHub Actions, o workflow **Piloto — provérbio aplicado (não publicar)** produz o MP4 como artefato para análise.

### Segurança editorial

- Nenhum episódio é inserido em `conteudo/fila.json`.
- Nada é marcado como aprovado.
- Nenhuma credencial do Instagram é lida e nenhuma publicação é feita.
- A produção fica isolada da agenda existente.
- O texto bíblico é obtido diretamente da base do próprio repositório, sem reescrever a citação.

Depois de assistir ao piloto, decidir se vale testar novos provérbios no mesmo formato.
