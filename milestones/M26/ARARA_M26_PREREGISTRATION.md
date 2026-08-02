# ARARA From Zero — Pré-registro M26 Exact-Onset Control for Split Confirmation

**Versão:** M26.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** controle causal do M25, devolvendo apenas o onset exato.

## 1. Pergunta pequena

Em \(13.75\sigma\) e com endpoint verdadeiro \(t_{50}\), o matched filter de oito cadências usado no M25 satisfaz o contrato quando recebe o onset exato?

## 2. Objetivo causal

O M25 alterou simultaneamente:

1. onset exato → onset estimado por dobradiça;
2. score completo → confirmação em oito cadências.

O M26 mantém exatamente a confirmação do M25 e remove somente o erro de onset.

- **PASS:** o estimador de onset foi o principal gargalo do M25;
- **STRONG_FAIL:** a janela/estatística de confirmação é insuficiente mesmo com onset exato;
- **INCONCLUSIVE:** ambos contribuíram e nenhum gargalo domina sozinho.

## 3. Condição fixa

\[
A/\sigma_0=13.75,\qquad f=0.50.
\]

Continuam como oráculos:

- onset verdadeiro;
- endpoint verdadeiro \(t_{50}\);
- forma e duração exatas.

## 4. Partição idêntica ao M25

Para cada endpoint \(e=t_{50}\):

- região anterior: \([50,e-9]\);
- guarda: \(e-8\);
- confirmação: \([e-7,e]\).

A região anterior não participa do score do M26. Ela é mantida apenas para preservar a mesma geometria temporal do controle.

## 5. Score idêntico ao M25

O template exato é processado pelo operador SBW da curva.

\[
Z_{\rm confirm}
=
\frac{\sum_{k=e-7}^{e}r_kh_k}
{\sqrt{\sum_{k=e-7}^{e}h_k^2}}.
\]

Não há busca, maximização ou ajuste de onset.

## 6. Calibração

Antes dos holdouts serão gerados 50.000 negativos por cada uma das cinco famílias.

Cada negativo recebe hipótese virtual exata de forma, duração, onset e endpoint \(t_{50}\).

O limiar global será calibrado para FPR empírico máximo de 0,5% por família e congelado.

Root seed: `2026082101`.

## 7. Dez holdouts independentes

Cada holdout terá:

- 2.500 positivos por cada um dos oito estratos;
- 5.000 negativos por família;
- 20 lotes;
- bootstrap com 10.000 réplicas.

Root seeds:

- holdouts: `2026082102`;
- bootstrap agregado: `2026082103`.

## 8. Passe por holdout

Um holdout passa somente se:

1. cada família negativa possui \(FPR_{upper}^{95\%}\leq0.01\);
2. recall global possui limite inferior \(\geq0.60\);
3. pelo menos 6/8 estratos possuem limite inferior \(\geq0.50\);
4. pelo menos 15/20 lotes possuem recall \(\geq0.55\).

## 9. Passe agregado

M26 passa se:

1. pelo menos 8/10 holdouts passam;
2. limite inferior agregado do recall \(\geq0.60\);
3. pelo menos 9/10 holdouts controlam FPR;
4. nenhuma família ultrapassa limite superior de 1,5%.

Rótulo: `PASS_EXACT_ONSET_SPLIT_CONFIRMATION`.

## 10. Falha forte

`STRONG_FAIL_EXACT_ONSET_SPLIT_CONFIRMATION` se:

- no máximo 2/10 holdouts passam; ou
- limite superior agregado do recall \(\leq0.60\); ou
- alguma família ultrapassa limite superior de FPR de 1,5%.

Qualquer resultado intermediário será `INCONCLUSIVE`.

## 11. Previsão anterior aos dados

O onset exato deverá recuperar substancialmente o desempenho do M25, mas o matched filter curto continuará exposto à cauda de `shared_step`.

Prevê-se:

\[
R_{agregado}\in[0.55,0.68],
\]

\[
3\leq N_{PASS}\leq7,
\]

com veredito `INCONCLUSIVE`.

Também se prevê:

\[
\theta_{M26}\in[14,18].
\]

## 12. Regras contra puxadinho

1. Mesma guarda e mesmas oito cadências do M25.
2. Mesmo matched filter do M25.
3. Exatamente 50.000 negativos por família.
4. Exatamente dez holdouts.
5. Nenhum parâmetro será ajustado após abrir a calibração.
6. Nenhum holdout será aberto antes de congelar o limiar.
7. Nenhuma seed, família, estrato ou lote será excluído.
8. Nenhuma busca de onset será executada.
9. Código, seeds, limiar e dependências serão congelados por hash.
