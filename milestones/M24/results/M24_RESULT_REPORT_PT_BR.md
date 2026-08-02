# ARARA From Zero — Relatório do M24 Causal Hinge Onset Estimator

**Estado:** concluído  
**Calibração:** 50.000 negativos por família  
**Holdouts:** 10/10 concluídos  
**Veredito:** `STRONG_FAIL_CAUSAL_ONSET_ESTIMATOR`  
**Decisão:** rejeitar o estimador hinge como solução para retirar o onset-oráculo

## 1. Pergunta

Um estimador causal retrospectivo de onset, baseado em uma mudança para subida, consegue preservar a detecção em 13,75σ e colocar pelo menos 90% dos onsets detectados no envelope certificado [-2,+1] cadências?

## 2. Pipeline congelado

1. calcular residual SBW sem usar o sinal;
2. testar 51 onsets inteiros entre 70 e 120;
3. escolher o onset com maior t-score de uma dobradiça linear no intervalo [50,t50];
4. deslocar o template exato de forma e duração para o onset estimado;
5. calcular o score final em [onset estimado,t50];
6. aplicar um limiar calibrado no pipeline inteiro.

Limiar congelado: `14.324525`.

Família determinante: `quiet`.

## 3. Resultado agregado

- recall agregado: `0.019795`;
- intervalo hierárquico de 95%: `0.019095` a `0.020505`;
- holdouts que passaram detecção: `0/10`;
- holdouts que passaram onset: `0/10`;
- holdouts completos aprovados: `0/10`;
- holdouts com FPR aprovado: `9/10`.

O limite superior inteiro do recall permaneceu em aproximadamente 2,05%, muito abaixo do requisito de 60%.

## 4. Acurácia do onset entre eventos detectados

- positivos detectados: `3959`;
- dentro de [-2,+1]: `1239`;
- acurácia pontual: `0.312958`;
- intervalo unilateral de 95%: `0.300815` a `0.325306`;
- estimativas anteriores a -2: `1181`;
- estimativas posteriores a +1: `1539`.

O limite superior da acurácia ficou abaixo de 0,75, acionando independentemente o critério de falha forte.

## 5. Resultado por holdout

| Holdout | Recall | Limite inferior | Acurácia onset | Limite inferior onset | FPR | Passou |
|---:|---:|---:|---:|---:|---|---|
| 0 | 0.021200 | 0.019500 | 0.306604 | 0.269682 | SIM | NÃO |
| 1 | 0.020000 | 0.018400 | 0.297500 | 0.259860 | SIM | NÃO |
| 2 | 0.019300 | 0.017700 | 0.277202 | 0.239799 | SIM | NÃO |
| 3 | 0.019750 | 0.018200 | 0.291139 | 0.253535 | SIM | NÃO |
| 4 | 0.020550 | 0.018950 | 0.284672 | 0.248084 | SIM | NÃO |
| 5 | 0.020250 | 0.018650 | 0.362963 | 0.323268 | NÃO | NÃO |
| 6 | 0.018300 | 0.016800 | 0.368852 | 0.326906 | SIM | NÃO |
| 7 | 0.019650 | 0.018097 | 0.277354 | 0.240277 | SIM | NÃO |
| 8 | 0.020900 | 0.019250 | 0.356459 | 0.317578 | SIM | NÃO |
| 9 | 0.018050 | 0.016500 | 0.307479 | 0.267432 | SIM | NÃO |

## 6. Resultado por forma

| Estrato | Recall | Acurácia onset entre detectados | Muito cedo | Muito tarde |
|---|---:|---:|---:|---:|
| `exponential__clean` | 0.008800 | 0.077273 | 8 | 195 |
| `exponential__concurrent` | 0.036680 | 0.226827 | 261 | 448 |
| `linear__clean` | 0.013880 | 0.691643 | 45 | 62 |
| `linear__concurrent` | 0.058040 | 0.428670 | 675 | 154 |
| `logistic__clean` | 0.004640 | 0.017241 | 0 | 114 |
| `logistic__concurrent` | 0.009080 | 0.171806 | 28 | 160 |
| `power_law__clean` | 0.004080 | 0.058824 | 0 | 96 |
| `power_law__concurrent` | 0.023160 | 0.181347 | 164 | 310 |

As curvas lineares foram as menos incompatíveis com o estimador. Power-law, exponencial e logística apresentaram forte tendência de estimativa tardia.

Mesmo nas lineares, o recall operacional permaneceu baixo porque o limiar nulo aumentou muito após a escolha adaptativa do onset.

## 7. Por que o limiar subiu

No M23, com onset fornecido, os limiares ficaram próximos de 7,3. No M24, o pipeline procura o melhor entre 51 candidatos usando os mesmos dados que alimentam o score final.

O limiar passou para `14.324525`.

Isso é um efeito legítimo de look-elsewhere e seleção: negativos também conseguem escolher um onset que maximiza uma flutuação favorável. A calibração não remove esse custo; ela o quantifica.

A família `quiet` determinou o limiar, mostrando que o principal custo veio da busca adaptativa em ruído, não apenas dos artefatos compartilhados.

## 8. Falso alerta

O FPR agregado permaneceu controlado em 9/10 holdouts e nenhuma família ultrapassou o limite extremo de 1,5%.

A única violação do limite de 1% ocorreu no holdout `5`, família `quiet`.

`FPR_upper_95 = 0.010401`.

A falha científica não foi causada principalmente pelo FPR. Ela veio do recall extremamente baixo e da baixa precisão do onset.

## 9. Previsão

- recall previsto entre 0,48 e 0,60: `REFUTADA` — observado `0.019795`;
- acurácia prevista entre 0,25 e 0,60: `CONFIRMADA`;
- no máximo dois holdouts completos: `CONFIRMADA`;
- falha forte prevista: `CONFIRMADA`.

Previsão integralmente confirmada: `False`.

O fracasso foi muito mais severo que o previsto.

## 10. Conclusão permitida

> O estimador causal retrospectivo de dobradiça foi rejeitado. A busca entre 51 onsets elevou fortemente a cauda nula, reduziu o recall agregado para aproximadamente 2% e colocou somente cerca de 31% dos onsets detectados no envelope [-2,+1].

## 11. O que não pode ser concluído

- não foi provado que onset causal seja impossível;
- não foi testado um estimador matched-filter ótimo;
- não foi testada separação de dados entre estimativa de onset e score;
- endpoint, forma e duração permaneceram como oráculos.

## 12. Próximo teste correto

Não devemos ajustar informalmente a dobradiça até ela passar.

O próximo teste deve separar a amostra usada para estimar onset da amostra usada para confirmar o evento:

- estimar onset somente até t25 ou em uma janela inicial;
- congelar a estimativa;
- calcular o score de confirmação apenas em amostras posteriores independentes da escolha;
- calibrar o pipeline inteiro novamente.

Isso testará se o colapso veio principalmente da reutilização dos mesmos dados e do look-elsewhere, em vez de apenas da forma do estimador.