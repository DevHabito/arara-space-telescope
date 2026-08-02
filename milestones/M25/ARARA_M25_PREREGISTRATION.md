# ARARA From Zero — Pré-registro M25 Split-Sample Onset Estimation and Confirmation

**Versão:** M25.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** separação temporal entre estimativa do onset e confirmação do evento.

## 1. Pergunta pequena

Em \(13.75\sigma\) e com endpoint verdadeiro \(t_{50}\), separar temporalmente os dados usados para estimar o onset daqueles usados para confirmar o evento resgata a detecção sem fabricar precisão de onset?

## 2. Informações ainda fornecidas

Continuam como oráculos:

- endpoint verdadeiro \(t_{50}\);
- forma exata;
- duração e parâmetros exatos da forma;
- faixa de candidatos:
\[
70\leq\tau_c\leq120.
\]

O onset verdadeiro não participa da escolha.

## 3. Partição temporal congelada

Para cada curva, com endpoint \(e=t_{50}\):

### Seleção

\[
[50,e-9].
\]

O hinge scan escolhe o onset usando apenas esse intervalo.

### Guarda

A cadência:

\[
e-8
\]

não participa de nenhuma das duas etapas.

### Confirmação

\[
[e-7,e],
\]

totalizando exatamente oito cadências.

Nenhuma amostra da confirmação participa da escolha do onset.

## 4. Estimador

Para cada candidato inteiro:

\[
\tau_c\in\{70,\ldots,120\},
\]

é calculado o t-score unilateral da dobradiça:

\[
h_{\tau_c}(k)=\max(0,k-\tau_c)
\]

somente no intervalo de seleção.

Candidatos com menos de três amostras após o onset dentro da seleção são inválidos.

\[
\widehat\tau
=
\arg\max_{\tau_c}T_{\rm hinge}(\tau_c).
\]

Empates usam o menor candidato.

## 5. Score de confirmação

A forma e duração exatas são deslocadas para \(\widehat\tau\) e processadas pelo mesmo operador SBW da curva.

Somente as oito amostras de confirmação são usadas:

\[
Z_{\rm confirm}
=
\frac{\sum_{k=e-7}^{e}r_k h_k}
{\sqrt{\sum_{k=e-7}^{e}h_k^2}}.
\]

Se o denominador for numericamente nulo, o score é zero.

Não há busca nem maximização na confirmação.

## 6. Calibração

O pipeline completo será calibrado antes dos holdouts em:

\[
50\,000
\]

negativos por cada uma das cinco famílias.

Cada negativo recebe hipótese virtual de forma, duração e endpoint \(t_{50}\), mas o onset é escolhido pelo hinge scan dividido.

O limiar global será calibrado para FPR empírico máximo de 0,5% por família e congelado.

Root seed:

`2026082001`.

## 7. Dez holdouts

Cada holdout terá:

- 2.500 positivos por cada um dos oito estratos;
- 5.000 negativos por família;
- 20 lotes;
- bootstrap com 10.000 réplicas.

Root seeds:

- holdouts: `2026082002`;
- bootstrap agregado: `2026082003`.

## 8. Gate de detecção por holdout

Um holdout passa detecção somente se:

1. cada família:
\[
FPR_{\mathrm{upper}}^{95\%}\leq0.01;
\]

2. recall:
\[
R_{\mathrm{lower}}^{95\%}\geq0.60;
\]

3. pelo menos 6/8 estratos têm limite inferior \(\geq0.50\);

4. pelo menos 15/20 lotes têm recall \(\geq0.55\).

## 9. Gate de onset

Entre os positivos detectados:

\[
A=
P(-2\leq\widehat\tau-\tau\leq+1
\mid \text{detectado}).
\]

O gate passa se:

\[
A_{\mathrm{lower}}^{95\%}\geq0.90.
\]

## 10. Passe completo

Um holdout passa somente se detecção e onset passam.

M25 passa se:

1. pelo menos 8/10 holdouts completos passam;
2. limite inferior agregado do recall \(\geq0.60\);
3. limite inferior agrupado da acurácia de onset \(\geq0.90\);
4. pelo menos 9/10 holdouts controlam FPR;
5. nenhuma família ultrapassa limite superior de 1,5%.

Rótulo:

`PASS_SPLIT_SAMPLE_ONSET`.

## 11. Falha forte

`STRONG_FAIL_SPLIT_SAMPLE_ONSET` se:

- no máximo 2/10 holdouts completos passam; ou
- limite superior agregado do recall \(\leq0.60\); ou
- limite superior da acurácia de onset é menor que 0,75; ou
- alguma família ultrapassa limite superior de FPR de 1,5%.

Qualquer resultado intermediário será `INCONCLUSIVE`.

## 12. Previsão anterior aos dados

Prevê-se que a separação remova grande parte do custo de reutilização observado no M24:

\[
\theta_{\rm M25}<\theta_{\rm M24}=14.324525.
\]

Prevê-se:

\[
R_{\rm agregado}\in[0.55,0.80],
\]

\[
A_{\rm envelope}\in[0.20,0.55].
\]

A detecção deverá passar em pelo menos 8/10 holdouts, mas o gate de onset não.

Prevê-se:

\[
N_{\rm PASS\,completo}\leq2
\]

e veredito:

`STRONG_FAIL_SPLIT_SAMPLE_ONSET`.

## 13. Interpretação

- detecção recuperada com onset ainda ruim: reutilização dos dados era a principal causa do colapso de recall, mas a dobradiça continua sendo estimador inadequado;
- detecção ainda colapsada: o problema não era apenas reutilização;
- passe completo: o onset absoluto pode ser removido mantendo endpoint, forma e duração como oráculos.

## 14. Regras contra puxadinho

1. Exatamente uma partição: seleção, uma guarda e oito cadências de confirmação.
2. Exatamente 51 candidatos.
3. Exatamente 50.000 negativos por família.
4. Exatamente dez holdouts.
5. Nenhuma amostra de confirmação participa da seleção.
6. Nenhum parâmetro será ajustado após abrir a calibração.
7. Nenhum holdout será aberto antes de congelar o limiar.
8. Nenhuma seed, família, estrato ou lote será excluído.
9. O onset verdadeiro é usado apenas para mensurar erro nos positivos.
10. Código, seeds, limiar e dependências serão congelados por hash.
