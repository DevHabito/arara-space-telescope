# ARARA From Zero — Pré-registro M17 Multi-Seed Replication of 14σ at t50

**Versão:** M17.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** replicação prospectiva completa do requisito candidato de 14σ.

---

## 1. Pergunta pequena

O nível \(14\sigma\) em \(t_{50}\) satisfaz o contrato de maneira robusta quando calibração, limiar e holdout são repetidos integralmente em dez realizações independentes?

---

## 2. Condição fixa

\[
A/\sigma_0=14,
\qquad
f=0.50.
\]

Não haverá grade de SNR nem busca de fração.

---

## 3. Dez replicações completas

Cada replicação possui:

- seed de desenvolvimento própria;
- 2.000 negativos por família para calibração;
- limiar próprio;
- holdout positivo próprio;
- holdout negativo próprio;
- 2.500 positivos por cada um dos oito estratos;
- 5.000 negativos por família;
- 20 lotes;
- bootstrap estratificado próprio com 10.000 réplicas.

Root seeds:

- replicações: `2026081201`;
- bootstrap agregado: `2026081202`.

---

## 4. Passe por replicação

Uma replicação passa somente se:

1. em cada família negativa:
\[
FPR_{\mathrm{upper}}^{95\%}\leq0.01;
\]

2. recall global:
\[
R_{\mathrm{lower}}^{95\%}\geq0.60;
\]

3. pelo menos seis dos oito estratos:
\[
R_{h,\mathrm{lower}}^{95\%}\geq0.50;
\]

4. pelo menos 15 dos 20 lotes:
\[
R_{\mathrm{batch}}\geq0.55.
\]

---

## 5. Métrica agregada

\[
R_{\mathrm{agg}}
=
\frac{1}{10}
\sum_{r=1}^{10}
\frac{1}{8}
\sum_{h=1}^{8}R_{r,h}.
\]

O intervalo agregado será obtido pelo mesmo bootstrap hierárquico do M15:

1. reamostrar replicações com reposição;
2. reamostrar cada estrato pela distribuição binomial observada;
3. 10.000 réplicas.

---

## 6. Robustez de falso alerta

A robustez exige:

- pelo menos 9/10 replicações com FPR aprovado em todas as famílias;
- nenhuma família em nenhuma replicação com limite superior acima de 1,5%.

---

## 7. Previsão anterior aos resultados

Prevê-se:

\[
8\leq N_{\mathrm{PASS}}\leq10,
\]

\[
0.68\leq R_{\mathrm{agg}}\leq0.78.
\]

Previsão formal:

> M17 passará e 14σ poderá ser tratado como requisito robusto provisório em t50.

---

## 8. Vitória

M17 passa somente se:

1. pelo menos 8/10 replicações passam;
2. limite inferior agregado:
\[
R_{\mathrm{agg,lower}}^{95\%}\geq0.60;
\]
3. robustez de FPR é satisfeita.

---

## 9. Falha forte

M17 falha fortemente se:

- no máximo 2/10 replicações passam; ou
- limite superior agregado:
\[
R_{\mathrm{agg,upper}}^{95\%}\leq0.60;
\]
ou
- alguma família possui limite superior de FPR acima de 1,5%.

---

## 10. Inconclusivo

Qualquer resultado intermediário é inconclusivo.

---

## 11. Interpretação

- **PASS:** 14σ é requisito robusto provisório em t50 sob o procedimento atual.
- **STRONG_FAIL:** 14σ é insuficiente.
- **INCONCLUSIVE:** o requisito robusto está acima de 14σ ou o procedimento precisa ser reformulado.

---

## 12. Regras contra puxadinho

1. Exatamente dez replicações.
2. Nenhuma replicação será excluída.
3. Nenhuma seed será substituída.
4. Nenhum limiar será compartilhado.
5. Nenhuma alteração após iniciar a primeira replicação.
6. Resultados individuais serão preservados.
7. Falhas técnicas serão registradas.
8. Código, seeds e dependências serão congelados por hash.
