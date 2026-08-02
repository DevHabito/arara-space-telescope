# ARARA From Zero — Pré-registro M18 Multi-Seed Replication of 13σ at t50

**Versão:** M18.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** replicação prospectiva completa para refinar o intervalo robusto em \(t_{50}\).

---

## 1. Pergunta pequena

O nível \(13\sigma\) em \(t_{50}\) satisfaz o contrato de maneira robusta quando calibração, limiar e holdout são repetidos integralmente em dez realizações independentes?

---

## 2. Condição fixa

\[
A/\sigma_0=13,
\qquad
f=0.50.
\]

Não haverá grade de SNR nem busca de fração.

---

## 3. Motivação anterior aos dados

Resultados já congelados:

\[
R_{\mathrm{agg}}(12\sigma)=0.51471
\]

no M15, com 1/10 replicações aprovadas, e

\[
R_{\mathrm{agg}}(14\sigma)=0.66393
\]

no M17, com 10/10 replicações aprovadas.

A interpolação linear simples no ponto médio fornece:

\[
\widehat R_{\mathrm{agg}}(13\sigma)
=
\frac{0.51471+0.66393}{2}
=
0.58932.
\]

Essa interpolação é somente uma previsão anterior aos dados, não um modelo físico nem um ajuste do critério.

---

## 4. Dez replicações completas

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

- replicações: `2026081301`;
- bootstrap agregado: `2026081302`.

---

## 5. Passe por replicação

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

## 6. Métrica agregada

\[
R_{\mathrm{agg}}
=
\frac{1}{10}
\sum_{r=1}^{10}
\frac{1}{8}
\sum_{h=1}^{8}R_{r,h}.
\]

O intervalo agregado será obtido pelo bootstrap hierárquico já congelado:

1. reamostrar replicações com reposição;
2. reamostrar cada estrato pela distribuição binomial observada;
3. 10.000 réplicas.

---

## 7. Robustez de falso alerta

A robustez exige:

- pelo menos 9/10 replicações com FPR aprovado em todas as famílias;
- nenhuma família em nenhuma replicação com limite superior acima de 1,5%.

---

## 8. Previsão anterior aos resultados

Prevê-se:

\[
3\leq N_{\mathrm{PASS}}\leq7,
\]

\[
0.56\leq R_{\mathrm{agg}}\leq0.62.
\]

Previsão formal:

> M18 será inconclusivo; 13σ ficará na região de transição entre a rejeição robusta de 12σ e a confirmação robusta de 14σ.

---

## 9. Vitória

M18 passa somente se:

1. pelo menos 8/10 replicações passam;
2. limite inferior agregado:
\[
R_{\mathrm{agg,lower}}^{95\%}\geq0.60;
\]
3. robustez de FPR é satisfeita.

---

## 10. Falha forte

M18 falha fortemente se:

- no máximo 2/10 replicações passam; ou
- limite superior agregado:
\[
R_{\mathrm{agg,upper}}^{95\%}\leq0.60;
\]
ou
- alguma família possui limite superior de FPR acima de 1,5%.

---

## 11. Inconclusivo

Qualquer resultado entre vitória e falha forte será:

`INCONCLUSIVE`.

---

## 12. Interpretação

- **PASS:** 13σ substitui 14σ como requisito robusto provisório em \(t_{50}\).
- **STRONG_FAIL:** 13σ é insuficiente; o intervalo robusto permanece \((13\sigma,14\sigma]\).
- **INCONCLUSIVE:** 13σ é limítrofe e não deve ser promovido; 14σ permanece o requisito confirmado.

---

## 13. Regras contra puxadinho

1. Exatamente dez replicações.
2. Nenhuma replicação será excluída.
3. Nenhuma seed será substituída.
4. Nenhum limiar será compartilhado.
5. Nenhuma alteração após iniciar a primeira replicação.
6. Resultados individuais serão preservados.
7. Falhas técnicas serão registradas.
8. Código, seeds e dependências serão congelados por hash.
