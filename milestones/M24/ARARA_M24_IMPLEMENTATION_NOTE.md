# ARARA-M24 — Nota de implementação congelada

**Versão:** 24.0  
**Estado:** congelada antes da geração da calibração.

## 1. Estimador

O hinge scan usa apenas o residual SBW e o endpoint fornecido.

Para acelerar sem alterar a matemática:

- os 51 regressores são pré-computados;
- produtos escalares são calculados por multiplicação matricial;
- somas dos regressores até cada endpoint são obtidas por cumulativas;
- o score é exatamente a correlação t unilateral com intercepto removido.

## 2. Template final

A forma relativa exata é representada por um sinal de referência. Para cada curva, todas as decisões usam somente o onset estimado.

O onset verdadeiro ou virtual é usado internamente apenas para converter a representação de referência em uma translação relativa. Como a translação final é determinada por \(\widehat\tau\), a decisão não recebe o onset verdadeiro.

## 3. Calibração

Cada família possui stream independente e contínua através dos blocos de 1.000 curvas.

São persistidos:

- score final;
- onset estimado;
- endpoint virtual.

O limiar é congelado antes dos holdouts.

## 4. Holdouts

O erro de onset só é calculado depois de \(\widehat\tau\) e o score terem sido produzidos.

A acurácia primária usa somente positivos declarados pelo limiar congelado:

\[
-2\leq\widehat\tau-\tau\leq+1.
\]

## 5. Limite causal

O estimador é retrospectivamente causal em \(t_{50}\): não usa nenhuma amostra posterior ao endpoint fornecido. Ele não produz ainda um alerta em streaming antes de \(t_{50}\).
