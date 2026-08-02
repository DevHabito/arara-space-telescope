# ARARA From Zero — Relatório do M25 Split-Sample Onset Estimation and Confirmation

**Estado:** concluído  
**Calibração:** 50.000 negativos por família  
**Holdouts:** 10/10 concluídos  
**Veredito:** `STRONG_FAIL_SPLIT_SAMPLE_ONSET`  
**Decisão:** a separação temporal melhora o recall frente ao M24, mas não resgata o contrato nem o estimador de onset

## 1. Pergunta

Separar os dados usados para escolher o onset daqueles usados para confirmar o evento elimina o colapso observado no M24?

## 2. Partição congelada

Para cada endpoint e=t50:

- seleção: `[50,e-9]`;
- guarda: `e-8`;
- confirmação: `[e-7,e]`, exatamente oito cadências.

A confirmação não reutilizou nenhuma amostra bruta da seleção.

## 3. Calibração

Limiar congelado: `16.778311`.

Família determinante: `shared_step`.

A previsão de que o limiar cairia abaixo do M24 foi refutada:

- M24: `14.324525`;
- M25: `16.778311`;
- mudança: `+2.453786`.

A família `shared_step` dominou a cauda nula do matched filter de oito pontos.

## 4. Resultado agregado

- recall agregado: `0.270425`;
- intervalo hierárquico de 95%: `0.267820` a `0.273030`;
- holdouts que passaram detecção: `0/10`;
- holdouts que passaram onset: `0/10`;
- holdouts completos aprovados: `0/10`;
- holdouts com FPR aprovado: `10/10`.

O limite superior do recall permaneceu em 27,30%, muito abaixo do requisito de 60%. Isso aciona falha forte independentemente dos demais gates.

## 5. Acurácia do onset

- positivos detectados: `54085`;
- dentro de [-2,+1]: `15017`;
- acurácia pontual: `0.277656`;
- intervalo de 95%: `0.274488` a `0.280841`;
- estimativas anteriores a -2: `15739`;
- estimativas posteriores a +1: `23329`.

O limite superior da acurácia ficou em 28,08%, também acionando falha forte.

A mediana do erro por holdout foi aproximadamente +1 cadência, mas a mediana do erro absoluto foi 4 cadências. A mediana próxima de zero esconde caudas largas nos dois sentidos.

## 6. Resultado por holdout

| Holdout | Recall | Limite inferior | Acurácia onset | Limite inferior onset | FPR | Passou |
|---:|---:|---:|---:|---:|---|---|
| 0 | 0.264750 | 0.259800 | 0.279131 | 0.268989 | SIM | NÃO |
| 1 | 0.276300 | 0.271300 | 0.281216 | 0.271265 | SIM | NÃO |
| 2 | 0.271000 | 0.265900 | 0.273432 | 0.263473 | SIM | NÃO |
| 3 | 0.276800 | 0.271650 | 0.279444 | 0.269521 | SIM | NÃO |
| 4 | 0.266150 | 0.261100 | 0.276348 | 0.266264 | SIM | NÃO |
| 5 | 0.270250 | 0.265150 | 0.269750 | 0.259821 | SIM | NÃO |
| 6 | 0.270900 | 0.265900 | 0.274086 | 0.264118 | SIM | NÃO |
| 7 | 0.270350 | 0.265400 | 0.282227 | 0.272155 | SIM | NÃO |
| 8 | 0.272650 | 0.267600 | 0.281313 | 0.271294 | SIM | NÃO |
| 9 | 0.265100 | 0.260050 | 0.279517 | 0.269377 | SIM | NÃO |

## 7. Resultado por forma

| Estrato | Recall | Acurácia onset entre detectados | Muito cedo | Muito tarde |
|---|---:|---:|---:|---:|
| `exponential__clean` | 0.215480 | 0.229441 | 691 | 3460 |
| `exponential__concurrent` | 0.372760 | 0.233072 | 3518 | 3629 |
| `linear__clean` | 0.243280 | 0.552614 | 1303 | 1418 |
| `linear__concurrent` | 0.399360 | 0.454627 | 3681 | 1764 |
| `logistic__clean` | 0.113680 | 0.158339 | 563 | 1829 |
| `logistic__concurrent` | 0.255720 | 0.198655 | 2571 | 2552 |
| `power_law__clean` | 0.202440 | 0.105315 | 425 | 4103 |
| `power_law__concurrent` | 0.360680 | 0.161473 | 2987 | 4574 |

As formas lineares permaneceram mais compatíveis com a dobradiça. Power-law e logística apresentaram principalmente estimativas tardias.

## 8. Falso alerta

Todos os dez holdouts controlaram o FPR e nenhuma combinação ultrapassou 1%.

| Família | Alertas totais | Curvas | Taxa | Maior limite superior 95% |
|---|---:|---:|---:|---:|
| `quiet` | 0 | 50000 | 0.000000 | 0.000599 |
| `shared_bump` | 69 | 50000 | 0.001380 | 0.004131 |
| `shared_oscillation` | 15 | 50000 | 0.000300 | 0.001830 |
| `shared_ramp` | 78 | 50000 | 0.001560 | 0.003390 |
| `shared_step` | 262 | 50000 | 0.005240 | 0.009497 |

A falha não veio de falso alerta. O limiar conservador controlou o FPR, mas removeu a maior parte dos positivos.

## 9. Comparação M24 → M25

- recall: `0.019795` → `0.270425`;
- ganho absoluto: `25.06` pontos percentuais;
- multiplicação do recall: `13.66x`;
- acurácia de onset: `0.312958` → `0.277656`;
- limiar: `14.324525` → `16.778311`.

A separação temporal recuperou parte substancial do recall, mostrando que a reutilização dos dados era um problema real. Porém, não era o único problema.

O novo score de confirmação ficou muito sensível a degraus compartilhados, elevando ainda mais o limiar. Ao mesmo tempo, a dobradiça continuou localizando mal o onset.

## 10. Previsão

- limiar menor que o M24: `REFUTADA`;
- recall entre 0,55 e 0,80: `REFUTADA`;
- acurácia entre 0,20 e 0,55: `CONFIRMADA`;
- pelo menos oito holdouts passariam detecção: `REFUTADA`;
- no máximo dois holdouts completos: `CONFIRMADA`;
- falha forte: `CONFIRMADA`.

Previsão integralmente confirmada: `False`.

A direção do veredito foi prevista, mas o mecanismo e a severidade foram parcialmente diferentes do esperado.

## 11. Conclusão permitida

> Separar temporalmente seleção e confirmação elevou o recall de cerca de 2% para 27%, demonstrando que a reutilização dos mesmos dados contribuía para o colapso do M24. Entretanto, o contrato continuou muito longe de ser satisfeito, o limiar aumentou por causa da família shared_step e a precisão do onset permaneceu abaixo de 28%.

## 12. Próximo controle obrigatório

M25 alterou simultaneamente a disponibilidade do onset e a estatística de confirmação. Portanto, o próximo teste não deve inventar outro estimador.

O controle correto é usar o onset exato com a mesma partição, a mesma guarda e o mesmo matched filter de oito pontos.

Esse M26 responderá:

- se o onset exato também produzir recall baixo, a janela/estatística de confirmação é o gargalo principal;
- se o onset exato recuperar o contrato, a dobradiça é o gargalo principal.