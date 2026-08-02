# ARARA From Zero — Pré-registro M20 Adaptive Refinement at 13.75σ, t50

**Versão:** M20.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** refinamento adaptativo prospectivo do intervalo entre 13.5σ e 14σ.

## 1. Pergunta pequena

O nível \(13.75\sigma\) em \(t_{50}\) satisfaz o contrato em dez replicações completas independentes?

## 2. Condição fixa

\[
A/\sigma_0=13.75,\qquad f=0.50.
\]

Não haverá grade de SNR nem busca de fração.

## 3. Status adaptativo

O nível 13.75σ foi escolhido depois de observar:

- M19: 13.5σ, 7/10 passes, `INCONCLUSIVE`;
- M17: 14σ, 10/10 passes, `PASS`.

M20 é um refinamento adaptativo prospectivo. Mesmo que passe, 13.75σ será classificado como `PASS_REFINEMENT_CANDIDATE` e não substituirá 14σ até uma confirmação independente posterior com seeds novas.

## 4. Motivação numérica anterior aos dados

\[
R_{\mathrm{agg}}(13.5\sigma)=0.656570,
\]

\[
R_{\mathrm{agg}}(14\sigma)=0.663930.
\]

Interpolação simples:

\[
\widehat R_{\mathrm{agg}}(13.75\sigma)=0.660250.
\]

A interpolação é somente previsão, não modelo físico.

## 5. Dez replicações completas

Cada replicação possui calibração, limiar, holdout e bootstrap próprios:

- 2.000 negativos por família para calibração;
- 2.500 positivos por cada um dos oito estratos;
- 5.000 negativos por família;
- 20 lotes;
- 10.000 réplicas bootstrap.

Root seeds:

- replicações: `2026081501`;
- bootstrap agregado: `2026081502`.

## 6. Passe por replicação

Uma replicação passa somente se:

1. \(FPR_{\mathrm{upper}}^{95\%}\leq0.01\) em cada família;
2. \(R_{\mathrm{lower}}^{95\%}\geq0.60\);
3. pelo menos 6/8 estratos têm limite inferior \(\geq0.50\);
4. pelo menos 15/20 lotes têm recall \(\geq0.55\).

## 7. Métrica agregada

\[
R_{\mathrm{agg}}=
\frac{1}{10}\sum_{r=1}^{10}
\frac{1}{8}\sum_{h=1}^{8}R_{r,h}.
\]

Intervalo por bootstrap hierárquico com 10.000 réplicas.

## 8. Robustez de falso alerta

Exige:

- pelo menos 9/10 replicações com FPR aprovado;
- nenhuma família com limite superior acima de 1,5%.

## 9. Previsão anterior aos resultados

\[
8\leq N_{\mathrm{PASS}}\leq10,
\]

\[
0.645\leq R_{\mathrm{agg}}\leq0.675.
\]

Previsão formal:

> M20 passará como candidato de refinamento, mas exigirá confirmação independente antes de substituir 14σ.

## 10. Vitória operacional

M20 satisfaz o contrato numérico se:

1. pelo menos 8/10 replicações passam;
2. \(R_{\mathrm{agg,lower}}^{95\%}\geq0.60\);
3. robustez de FPR é satisfeita.

Rótulo científico: `PASS_REFINEMENT_CANDIDATE`.

## 11. Falha forte

`STRONG_FAIL` se:

- no máximo 2/10 replicações passam; ou
- \(R_{\mathrm{agg,upper}}^{95\%}\leq0.60\); ou
- alguma família ultrapassa 1,5%.

## 12. Inconclusivo

Qualquer resultado intermediário será `INCONCLUSIVE`.

## 13. Regras contra puxadinho

1. Exatamente dez replicações.
2. Nenhuma replicação, seed ou família será excluída.
3. Nenhum limiar será compartilhado.
4. Nenhuma alteração após iniciar a primeira replicação.
5. Código, seeds e dependências congelados por hash.
6. Um eventual PASS não será confirmação final sem M21 independente.
