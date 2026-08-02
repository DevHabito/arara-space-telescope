# ARARA From Zero — Pré-registro M23 Stable Calibration and Late-Onset Tolerance

**Versão:** M23.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** teste de erro tardio de onset condicionado a limiares grandes e congelados.

## 1. Pergunta pequena

Com limiares calibrados uma única vez em 50.000 negativos por família e congelados antes dos holdouts, \(13.75\sigma\) em \(t_{50}\) tolera um onset fornecido uma ou duas cadências tarde?

## 2. Condição fixa

\[
A/\sigma_0=13.75,\qquad f=0.50.
\]

O endpoint \(t_{50}\), a forma e a duração verdadeiros continuam sendo fornecidos.

## 3. Erros tardios congelados

\[
\delta\in\{0,+1,+2\}.
\]

\[
\widehat\tau=\tau+\delta.
\]

O template bruto é deslocado pelo mesmo \(\delta\), preenchido por zero e processado pelo operador SBW da curva.

## 4. Calibração única e estável

Antes de abrir qualquer holdout serão gerados 50.000 negativos por cada uma das cinco famílias.

Cada curva será avaliada nos três erros emparelhados. Cada erro recebe limiar próprio:

\[
\theta_0,\theta_{+1},\theta_{+2}.
\]

Os limiares serão calibrados para FPR empírico máximo de 0,5% em cada família e congelados por hash.

Nenhum holdout será gerado antes do congelamento dos três limiares.

## 5. Dez holdouts independentes

Após o congelamento:

- dez seeds independentes;
- 2.500 positivos por cada um dos oito estratos em cada holdout;
- 5.000 negativos por família em cada holdout;
- 20 lotes por holdout;
- mesmos campos emparelhados entre os três erros dentro de cada holdout;
- bootstrap estratificado com 10.000 réplicas por erro e holdout.

Root seeds:

- calibração: `2026081801`;
- holdouts: `2026081802`;
- bootstraps agregados: `2026081803`.

## 6. Passe por holdout e erro

Para um erro \(\delta\), um holdout passa somente se:

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

## 7. Passe agregado por erro

Um erro passa se:

1. pelo menos 8/10 holdouts passam;
2. limite inferior hierárquico do recall agregado \(\geq0.60\);
3. pelo menos 9/10 holdouts controlam FPR;
4. nenhuma família ultrapassa limite superior de 1,5%.

## 8. Vereditos globais

`PASS_LATE_ONSET_PLUS2` se os três erros passam.

`PASS_LATE_ONSET_PLUS1` se \(\delta=0\) e \(\delta=+1\) passam, mas \(+2\) não passa.

`STRONG_FAIL_STABLE_ONSET` se \(\delta=0\) ou \(\delta=+1\) falha fortemente.

Qualquer resultado intermediário será `INCONCLUSIVE`.

## 9. Previsão anterior aos dados

Prevê-se:

1. \(\delta=0\) passará;
2. \(\delta=+1\) passará;
3. \(\delta=+2\) será inconclusivo;
4. os três erros terão FPR robusto;
5. recall agregado será monotonicamente decrescente:
\[
R(0)>R(+1)>R(+2);
\]
6. veredito `PASS_LATE_ONSET_PLUS1`.

Faixas previstas:

\[
R(0)\in[0.64,0.70],
\]

\[
R(+1)\in[0.62,0.68],
\]

\[
R(+2)\in[0.58,0.63].
\]

## 10. Interpretação

Um passe em +1 demonstrará tolerância condicionada a uma estimativa externa atrasada em no máximo uma cadência.

Um passe em +2 demonstrará tolerância condicionada de duas cadências.

Nenhum resultado valida ainda busca autônoma de onset.

## 11. Regras contra puxadinho

1. Exatamente 50.000 negativos por família.
2. Exatamente três erros e dez holdouts.
3. Nenhum holdout será aberto antes do congelamento dos limiares.
4. Nenhum limiar será recalibrado após os holdouts.
5. Nenhum erro, seed, estrato, família ou lote será excluído.
6. Nenhuma alteração após a abertura da calibração.
7. Endpoint, forma e duração permanecem explicitamente classificados como oráculos.
8. Código, seeds, limiares e dependências serão congelados por hash.
