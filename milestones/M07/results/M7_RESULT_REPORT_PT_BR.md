# ARARA From Zero — Relatório do M7 Oracle at t75

**Estado:** concluído  
**Holdout:** aberto uma única vez  
**Veredito:** `INCONCLUSIVE`  
**Decisão:** **NÃO PROMOVER; TESTAR \(t_{100}\)**

## Resultado primário

- recall: 0.129250 = 12.925%;
- intervalo de 95%: 0.126475 a 0.132050;
- limiar: 8.229795456;
- estratos aprovados: 0/8;
- lotes aprovados: 0/20.

A previsão registrada foi de 12% a 35%. O resultado pontual ficou dentro dessa faixa, mas abaixo do critério de promoção de 30%.

## Resultado por estrato

| Estrato | Recall | Limite inferior 95% |
|---|---:|---:|
| linear__clean | 0.084400 | 0.078014 |
| linear__concurrent | 0.141200 | 0.133156 |
| power_law__clean | 0.141800 | 0.133741 |
| power_law__concurrent | 0.173600 | 0.164832 |
| exponential__clean | 0.117400 | 0.109979 |
| exponential__concurrent | 0.145000 | 0.136864 |
| logistic__clean | 0.092400 | 0.085741 |
| logistic__concurrent | 0.138200 | 0.130230 |

## Falsos alertas

| Família | FPR | Limite superior 95% |
|---|---:|---:|
| quiet | 0.000000 | 0.000599 |
| shared_ramp | 0.003800 | 0.005571 |
| shared_step | 0.000800 | 0.001830 |
| shared_bump | 0.003800 | 0.005571 |
| shared_oscillation | 0.001600 | 0.002885 |

O FPR passou em todas as famílias. `shared_ramp` determinou o limiar de desenvolvimento.

## Clean versus concurrent

- clean: 0.109000;
- concurrent: 0.149500.

A diferença continua sem interpretação astrofísica positiva, porque a perturbação concorrente pode aumentar o score.

## Métricas secundárias

- AUROC: 0.938619;
- Average Precision: 0.955768.

## Conclusão

> Até 75% da amplitude, o contrato tornou-se parcialmente informativo, mas ainda não operacional: recall próximo de 13% sob alinhamento-oráculo.

O próximo teste permitido é \(t_{100}\), alterando apenas a fração final.
