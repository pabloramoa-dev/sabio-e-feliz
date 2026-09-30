# Prévia HyperFrames — Provérbios

Ensaio isolado do EP-001 (Provérbios 15:1), solicitado por Pablo em 30/09/2026.
**Não aprovado para aplicação definitiva. Não publica, não modifica a fila,
não muda o renderizador de produção e não altera workflows.**

Preserva o personagem de `estudio.cena` e a voz original
`pm_alex+im_nicola`, velocidade 0,94. A composição adapta o compositor
HyperFrames aprovado da Nina: cartões, câmera, transições, legendas por
palavra, trilha original sintetizada, efeitos sonoros e CTA do próprio episódio.
As posições das palavras são estimadas dentro de frases alinhadas aos silêncios.

## Reproduzir

Na raiz do repositório, com dependências do estúdio instaladas:

```bash
npm ci --prefix experiments/hyperframes-preview
npx --prefix experiments/hyperframes-preview hyperframes browser ensure
python experiments/hyperframes-preview/preview.py
```

Pode-se definir `HYPERFRAMES_BROWSER_PATH` para um Chromium já instalado.
O comando gera `../Proverbios_HyperFrames_Teste.mp4`, 1080×1920, 30 fps,
com cerca de 32 segundos. `--prepare-only` prepara as camadas sem render final.
O modelo Kokoro é baixado pelo módulo original do estúdio quando necessário.

Após aprovação visual do usuário, a etapa seguinte é generalizar este
adaptador para os formatos da fila e integrar ao estúdio. Isso ainda não foi feito.
