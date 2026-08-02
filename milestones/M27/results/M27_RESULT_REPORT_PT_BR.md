# ARARA From Zero — Relatório do M27 Exact-Onset 16-Cadence Confirmation

**Estado:** concluído  
**Calibração:** 50.000 negativos por família  
**Holdouts:** 10/10  
**Veredito:** `STRONG_FAIL_EXACT_ONSET_16_CONFIRMATION`  
**Decisão:** rejeitar a confirmação de 16 cadências sob o protocolo atual

## 1. Pergunta

Com onset, forma, duração e endpoint t50 exatos, ampliar a confirmação de 8 para 16 cadências recupera o contrato?

## 2. Alteração única

- M26: oito últimas cadências até t50;
- M27: dezesseis últimas cadências até t50;
- uma guarda, mesmo operador SBW, mesmo matched filter normalizado e mesmos gates.

## 3. Calibração

Limiar congelado: `21.526670`.

Família determinante: `shared_step`.

| Família | Limiar específico | Alertas de calibração | Taxa |
|---|---:|---:|---:|
| `quiet` | 3.917926 | 0/50000 | 0.000000 |
| `shared_ramp` | 16.308826 | 52/50000 | 0.001040 |
| `shared_step` | 21.526670 | 250/50000 | 0.005000 |
| `shared_bump` | 16.773134 | 58/50000 | 0.001160 |
| `shared_oscillation` | 11.544445 | 4/50000 | 0.000080 |

## 4. Resultado agregado

- recall agregado: `0.164580`;
- limite inferior unilateral de 95%: `0.162840`;
- limite superior unilateral de 95%: `0.166290`;
- holdouts aprovados: `0/10`;
- holdouts com FPR aprovado: `10/10`;
- violação extrema: `False`.

O limite superior inteiro do recall ficou abaixo de 17%, muito distante do gate de 60%. A falha forte é inequívoca.

## 5. Resultado por holdout

| Holdout | Recall | Limite inferior 95% | Estratos | Lotes | FPR | Passou |
|---:|---:|---:|---:|---:|---|---|
| 0 | 0.162050 | 0.157950 | 0/8 | 0/20 | SIM | NÃO |
| 1 | 0.166650 | 0.162400 | 0/8 | 0/20 | SIM | NÃO |
| 2 | 0.165100 | 0.160947 | 0/8 | 0/20 | SIM | NÃO |
| 3 | 0.168300 | 0.164050 | 0/8 | 0/20 | SIM | NÃO |
| 4 | 0.162400 | 0.158350 | 0/8 | 0/20 | SIM | NÃO |
| 5 | 0.166200 | 0.162000 | 0/8 | 0/20 | SIM | NÃO |
| 6 | 0.162950 | 0.158750 | 0/8 | 0/20 | SIM | NÃO |
| 7 | 0.165650 | 0.161400 | 0/8 | 0/20 | SIM | NÃO |
| 8 | 0.161600 | 0.157400 | 0/8 | 0/20 | SIM | NÃO |
| 9 | 0.164900 | 0.160750 | 0/8 | 0/20 | SIM | NÃO |

## 6. Resultado por forma

| Estrato | Recall |
|---|---:|
| `exponential__clean` | 0.111720 |
| `exponential__concurrent` | 0.272320 |
| `linear__clean` | 0.137960 |
| `linear__concurrent` | 0.296400 |
| `logistic__clean` | 0.030160 |
| `logistic__concurrent` | 0.128840 |
| `power_law__clean` | 0.094960 |
| `power_law__concurrent` | 0.244280 |

Nenhum estrato chegou perto de fechar o contrato. As condições concorrentes tiveram recall maior que as clean, mas isso não representa vantagem operacional; é uma propriedade do modelo sintético e do score.

## 7. Falso alerta

Todos os dez holdouts controlaram o FPR e nenhuma família ultrapassou 1%.

| Família | Alertas totais | Curvas | Taxa | Maior limite superior 95% |
|---|---:|---:|---:|---:|
| `quiet` | 0 | 50000 | 0.000000 | 0.000599 |
| `shared_bump` | 60 | 50000 | 0.001200 | 0.003390 |
| `shared_oscillation` | 2 | 50000 | 0.000040 | 0.000948 |
| `shared_ramp` | 48 | 50000 | 0.000960 | 0.002628 |
| `shared_step` | 208 | 50000 | 0.004160 | 0.007670 |

A falha não veio de falso alerta descontrolado. O limiar imposto por `shared_step` controlou o nulo, mas eliminou a maior parte dos positivos.

## 8. Comparação com M26

| Teste | Janela | Limiar | Recall | Passes |
|---|---:|---:|---:|---:|
| M26 | 8 | 16.623075 | 0.284350 | 0/10 |
| M27 | 16 | 21.526670 | 0.164580 | 0/10 |

A janela de 16 cadências não resgatou o contrato; nesta execução prospectiva, o limiar aumentou e o recall caiu. M26 e M27 usam calibrações e holdouts independentes, portanto essa diferença não deve ser tratada como estimativa pareada exata do efeito de dobrar a janela. O veredito próprio do M27, porém, é válido: 16 cadências falharam fortemente.

## 9. Previsão

- limiar entre 20 e 26: `CONFIRMADA`;
- recall entre 0,45 e 0,62: `REFUTADA`;
- 2–6 holdouts aprovados: `REFUTADA`;
- veredito inconclusivo: `REFUTADA`.

Previsão integralmente confirmada: `False`.

O resultado foi muito pior que a previsão.

## 10. Conclusão permitida

> Sob alinhamento-oráculo completo, o matched filter restrito às 16 últimas cadências até t50 falhou fortemente. Aumentar de 8 para 16 cadências não tornou essa família de confirmação operacional sob o nulo atual.

## 11. Próximo teste correto

Não é prudente saltar automaticamente para 24 cadências: M26 e M27 mostram que o efeito da janela não é monotônico sob calibrações independentes e `shared_step` domina a cauda.

O próximo teste deve ser pareado: nos mesmos campos negativos e positivos, calcular janelas de 8, 16, 24 e o intervalo completo, com um limiar próprio por janela. Isso isolará a curva comprimento–limiar–recall sem confundir o efeito da janela com seeds diferentes.

Se a curva pareada confirmar que janelas intermediárias são piores, o próximo passo será uma estatística explicitamente resistente a degraus compartilhados, e não simplesmente aumentar o comprimento.