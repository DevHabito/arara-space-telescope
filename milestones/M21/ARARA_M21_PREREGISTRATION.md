# ARARA From Zero — Pré-registro M21 Independent Confirmation of 13.75σ at t50

**Versão:** M21.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** confirmação independente do candidato selecionado no M20.

## 1. Pergunta

O resultado candidato de \(13.75\sigma\) em \(t_{50}\) se confirma em dez novas replicações completas, sem nova seleção de SNR?

## 2. Condição fixa

\[
A/\sigma_0=13.75,\qquad f=0.50.
\]

O nível foi fixado pelo M20 antes da abertura do M21. Nenhuma nova busca será realizada.

## 3. Independência

Root seeds inéditas:

- replicações: `2026081601`;
- bootstrap agregado: `2026081602`.

Nenhuma seed do M20 será reutilizada.

## 4. Dez replicações

Cada replicação possui:

- calibração própria com 2.000 negativos por família;
- limiar próprio;
- holdout próprio;
- 2.500 positivos por cada um dos oito estratos;
- 5.000 negativos por família;
- 20 lotes;
- bootstrap próprio com 10.000 réplicas.

## 5. Passe por replicação

Uma replicação passa somente se:

1. \(FPR_{\mathrm{upper}}^{95\%}\leq0.01\) em cada família;
2. \(R_{\mathrm{lower}}^{95\%}\geq0.60\);
3. pelo menos 6/8 estratos têm limite inferior \(\geq0.50\);
4. pelo menos 15/20 lotes têm recall \(\geq0.55\).

## 6. Confirmação

M21 confirma 13,75σ somente se:

1. pelo menos 8/10 replicações passam;
2. \(R_{\mathrm{agg,lower}}^{95\%}\geq0.60\);
3. pelo menos 9/10 replicações controlam o FPR;
4. nenhuma família ultrapassa limite superior de 1,5%.

Rótulo: `PASS_CONFIRMATORY`.

## 7. Falha forte

`STRONG_FAIL` se:

- no máximo 2/10 replicações passam; ou
- \(R_{\mathrm{agg,upper}}^{95\%}\leq0.60\); ou
- alguma família ultrapassa 1,5%.

## 8. Inconclusivo

Qualquer resultado intermediário será `INCONCLUSIVE`.

## 9. Previsão anterior aos dados

Com base no candidato M20, prevê-se:

\[
8\leq N_{\mathrm{PASS}}\leq10,
\]

\[
0.635\leq R_{\mathrm{agg}}\leq0.685.
\]

Previsão formal:

> M21 confirmará 13,75σ como requisito robusto provisório em t50.

## 10. Consequência

- **PASS_CONFIRMATORY:** 13,75σ substitui 14σ como menor nível robustamente confirmado entre os níveis testados.
- **INCONCLUSIVE ou STRONG_FAIL:** 14σ permanece requisito confirmado.

## 11. Regras contra puxadinho

1. Exatamente dez replicações.
2. Nenhuma seed, replicação ou família será excluída.
3. Nenhum limiar será compartilhado.
4. Nenhuma alteração após iniciar a primeira replicação.
5. Código, seeds e dependências congelados por hash.
6. Nenhum novo nível será testado dentro do M21.
