# ARARA-M14 — Nota de implementação congelada

**Versão:** 14.0

O M14 reutiliza o núcleo emparelhado M9 com:

- fração fixa em \(t_{50}\);
- grade estreita \(10.5, 11.0, 11.5, 12.0\sigma\);
- seeds novas.

Gerador, SBW, alinhamento-oráculo, limiar, bootstrap e critérios permanecem congelados.

O holdout será aberto uma única vez.
