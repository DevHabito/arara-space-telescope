# ARARA-M13 — Nota de implementação congelada

**Versão:** 13.0

O M13 usa o núcleo emparelhado M9, alterando somente:

- fração final: \(t_{50}\);
- grade de SNR: \(10,12,14,16,18\);
- seeds;
- previsão.

Os critérios estatísticos, o gerador, o SBW, o alinhamento-oráculo e o procedimento de limiar permanecem iguais.

O parâmetro interno legado `strong_fail_snr12_recall_upper` do núcleo M9 é aplicado ao maior nível da grade M13, isto é, 18σ.

O holdout será aberto uma única vez.
