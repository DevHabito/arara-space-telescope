# ARARA-M28 — Nota de implementação congelada

**Versão:** 28.0  
**Estado:** congelada antes da calibração.

## 1. Cálculo pareado

Para cada curva, o residual SBW e o template processado são calculados uma única vez.

Os quatro scores são obtidos por máscaras diferentes sobre esses mesmos arrays. Não há regeneração da curva entre comprimentos.

## 2. Estatística

Todos os comprimentos usam exatamente:

\[
Z=\frac{r^\top h}{\|h\|_2}.
\]

A única variável alterada é a máscara temporal.

`full` usa o suporte entre onset e endpoint. Os comprimentos fixos usam as últimas 8, 16 ou 24 cadências até o endpoint. Valores do template anteriores ao onset são zero.

## 3. Calibração

Cada arquivo de família negativa contém os quatro vetores de scores pareados. Os quatro limiares são calculados somente depois de todos os arquivos terem sido persistidos e verificados.

## 4. Holdouts

Cada positivo e negativo produz os quatro scores antes de qualquer comparação com limiar.

Além dos gates primários, são preservados:

- scores correlacionados;
- contagens de detecção exclusiva por par de comprimentos;
- diferença de recall por holdout;
- AUROC e AP por comprimento.

Esses diagnósticos não alteram o veredito.

## 5. Confiança

O projeto usa gates unilaterais de 95%:

- quantil 0,05 como limite inferior;
- quantil 0,95 como limite superior.

A apresentação conjunta dos dois valores será explicitamente rotulada como limites unilaterais de 95%, não como intervalo bilateral de 95%.
