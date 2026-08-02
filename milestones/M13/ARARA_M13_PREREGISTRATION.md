# ARARA From Zero — Pré-registro M13 SNR Threshold at t50

**Versão:** M13.0  
**Estado:** congelado antes da implementação e dos dados

---

## 1. Pergunta pequena

Com janela fixada em \(t_{50}\), qual é o menor SNR final entre 10σ e 18σ que satisfaz o contrato?

---

## 2. Grade congelada

\[
A/\sigma_0 \in \{10,12,14,16,18\}.
\]

Apenas a amplitude final muda. Os campos são emparelhados entre níveis.

---

## 3. Elementos mantidos

- janela \(t_{50}\);
- gerador, ruído e artefatos anteriores;
- preprocessing SBW;
- onset e template exatos;
- uma hipótese por curva;
- FPR por família;
- oito estratos positivos;
- cinco famílias negativas.

Seeds:

- desenvolvimento: `2026080801`;
- holdout: `2026080802`;
- bootstrap: `2026080803`.

---

## 4. Previsão anterior aos resultados

\[
R(10)\in[0.20,0.35],
\]

\[
R(12)\in[0.38,0.55],
\]

\[
R(14)\in[0.58,0.72],
\]

\[
R(16)\in[0.72,0.84],
\]

\[
R(18)\in[0.82,0.92].
\]

Previsão principal:

> O primeiro nível aprovado será \(14\sigma\).

Também se prevê:

1. recall global não decrescente;
2. logística e power-law terão maior recall;
3. linear e exponencial terão menor recall;
4. ramp ou bump determinará o limiar;
5. diferenças clean–concurrent diminuirão em SNR alto.

---

## 5. Desenvolvimento

- 1.000 campos-base por forma/contexto;
- cinco SNRs por campo;
- 2.000 negativos por família;
- limiar calculado apenas nos negativos;
- máximo empírico de 0,5% por família.

---

## 6. Holdout

- 2.500 campos por forma/contexto/SNR;
- 5.000 negativos por família;
- 20 lotes;
- 125 positivos por estrato em cada lote;
- 250 negativos por família em cada lote.

---

## 7. Vitória de um nível

Um nível passa se:

1. Em cada família negativa:
\[
FPR_{\mathrm{upper}}^{95\%}\leq0.01.
\]

2. Recall global:
\[
R_{\mathrm{lower}}^{95\%}\geq0.60.
\]

3. Pelo menos seis dos oito estratos:
\[
R_{h,\mathrm{lower}}^{95\%}\geq0.50.
\]

4. Pelo menos 15 dos 20 lotes:
\[
R_{\mathrm{batch}}\geq0.55.
\]

---

## 8. Vitória do M13

M13 passa se:

- pelo menos um nível passa;
- a curva pontual não cai mais de 0,02 entre níveis adjacentes.

O menor nível aprovado será o requisito provisório em \(t_{50}\).

---

## 9. Falha forte

M13 falha fortemente se nenhum nível passa e o limite superior em 18σ é menor ou igual a 0,50.

---

## 10. Inconclusivo

Se nenhum nível passar, mas 18σ tiver limite superior acima de 0,50, o resultado será inconclusivo.

---

## 11. Regras contra puxadinho

1. Nenhum nível será adicionado.
2. Nenhum nível será removido.
3. Nenhuma alteração após abrir o holdout.
4. Nenhuma exclusão de forma, contexto, seed ou lote.
5. O limiar será calibrado apenas nos negativos.
6. Código e dependências serão congelados por hash.
7. Bug pós-holdout invalida a execução.
8. Resultado negativo será preservado.
