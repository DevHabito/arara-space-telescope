# ARARA From Zero — Relatório do M31 Independent Confirmation

**Estado:** concluído  
**Natureza:** réplica confirmatória exata do M30  
**Nova calibração:** 50.000 negativos por família  
**Novos holdouts:** 10/10  
**Veredito:** `CONFIRMED_REFERENCE_PROJECTION`  

## 1. Resultado principal

O M31 importou diretamente a implementação matemática congelada do M30. Somente seeds, curvas, calibração e holdouts foram substituídos.

| Método | Limiar | Família determinante | Recall | Limite inferior unilateral 95% | Limite superior unilateral 95% | Passes | FPR |
|---|---:|---|---:|---:|---:|---:|---:|
| `baseline8` | 16.332716 | `shared_step` | 0.301910 | 0.299865 | 0.303980 | 0/10 | 10/10 |
| `reference_projected8` | 4.074482 | `shared_ramp` | 0.796505 | 0.794665 | 0.798355 | 10/10 | 10/10 |

O candidato voltou a passar em 10/10 holdouts.

## 2. Superioridade pareada

- baseline: `0.301910`;
- candidato: `0.796505`;
- diferença: `0.494595`;
- limite inferior unilateral de 95% da diferença: `0.492025`;
- limite superior unilateral de 95% da diferença: `0.497155`;
- holdouts com ganho de pelo menos 0,08: `10/10`.

O gate de superioridade foi novamente satisfeito com ampla margem.

## 3. Resultado por holdout

| Holdout | Baseline | Candidato | Diferença | Limite inferior candidato | Estratos | Lotes | Passou |
|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | 0.303800 | 0.796200 | 0.492453 | 0.792150 | 8/8 | 20/20 | SIM |
| 1 | 0.298200 | 0.792800 | 0.494587 | 0.788650 | 8/8 | 20/20 | SIM |
| 2 | 0.300950 | 0.797800 | 0.496849 | 0.793750 | 8/8 | 20/20 | SIM |
| 3 | 0.301450 | 0.792800 | 0.491455 | 0.788700 | 8/8 | 20/20 | SIM |
| 4 | 0.299600 | 0.794700 | 0.495098 | 0.790600 | 8/8 | 20/20 | SIM |
| 5 | 0.300700 | 0.798100 | 0.497431 | 0.793950 | 8/8 | 20/20 | SIM |
| 6 | 0.301900 | 0.800300 | 0.498415 | 0.796150 | 8/8 | 20/20 | SIM |
| 7 | 0.307000 | 0.794800 | 0.487811 | 0.790700 | 8/8 | 20/20 | SIM |
| 8 | 0.304000 | 0.799850 | 0.495897 | 0.795800 | 8/8 | 20/20 | SIM |
| 9 | 0.301500 | 0.797700 | 0.496227 | 0.793650 | 8/8 | 20/20 | SIM |

## 4. Resultado por estrato

| Estrato | Baseline | Candidato | Retenção média de energia |
|---|---:|---:|---:|
| `exponential__clean` | 0.247040 | 0.993000 | 0.789512 |
| `exponential__concurrent` | 0.407360 | 0.588440 | 0.219130 |
| `linear__clean` | 0.270120 | 0.993240 | 0.788716 |
| `linear__concurrent` | 0.431240 | 0.578040 | 0.198459 |
| `logistic__clean` | 0.136000 | 0.987560 | 0.794268 |
| `logistic__concurrent` | 0.295920 | 0.647920 | 0.248134 |
| `power_law__clean` | 0.231200 | 0.991560 | 0.791156 |
| `power_law__concurrent` | 0.396400 | 0.592280 | 0.221689 |

## 5. Falso alerta

Os dois métodos controlaram o FPR em 10/10 holdouts. Não houve violação extrema.

| Método | Família | Taxa agregada | Maior limite superior unilateral 95% |
|---|---|---:|---:|
| `baseline8` | `quiet` | 0.000000 | 0.000599 |
| `baseline8` | `shared_bump` | 0.001200 | 0.003139 |
| `baseline8` | `shared_oscillation` | 0.000740 | 0.002628 |
| `baseline8` | `shared_ramp` | 0.001580 | 0.004374 |
| `baseline8` | `shared_step` | 0.005120 | 0.008815 |
| `reference_projected8` | `quiet` | 0.002820 | 0.006277 |
| `reference_projected8` | `shared_bump` | 0.004340 | 0.007439 |
| `reference_projected8` | `shared_oscillation` | 0.002780 | 0.006042 |
| `reference_projected8` | `shared_ramp` | 0.004760 | 0.007900 |
| `reference_projected8` | `shared_step` | 0.004820 | 0.009497 |

## 6. Consistência M30–M31

- recall M30: `0.798225`;
- recall M31: `0.796505`;
- diferença M31−M30: `-0.001720`;
- passes: `10/10` em ambos;
- limiar candidato M30: `4.052855`;
- limiar candidato M31: `4.074482`.

A diferença de recall foi de aproximadamente -0,17 ponto percentual, pequena em relação ao efeito de quase 49 pontos sobre o baseline.

A família determinante do limiar candidato mudou de `shared_step` no M30 para `shared_ramp` no M31. Isso não alterou o controle de FPR nem o passe operacional.

## 7. Previsão

- baseline na faixa: `CONFIRMADA`;
- candidato na faixa: `CONFIRMADA`;
- diferença na faixa: `CONFIRMADA`;
- FPR robusto: `CONFIRMADO`;
- passes previstos: `CONFIRMADOS`;
- sem degeneração do template: `CONFIRMADO`;
- veredito confirmatório: `CONFIRMADO`.

Previsão integralmente confirmada: `True`.

## 8. Conclusão permitida

> O downstream sintético `reference_projected8` foi confirmado em uma réplica com nova calibração, novas seeds e dez novos holdouts. Sob onset, endpoint, forma e duração exatos, ele alcançou recall agregado de 79,65%, controle robusto de falso alerta e 10/10 holdouts aprovados.

## 9. Limite da independência

A independência do M31 é de dados, seeds, calibração e holdouts. A implementação matemática foi deliberadamente importada do M30 para impedir drift de código. Portanto, isto não é uma reimplementação independente por uma segunda equipe.

## 10. O que ainda não está demonstrado

- onset autônomo;
- endpoint autônomo;
- seleção autônoma de forma e duração;
- desempenho em dados astronômicos reais;
- tradução para fótons, abertura, magnitude e hardware;
- viabilidade de missão.

## 11. Próximo teste correto

O próximo passo deve retirar apenas o onset-oráculo, mantendo o downstream M31 confirmado.

O controle apropriado é reaplicar o estimador causal dividido do M25, mas trocar o antigo matched filter pelo `reference_projected8` confirmado. O endpoint, a forma e a duração permanecem exatos. Assim o efeito da estimativa de onset será isolado sobre um downstream que já funciona quando recebe o onset correto.

## 12. Registro operacional

Uma chamada de execução foi interrompida pelo limite de tempo após a persistência dos holdouts 0–6. Esses arquivos foram verificados, e os holdouts 7–9 foram concluídos com as seeds originalmente congeladas. Nenhum dado, seed ou gate foi substituído. O registro detalhado está em `POST_HOLDOUT_EXECUTION_INCIDENT.md`.
