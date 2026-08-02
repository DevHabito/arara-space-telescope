# ARARA-M6 — Nota de implementação congelada

**Versão:** 6.0

O M6 importa o gerador M2 e o operador/estatística M5. Os hashes serão congelados.

## Tempo de fração

Para cada sinal não negativo com amplitude final \(A=\max_k s_k\):

\[
t_f=\min\{k:s_k\geq fA\},
\qquad f=0.50.
\]

## Positivos

Usam sinal verdadeiro, onset verdadeiro e contribuição SBW exata, como no M5.

## Negativos

Usam uma hipótese virtual independente por curva. O pseudo-\(t_{50}\) é calculado na forma virtual.

## Estatística, limiar e intervalos

Idênticos ao M5. A única mudança científica é \(0.25\rightarrow0.50\).

## Holdout

A abertura será marcada antes da geração e uma segunda execução será recusada.
