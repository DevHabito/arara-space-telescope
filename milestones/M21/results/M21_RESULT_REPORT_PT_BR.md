# ARARA From Zero — Relatório do M21 Independent Confirmation of 13,75σ at t50

**Estado:** concluído  
**Replicações:** 10/10  
**Veredito científico:** `PASS_CONFIRMATORY`  
**Veredito numérico:** `PASS`  
**Decisão:** 13,75σ substitui 14σ como menor nível robustamente confirmado entre os níveis testados

## 1. Pergunta

O candidato adaptativo de 13,75σ identificado no M20 se confirma em dez novas replicações completas, sem nova seleção de SNR?

## 2. Resultado agregado

- recall agregado: `0.673305`;
- intervalo hierárquico de 95%: `0.658125` a `0.688560`;
- replicações aprovadas: `10/10`;
- replicações com FPR aprovado: `10/10`;
- violação extrema de FPR: `False`.

Todos os critérios confirmatórios foram satisfeitos.

## 3. Resultado por replicação

| Replicação | Limiar | Recall | Limite inferior 95% | Estratos | Lotes | FPR | Passou |
|---:|---:|---:|---:|---:|---:|---|---|
| 0 | 7.293417 | 0.675350 | 0.669850 | 8/8 | 20/20 | PASSOU | SIM |
| 1 | 7.210591 | 0.691400 | 0.686000 | 8/8 | 20/20 | PASSOU | SIM |
| 2 | 7.413955 | 0.664800 | 0.659350 | 8/8 | 20/20 | PASSOU | SIM |
| 3 | 6.841455 | 0.731300 | 0.726200 | 8/8 | 20/20 | PASSOU | SIM |
| 4 | 7.412633 | 0.657650 | 0.652200 | 8/8 | 20/20 | PASSOU | SIM |
| 5 | 7.634862 | 0.628550 | 0.622950 | 8/8 | 20/20 | PASSOU | SIM |
| 6 | 7.208908 | 0.683200 | 0.677850 | 8/8 | 20/20 | PASSOU | SIM |
| 7 | 7.301354 | 0.672450 | 0.667100 | 8/8 | 20/20 | PASSOU | SIM |
| 8 | 7.623803 | 0.632550 | 0.627097 | 7/8 | 20/20 | PASSOU | SIM |
| 9 | 7.127444 | 0.695800 | 0.690450 | 8/8 | 20/20 | PASSOU | SIM |

## 4. Previsão

- 8–10 replicações passariam: confirmada;
- recall agregado entre 0,635 e 0,685: confirmada;
- veredito confirmatório: confirmado.

Previsão integralmente confirmada: `True`.

## 5. Relação M20 → M21

| Teste | Natureza | Passes | Recall agregado | Veredito |
|---|---|---:|---:|---|
| M20 | Refinamento adaptativo | 8/10 | 0.659400 | PASS_REFINEMENT_CANDIDATE |
| M21 | Confirmação independente | 10/10 | 0.673305 | PASS_CONFIRMATORY |

O M21 utilizou seeds totalmente novas e manteve o mesmo nível de 13,75σ. Portanto, a seleção adaptativa do M20 foi seguida por confirmação independente válida.

## 6. Comparação robusta em t50

| SNR | Evidência robusta | Estado |
|---:|---|---|
| 12σ | 1/10 no M15; M16 não resgatou com calibração maior | Rejeitado |
| 13σ | 6/10 no M18 | Inconclusivo |
| 13,5σ | 7/10 no M19 | Inconclusivo |
| 13,75σ | 8/10 no M20 e 10/10 no M21 | Confirmado |
| 14σ | 10/10 no M17 | Confirmado |

## 7. Conclusão permitida

> No modelo sintético atual e sob alinhamento-oráculo, 13,75σ em t50 satisfaz robustamente o contrato e foi confirmado em uma execução independente após o refinamento adaptativo.

## 8. O que isso não prova

- não demonstra que 13,75σ seja o mínimo matemático;
- não valida um detector autônomo;
- não converte diretamente SNR em abertura, magnitude ou exposição;
- onset e template exatos continuam sendo fornecidos.

## 9. Estado do requisito

O menor nível robustamente confirmado entre os níveis testados passa a ser:

`13,75σ em t50`.

O intervalo inferior não resolvido permanece entre 13,5σ e 13,75σ. Qualquer refinamento adicional exigirá novamente uma etapa adaptativa e uma confirmação independente separada.