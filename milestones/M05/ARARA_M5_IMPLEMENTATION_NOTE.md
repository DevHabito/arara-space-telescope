# ARARA-M5 — Nota de implementação congelada

**Versão:** 5.0  
**Estado:** congelada antes da geração de dados.

## 1. Operador exato do sinal

O preprocessing SBW é reproduzido localmente para retornar:

- resíduo observado;
- contribuição processada de um sinal fornecido;
- parâmetros de baseline.

Como todo sinal M5 começa após a baseline, mediana, MAD, beta e AR(1) são idênticos com ou sem o sinal.

Se \(s_k\) é o sinal bruto e \(\sigma_0\) a escala robusta inicial do alvo:

\[
s^x_k=s_k/\sigma_0.
\]

A contribuição após o branqueamento final é:

\[
g_0=s^x_0/\sigma_e,
\]

\[
g_k=
\frac{s^x_k-\widehat\phi_e s^x_{k-1}}{\sigma_e},
\quad k\geq1.
\]

## 2. Positivos

Usa-se `target_signal` retornado pelo gerador. O score é calculado somente no segmento inclusivo:

\[
[\tau,t_{25}].
\]

## 3. Negativos

Cada negativo recebe uma hipótese virtual independente:

- forma uniforme entre linear, power-law, exponencial e logística;
- onset uniforme 80–110;
- duração uniforme 24–60;
- parâmetros sorteados pelas distribuições do gerador;
- amplitude bruta unitária.

A amplitude é irrelevante para correlação, mas o sinal virtual é processado pelo operador específico daquela curva.

A hipótese virtual não é adicionada aos dados.

## 4. Estatística

A regressão possui intercepto. Segmentos com menos de três pontos, template degenerado ou observação de variância zero recebem score zero.

Para correlação positiva:

\[
T=c\sqrt{\frac{L-2}{1-c^2}}.
\]

Para correlação não positiva, score zero.

## 5. Limiar

Para 2.000 negativos e alvo 0,5%, são permitidos no máximo 10 scores acima do limiar em cada família.

O limiar usa o próximo número representável acima do 11º maior score, no dtype do próprio array.

## 6. Intervalos

- FPR: Clopper–Pearson superior unilateral 95%;
- recall por estrato: Clopper–Pearson inferior unilateral 95%;
- recall global: bootstrap estratificado, 10.000 réplicas, percentis 5% e 95%.

## 7. Holdout

A abertura será marcada antes da geração. Segunda execução será recusada.
