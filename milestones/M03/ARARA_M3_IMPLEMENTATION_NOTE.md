# ARARA-M3 — Nota de implementação congelada

**Versão:** 3.0  
**Estado:** congelada antes da geração de dados.

## 1. Dependência congelada

O gerador, as famílias, a estatística de inclinação, o primeiro cruzamento, o limiar conservador e Clopper–Pearson são importados do arquivo:

`../m2/arara_m2.py`

O hash SHA-256 desse arquivo será incluído no congelamento pré-holdout.

## 2. Padronização raw

Para cada estrela:

\[
x_{j,k}=
\frac{y_{j,k}-\mu_j}{\sigma_j},
\]

com mediana e MAD estimados nos índices 0–49 e piso de escala \(10^{-8}\).

Nenhum filtro temporal é aplicado antes da construção de \(q_k\).

## 3. Beta

\[
q_k=\operatorname{median}_{j=1,\ldots,8}x_{j,k}.
\]

Beta usa todos os 50 pontos da baseline, com intercepto por centralização. Se \(\operatorname{Var}(q)<10^{-12}\), beta é zero. Depois, beta é limitado a \([0,3]\).

## 4. Resíduo

\[
e_k=x_{0,k}-\widehat\beta q_k.
\]

Na baseline do próprio resíduo:

\[
\mu_e=\operatorname{median}(e_{0:49}),
\]

\[
\sigma_e=1.4826\operatorname{MAD}(e_{0:49}),
\]

com piso \(10^{-8}\).

O AR(1) é estimado por Yule–Walker nos pares de baseline e limitado a \([0,0.8]\).

## 5. Branqueamento final

Para \(k=0\):

\[
r_0=(e_0-\mu_e)/\sigma_e.
\]

Para \(k\geq1\):

\[
r_k=
\frac{
(e_k-\mu_e)-\widehat\phi_e(e_{k-1}-\mu_e)
}{\sigma_e}.
\]

## 6. Comparador WBS

É a saída residual da função `normalize_field` do M2, sem alteração.

## 7. Limiar e intervalos

São idênticos ao M2:

- no máximo 10 alertas em 2.000 negativos por família no desenvolvimento;
- próximo número representável acima do 11º maior máximo;
- Clopper–Pearson unilateral 95%;
- bootstrap emparelhado estratificado, 10.000 réplicas;
- percentis 5% e 95%.

## 8. Holdout

A abertura será marcada antes da geração. Segunda execução será recusada.
