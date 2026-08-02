# ARARA From Zero — Pré-registro M6 Oracle at t50

**Versão:** M6.0  
**Estado:** congelado antes da implementação e dos dados  
**Mudança em relação ao M5:** somente a janela final, de \(t_{25}\) para \(t_{50}\).

## 1. Pergunta pequena

Se onset e template processado exato forem conhecidos, permitir observação até 50% da amplitude final torna o evento detectável sob o mesmo controle de falso alerta?

## 2. Elementos mantidos

Permanecem idênticos ao M5:

- gerador;
- amplitudes finais 3–7 desvios-padrão;
- ruído;
- common-mode;
- oito referências;
- SBW;
- uma hipótese por curva;
- FPR por família;
- estatística de regressão;
- tamanhos de desenvolvimento e holdout.

Seeds novas:

- desenvolvimento: `2026080101`;
- holdout: `2026080102`;
- bootstrap: `2026080103`.

## 3. Definição

\[
t_{50}
=
\min\{k:s_{0,k}\geq0.50A\}.
\]

O score positivo usa somente:

\[
[\tau,t_{50}].
\]

Negativos recebem hipótese virtual independente e pseudo-\(t_{50}\).

## 4. Previsão

\[
0.25\leq R_{t50}\leq0.60.
\]

Prevê-se:

1. aumento grande em relação ao M5;
2. maior recall em linear e logística;
3. menor recall em power-law e exponencial;
4. shared_oscillation ainda determinará o limiar;
5. concurrent não será interpretado como evidência caso supere clean por contaminação estrutural.

## 5. Vitória

M6 passa se todos ocorrerem:

1. por família negativa:
\[
FPR_{\mathrm{upper}}^{95\%}\leq0.01;
\]

2. recall global:
\[
R_{t50,\mathrm{lower}}^{95\%}\geq0.50;
\]

3. pelo menos seis dos oito estratos:
\[
R_{h,\mathrm{lower}}^{95\%}\geq0.40;
\]

4. pelo menos 15 dos 20 lotes:
\[
R_{\mathrm{batch}}\geq0.45.
\]

## 6. Falha forte

M6 falha fortemente se:

- qualquer família viola FPR; ou
- o limite superior global é:
\[
R_{t50,\mathrm{upper}}^{95\%}\leq0.20.
\]

## 7. Inconclusivo

Resultados intermediários não promovem o contrato, mas justificam testar \(t_{75}\) com novo pré-registro.

## 8. Interpretação

- PASS: \(t_{25}\) era severo demais e \(t_{50}\) contém informação suficiente.
- STRONG_FAIL: metade da amplitude ainda é insuficiente sob o contrato.
- INCONCLUSIVE: testar \(t_{75}\), sem ajustar retroativamente M6.

## 9. Regras

1. Uma hipótese por curva.
2. Nenhuma busca temporal.
3. Nenhuma alteração após holdout.
4. Nenhuma exclusão de família, seed ou lote.
5. Código e dependências congelados por hash.
6. Resultado negativo preservado.
