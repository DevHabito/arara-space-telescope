# ARARA-M8 — Nota de implementação congelada

**Versão:** 8.0

O M8 preserva o gerador, operador SBW, estatística alinhada, limiar e intervalos do M7.

A única mudança científica é:

\[
t_{75}\rightarrow t_{100}.
\]

O instante \(t_{100}\) é a primeira amostra que alcança o máximo final da curva injetada. Para as formas do gerador, isso coincide com o fim da duração sorteada.

Seeds, previsão e critérios são os registrados no pré-registro M8. O holdout será aberto uma única vez.
