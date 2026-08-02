# ARARA-M11 — Nota de implementação congelada

**Versão:** 11.0

O M11 usa diretamente o núcleo M9, com três mudanças congeladas:

- fração final: `0.75`;
- grade de SNR: `8.0, 8.5, 9.0, 9.5, 10.0`;
- seeds novas.

Todos os critérios estatísticos permanecem iguais ao M9. O nome interno legado do parâmetro de falha forte do núcleo M9 não altera seu significado: ele se aplica ao maior SNR da grade M11, isto é, 10σ.

O holdout será aberto uma única vez.
