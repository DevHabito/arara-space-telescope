# ARARA From Zero — Pré-registro M8 Oracle at t100

**Versão:** M8.0  
**Estado:** congelado antes da implementação e dos dados  
**Mudança em relação ao M7:** somente a janela final, de \(t_{75}\) para a primeira chegada à amplitude completa.

---

## 1. Pergunta pequena

Se onset e template processado exato forem conhecidos, a observação até a primeira chegada à amplitude final torna o evento detectável sob o mesmo controle de falso alerta?

---

## 2. Elementos mantidos

Permanecem idênticos ao M7:

- gerador;
- amplitudes finais de 3–7 desvios-padrão;
- ruído e artefatos;
- common-mode;
- oito referências;
- preprocessing SBW;
- uma hipótese por curva;
- estatística alinhada;
- FPR por família;
- tamanhos dos conjuntos.

Seeds novas:

- desenvolvimento: `2026080301`;
- holdout: `2026080302`;
- bootstrap: `2026080303`.

---

## 3. Definição

\[
t_{100}
=
\min\{k:s_{0,k}=A\},
\qquad
A=\max_k s_{0,k}.
\]

Por tolerância numérica, a implementação usa:

\[
s_{0,k}\geq1.0A.
\]

O score positivo usa somente:

\[
[\tau,t_{100}].
\]

Negativos recebem uma hipótese virtual independente e pseudo-\(t_{100}\).

---

## 4. Previsão anterior aos resultados

Com base na progressão M5–M7:

\[
0.25\leq R_{t100}\leq0.55.
\]

Também se prevê:

1. aumento substancial em relação ao M7;
2. maior recall em power-law e exponencial;
3. menor recall em linear e logística;
4. FPR continuará controlado;
5. `shared_ramp` ou `shared_bump` determinará o limiar.

---

## 5. Vitória

M8 passa somente se todos ocorrerem:

1. Em cada família negativa:
\[
FPR_{\mathrm{upper}}^{95\%}\leq0.01.
\]

2. Recall global:
\[
R_{t100,\mathrm{lower}}^{95\%}\geq0.40.
\]

3. Pelo menos seis dos oito estratos:
\[
R_{h,\mathrm{lower}}^{95\%}\geq0.30.
\]

4. Pelo menos 15 dos 20 lotes:
\[
R_{\mathrm{batch}}\geq0.35.
\]

---

## 6. Falha forte

M8 falha fortemente se:

- qualquer família negativa viola o FPR; ou
- o limite superior global é:
\[
R_{t100,\mathrm{upper}}^{95\%}\leq0.20.
\]

---

## 7. Inconclusivo

Resultados intermediários não promovem o contrato e encerram esta sequência de frações. A revisão seguinte deverá alterar amplitude, ruído, cadência ou fonte adicional de informação — não apenas ampliar novamente a janela.

---

## 8. Interpretação

- **PASS:** a amplitude completa contém informação suficiente, mas o alerta realmente precoce anterior não.
- **STRONG_FAIL:** nem a primeira chegada à amplitude final fecha o contrato atual.
- **INCONCLUSIVE:** há informação parcial, porém insuficiente para promoção.

---

## 9. Regras contra puxadinho

1. Uma hipótese por curva.
2. Nenhuma busca temporal.
3. Nenhuma alteração após abrir o holdout.
4. Nenhuma exclusão de família, seed ou lote.
5. Dependências congeladas por hash.
6. Bug pré-holdout será registrado.
7. Bug pós-holdout invalida a execução.
8. Resultado negativo será preservado.
