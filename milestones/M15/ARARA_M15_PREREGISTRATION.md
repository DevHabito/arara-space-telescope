# ARARA From Zero — Pré-registro M15 Multi-Seed Replication of 12σ at t50

**Versão:** M15.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** replicação prospectiva do procedimento completo.

---

## 1. Pergunta pequena

O resultado de \(12\sigma\) em \(t_{50}\) é robusto quando calibração, limiar e holdout são repetidos integralmente em dez realizações independentes?

---

## 2. Condição fixa

\[
A/\sigma_0=12,
\qquad
f=0.50.
\]

Não haverá grade de SNR nem busca de fração.

---

## 3. Dez replicações completas

Cada replicação \(r=1,\ldots,10\) possui:

- seed de desenvolvimento própria;
- 2.000 negativos por família para calibração;
- limiar próprio;
- holdout próprio;
- 2.500 positivos por cada um dos oito estratos;
- 5.000 negativos por família;
- 20 lotes de holdout;
- bootstrap estratificado próprio com 10.000 réplicas.

Root seeds:

- replicações: `2026081001`;
- bootstrap agregado: `2026081002`.

As seeds filhas serão registradas antes da execução.

---

## 4. Critério de passe por replicação

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

O recall agregado atribui peso igual às dez replicações e aos oito estratos:

\[
R_{\mathrm{agg}}
=
\frac{1}{10}
\sum_{r=1}^{10}
\frac{1}{8}
\sum_{h=1}^{8}R_{r,h}.
\]

O intervalo agregado será obtido por bootstrap hierárquico:

1. amostrar dez replicações com reposição;
2. dentro de cada replicação amostrada, reamostrar cada estrato pela distribuição binomial observada;
3. 10.000 réplicas.

---

## 6. Robustez de falso alerta

Defina uma replicação como `FPR_PASS` quando todas as cinco famílias respeitam 1%.

A robustez de FPR exige:

- pelo menos 9/10 replicações `FPR_PASS`;
- nenhuma família em nenhuma replicação com limite superior acima de 1,5%.

---

## 7. Previsão anterior aos resultados

Previsão principal:

\[
5\leq N_{\mathrm{PASS}}\leq7.
\]

Também se prevê:

\[
0.59\leq R_{\mathrm{agg}}\leq0.63.
\]

Portanto, a previsão formal é:

> M15 será inconclusivo; 12σ será limítrofe, mas não robustamente promovido.

---

## 8. Vitória

M15 passa somente se:

1. pelo menos 8/10 replicações passam;
2. limite inferior agregado:
\[
R_{\mathrm{agg,lower}}^{95\%}\geq0.60;
\]
3. robustez de FPR é satisfeita.

---

## 9. Falha forte

M15 falha fortemente se:

- no máximo 2/10 replicações passam; ou
- limite superior agregado:
\[
R_{\mathrm{agg,upper}}^{95\%}\leq0.60;
\]
ou
- alguma família possui limite superior de FPR acima de 1,5%.

---

## 10. Inconclusivo

Qualquer resultado entre vitória e falha forte é inconclusivo.

---

## 11. Interpretação

- **PASS:** 12σ pode ser tratado como requisito robusto provisório em \(t_{50}\).
- **STRONG_FAIL:** 12σ é insuficiente.
- **INCONCLUSIVE:** 12σ é limítrofe; requisito deve ser elevado ou reformulado.

---

## 12. Regras contra puxadinho

1. Exatamente dez replicações.
2. Nenhuma replicação será excluída.
3. Nenhuma seed será substituída.
4. Nenhum limiar será compartilhado entre replicações.
5. Nenhuma alteração após iniciar a primeira replicação.
6. Resultados individuais serão preservados.
7. Falhas técnicas serão registradas, não apagadas.
8. Código e dependências serão congelados por hash.
