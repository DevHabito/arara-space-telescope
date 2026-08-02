# ARARA From Zero — Pré-registro M27 Exact-Onset 16-Cadence Confirmation

**Versão:** M27.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** extensão controlada da janela confirmatória do M26.

## 1. Pergunta pequena

Em \(13.75\sigma\) e com onset, forma, duração e endpoint \(t_{50}\) exatos, ampliar a confirmação de oito para dezesseis cadências recupera o contrato?

## 2. Alteração única

O M27 mantém o protocolo do M26 e altera somente:

\[
L_{\rm confirm}:8\rightarrow16\text{ cadências}.
\]

Todo o restante permanece congelado:

- onset exato;
- endpoint exato \(t_{50}\);
- forma e duração exatas;
- operador SBW;
- uma cadência de guarda;
- matched filter normalizado;
- calibração com 50.000 negativos por família;
- dez holdouts e os mesmos gates.

## 3. Geometria temporal

Para endpoint \(e=t_{50}\):

- região anterior:
\[
[50,e-17];
\]

- guarda:
\[
e-16;
\]

- confirmação:
\[
[e-15,e],
\]

com exatamente 16 cadências.

A região anterior não participa do score.

## 4. Score

\[
Z_{16}
=
\frac{\sum_{k=e-15}^{e}r_k h_k}
{\sqrt{\sum_{k=e-15}^{e}h_k^2}}.
\]

Não há busca, maximização, ajuste de onset ou seleção dentro da confirmação.

## 5. Calibração

Antes dos holdouts serão gerados 50.000 negativos por cada uma das cinco famílias. Cada negativo recebe hipótese virtual exata de forma, duração, onset e endpoint.

O limiar global é calibrado para FPR empírico máximo de 0,5% por família e congelado antes dos holdouts.

Root seed:

`2026082201`.

## 6. Dez holdouts independentes

Cada holdout terá:

- 2.500 positivos por cada um dos oito estratos;
- 5.000 negativos por família;
- 20 lotes;
- bootstrap estratificado com 10.000 réplicas.

Root seeds:

- holdouts: `2026082202`;
- bootstrap agregado: `2026082203`.

## 7. Passe por holdout

Um holdout passa somente se:

1. em cada família:
\[
FPR_{\rm upper}^{95\%}\leq0.01;
\]

2. recall global:
\[
R_{\rm lower}^{95\%}\geq0.60;
\]

3. pelo menos 6/8 estratos têm limite inferior \(\geq0.50\);

4. pelo menos 15/20 lotes têm recall \(\geq0.55\).

## 8. Passe agregado

M27 passa se:

1. pelo menos 8/10 holdouts passam;
2. limite inferior agregado do recall \(\geq0.60\);
3. pelo menos 9/10 holdouts controlam FPR;
4. nenhuma família ultrapassa limite superior de FPR de 1,5%.

Rótulo:

`PASS_EXACT_ONSET_16_CONFIRMATION`.

## 9. Falha forte

`STRONG_FAIL_EXACT_ONSET_16_CONFIRMATION` se:

- no máximo 2/10 holdouts passam; ou
- limite superior agregado do recall \(\leq0.60\); ou
- alguma família ultrapassa limite superior de FPR de 1,5%.

Qualquer resultado intermediário será `INCONCLUSIVE`.

## 10. Previsão anterior aos dados

A duplicação da janela deve recuperar informação, mas `shared_step` continuará elevando a cauda nula.

Prevê-se:

\[
\theta_{16}\in[20,26],
\]

\[
R_{\rm agregado}\in[0.45,0.62],
\]

\[
2\leq N_{\rm PASS}\leq6,
\]

com veredito `INCONCLUSIVE`.

## 11. Interpretação

- **PASS:** 16 cadências são suficientes sob oráculo; o próximo teste poderá devolver o onset estimado usando esse downstream.
- **STRONG_FAIL:** 16 cadências ainda são insuficientes; deve-se testar 24 cadências ou abandonar esta estatística curta.
- **INCONCLUSIVE:** existe recuperação parcial, mas não robustez operacional.

## 12. Regras contra puxadinho

1. Alteração única: 8 → 16 cadências.
2. Exatamente uma guarda.
3. Exatamente 50.000 negativos por família.
4. Exatamente dez holdouts.
5. Nenhum parâmetro será ajustado após abrir a calibração.
6. Nenhum holdout será aberto antes do congelamento do limiar.
7. Nenhuma seed, família, estrato ou lote será excluído.
8. Nenhuma busca de onset será executada.
9. Código, seeds, limiar e dependências serão congelados por hash.
