# ARARA From Zero — Pré-registro M7 Oracle at t75

**Versão:** M7.0  
**Estado:** congelado antes da implementação e dos dados  
**Mudança em relação ao M6:** somente a janela final, de \(t_{50}\) para \(t_{75}\).

---

## 1. Pergunta pequena

Se onset e template processado exato forem conhecidos, permitir observação até 75% da amplitude final torna o evento detectável sob o mesmo controle de falso alerta?

---

## 2. Elementos mantidos

Permanecem idênticos ao M6:

- gerador sintético;
- amplitudes finais de 3–7 desvios-padrão;
- ruído AR(1), normal ou Student-t;
- common-mode;
- oito referências;
- preprocessing SBW;
- uma hipótese por curva;
- estatística de regressão alinhada;
- controle de FPR por família;
- desenvolvimento e holdout com os mesmos tamanhos.

Seeds novas:

- desenvolvimento: `2026080201`;
- holdout: `2026080202`;
- bootstrap: `2026080203`.

---

## 3. Definição

\[
t_{75}
=
\min\{k:s_{0,k}\geq0.75A\}.
\]

O score positivo usa somente:

\[
[\tau,t_{75}].
\]

Negativos recebem uma hipótese virtual independente e pseudo-\(t_{75}\).

---

## 4. Previsão anterior aos resultados

Com base no aumento observado de \(t_{25}\) para \(t_{50}\), a previsão é:

\[
0.12\leq R_{t75}\leq0.35.
\]

Também se prevê:

1. aumento substancial em relação ao M6;
2. recall maior em power-law e exponencial;
3. recall menor em linear e logística;
4. `shared_bump` ou `shared_oscillation` determinará o limiar;
5. o contexto concurrent poderá continuar artificialmente acima do clean e não será interpretado como benefício astrofísico.

---

## 5. Vitória

M7 passa somente se todos ocorrerem:

1. Em cada família negativa:
\[
FPR_{\mathrm{upper}}^{95\%}\leq0.01.
\]

2. Recall global:
\[
R_{t75,\mathrm{lower}}^{95\%}\geq0.30.
\]

3. Pelo menos seis dos oito estratos:
\[
R_{h,\mathrm{lower}}^{95\%}\geq0.20.
\]

4. Pelo menos 15 dos 20 lotes:
\[
R_{\mathrm{batch}}\geq0.25.
\]

---

## 6. Falha forte

M7 falha fortemente se:

- qualquer família negativa viola o FPR; ou
- o limite superior global é:
\[
R_{t75,\mathrm{upper}}^{95\%}\leq0.10.
\]

---

## 7. Inconclusivo

Resultados intermediários não promovem o contrato, mas justificam testar a amplitude completa \(t_{100}\) em novo pré-registro.

---

## 8. Interpretação

- **PASS:** 75% da amplitude contém informação operacional suficiente sob o modelo.
- **STRONG_FAIL:** mesmo 75% permanece insuficiente.
- **INCONCLUSIVE:** testar \(t_{100}\) sem alterar retrospectivamente o M7.

---

## 9. Regras contra puxadinho

1. Uma hipótese por curva.
2. Nenhuma busca temporal.
3. Nenhuma alteração após abrir o holdout.
4. Nenhuma exclusão de família, seed ou lote.
5. Código e dependências congelados por hash.
6. Bug pré-holdout será registrado.
7. Bug pós-holdout invalida a execução.
8. Resultado negativo será preservado.
