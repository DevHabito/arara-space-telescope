# ARARA-M7 — Nota de implementação congelada

**Versão:** 7.0

O M7 preserva o operador, o gerador, a estatística e o procedimento estatístico do M6.

A única mudança científica é:

\[
t_{50}\rightarrow t_{75}.
\]

Também mudam somente:

- seeds;
- previsão;
- critérios de promoção e falha previamente registrados.

O tempo de fração é calculado por:

\[
t_f=\min\{k:s_k\geq f\max(s)\},
\qquad f=0.75.
\]

O limiar continua sendo calibrado apenas nos negativos de desenvolvimento, com máximo empírico de 0,5% por família. O holdout será aberto uma única vez.
