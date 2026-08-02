# ARARA From Zero — Pré-registro M24 Causal Hinge Onset Estimator

**Versão:** M24.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** primeira estimativa causal do onset sem fornecer \(\tau\) verdadeiro ao score.

## 1. Pergunta pequena

Em \(13.75\sigma\) e com endpoint verdadeiro \(t_{50}\), um estimador causal retrospectivo de onset baseado em mudança para subida consegue:

1. manter o contrato de detecção;
2. controlar falsos alertas;
3. colocar pelo menos 90% dos onsets detectados no envelope certificado:
\[
-2\leq\widehat\tau-\tau\leq+1?
\]

## 2. Informações ainda fornecidas

Continuam sendo oráculos:

- endpoint verdadeiro \(t_{50}\);
- forma exata;
- duração e parâmetros exatos da forma;
- intervalo gerador conhecido para o onset, ampliado por margem:
\[
70\leq\tau_{\rm candidato}\leq120.
\]

O onset absoluto verdadeiro não participa da escolha.

## 3. Estimador congelado

O residual SBW é calculado sem usar o sinal.

Para cada candidato inteiro:

\[
\tau_c\in\{70,71,\ldots,120\},
\]

é construído, no intervalo fixo \([50,t_{50}]\), o regressor causal de dobradiça:

\[
h_{\tau_c}(k)=\max(0,k-\tau_c).
\]

Calcula-se o t-score unilateral da correlação entre o residual e o regressor. Candidatos com menos de três pontos após o onset são inválidos.

A estimativa é:

\[
\widehat\tau
=
\arg\max_{\tau_c}T_{\rm hinge}(\tau_c).
\]

Empates são resolvidos pelo menor candidato, pois `numpy.argmax` retorna a primeira ocorrência.

## 4. Score final

Depois de congelar \(\widehat\tau\):

1. o template relativo exato é deslocado para \(\widehat\tau\);
2. o mesmo operador linear SBW da curva é aplicado;
3. o score correlacional final usa:
\[
[\widehat\tau,t_{50}].
\]

O mesmo conjunto de dados é usado para estimar onset e calcular o score. O look-elsewhere e essa reutilização são incorporados à calibração negativa do pipeline inteiro.

## 5. Calibração

Antes de abrir os holdouts serão gerados:

\[
50\,000
\]

negativos por cada uma das cinco famílias.

Cada negativo recebe:

- uma hipótese virtual de forma e duração;
- endpoint virtual \(t_{50}\);
- estimativa de onset pelo hinge scan;
- score final.

O limiar global é calibrado para FPR empírico máximo de 0,5% por família e congelado.

Root seed:

`2026081901`.

## 6. Dez holdouts independentes

Cada holdout terá:

- 2.500 positivos por cada um dos oito estratos;
- 5.000 negativos por família;
- 20 lotes;
- bootstrap com 10.000 réplicas.

Root seeds:

- holdouts: `2026081902`;
- bootstrap agregado: `2026081903`.

## 7. Passe de detecção por holdout

Um holdout passa a parte de detecção somente se:

1. cada família negativa:
\[
FPR_{\mathrm{upper}}^{95\%}\leq0.01;
\]

2. recall global:
\[
R_{\mathrm{lower}}^{95\%}\geq0.60;
\]

3. pelo menos 6/8 estratos têm limite inferior \(\geq0.50\);

4. pelo menos 15/20 lotes têm recall \(\geq0.55\).

## 8. Gate de onset por holdout

Entre os positivos detectados:

\[
A=
P(-2\leq\widehat\tau-\tau\leq+1
\mid \text{detectado}).
\]

O holdout passa o gate de onset se:

\[
A_{\mathrm{lower}}^{95\%}\geq0.90.
\]

Também será reportado:

- atraso \(>+1\);
- antecedência \(<-2\);
- erro mediano;
- erro absoluto mediano;
- distribuição por estrato.

## 9. Passe completo por holdout

Um holdout passa somente se:

- passa todos os gates de detecção;
- passa o gate de onset.

## 10. Passe agregado

M24 passa somente se:

1. pelo menos 8/10 holdouts completos passam;
2. recall agregado possui limite inferior \(\geq0.60\);
3. acurácia de onset agrupada entre detectados possui limite inferior Clopper–Pearson \(\geq0.90\);
4. pelo menos 9/10 holdouts controlam FPR;
5. nenhuma família ultrapassa limite superior de FPR de 1,5%.

Rótulo:

`PASS_CAUSAL_ONSET_ESTIMATOR`.

## 11. Falha forte

`STRONG_FAIL_CAUSAL_ONSET_ESTIMATOR` se qualquer ocorrer:

- no máximo 2/10 holdouts completos passam;
- limite superior agregado do recall \(\leq0.60\);
- limite superior de 95% da acurácia no envelope \([-2,+1]\) é menor que 0,75;
- alguma família ultrapassa limite superior de FPR de 1,5%.

Qualquer caso intermediário será `INCONCLUSIVE`.

## 12. Previsão anterior aos dados

A previsão é pessimista.

O hinge scan deverá identificar razoavelmente as formas lineares, mas estimar tarde o onset de power-law, exponencial e logística.

Prevê-se:

\[
R_{\rm agregado}\in[0.48,0.60],
\]

\[
A_{\rm envelope}\in[0.25,0.60],
\]

\[
N_{\rm PASS}\leq2.
\]

Veredito previsto:

`STRONG_FAIL_CAUSAL_ONSET_ESTIMATOR`.

## 13. Interpretação

Uma falha não prova impossibilidade fundamental. Ela rejeita este estimador genérico de dobradiça.

Um passe demonstrará que o onset absoluto pode ser removido mantendo ainda endpoint, forma e duração como oráculos.

## 14. Regras contra puxadinho

1. Exatamente um estimador.
2. Exatamente 51 candidatos inteiros, 70–120.
3. Exatamente 50.000 negativos por família.
4. Exatamente dez holdouts.
5. Nenhum parâmetro será ajustado após abrir a calibração.
6. Nenhum holdout será aberto antes de congelar o limiar.
7. Nenhuma seed, família, estrato ou lote será excluído.
8. O onset verdadeiro será usado apenas para medir erro nos positivos, nunca para escolher \(\widehat\tau\).
9. Código, seeds, limiar e dependências serão congelados por hash.
