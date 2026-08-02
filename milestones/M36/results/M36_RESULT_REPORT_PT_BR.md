# ARARA From Zero — Relatório do M36 Four-Shape Rolling Bank

**Estado:** concluído  
**Hipóteses do controle:** 99 por curva  
**Hipóteses do banco:** 396 por curva  
**Calibração:** 50.000 negativos por família  
**Holdouts:** 10/10  
**Veredito:** `PASS_DETECTION_SHAPE_UNRELIABLE`  

## 1. Pergunta

A detecção rolling confirmada no M35 continua operacional quando o detector deixa de receber o rótulo verdadeiro da forma e avalia as quatro famílias em cada endpoint?

A duração e o parâmetro latente de inclinação permaneceram exatos. Portanto, o M36 retirou somente a identidade discreta da forma.

## 2. Resultado agregado

| Método | Limiar | Família determinante | Recall | Limite inferior unilateral 95% | Limite superior unilateral 95% | Passes | FPR |
|---|---:|---|---:|---:|---:|---:|---:|
| `rolling_exact_shape_latency4` | 6.950809 | `shared_step` | 0.759415 | 0.757730 | 0.761055 | 10/10 | 10/10 |
| `rolling_four_shape_bank_latency4` | 7.105932 | `shared_step` | 0.757055 | 0.755410 | 0.758685 | 10/10 | 10/10 |

O banco de quatro formas passou o contrato de detecção em 10/10 holdouts.

## 3. Custo de retirar o rótulo de forma

- controle com forma exata: `0.759415`;
- banco sem rótulo verdadeiro: `0.757055`;
- diferença banco−controle: `-0.002360`;
- limite inferior unilateral de 95%: `-0.002770`;
- limite superior unilateral de 95%: `-0.001955`.

A perda foi de aproximadamente 0,236 ponto percentual.

O aumento do look-elsewhere de 99 para 396 hipóteses elevou o limiar somente de 6,9508 para 7,1059.

## 4. Resultado por holdout

| Holdout | Controle | Banco | Diferença | Limite inferior banco | Estratos | Lotes | Detecção passou | Acurácia da forma | Forma passou |
|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| 0 | 0.759700 | 0.757200 | -0.002500 | 0.752950 | 6/8 | 20/20 | SIM | 0.293846 | NÃO |
| 1 | 0.760450 | 0.758600 | -0.001850 | 0.754400 | 6/8 | 20/20 | SIM | 0.290865 | NÃO |
| 2 | 0.761450 | 0.758850 | -0.002600 | 0.754747 | 7/8 | 20/20 | SIM | 0.291889 | NÃO |
| 3 | 0.759350 | 0.757450 | -0.001900 | 0.753300 | 7/8 | 20/20 | SIM | 0.293683 | NÃO |
| 4 | 0.761800 | 0.759000 | -0.002800 | 0.754800 | 7/8 | 20/20 | SIM | 0.285573 | NÃO |
| 5 | 0.758450 | 0.755900 | -0.002550 | 0.751650 | 7/8 | 20/20 | SIM | 0.291507 | NÃO |
| 6 | 0.761400 | 0.758350 | -0.003050 | 0.754100 | 7/8 | 20/20 | SIM | 0.287598 | NÃO |
| 7 | 0.759500 | 0.757400 | -0.002100 | 0.753150 | 7/8 | 20/20 | SIM | 0.287299 | NÃO |
| 8 | 0.756350 | 0.754450 | -0.001900 | 0.750200 | 7/8 | 20/20 | SIM | 0.286765 | NÃO |
| 9 | 0.755700 | 0.753350 | -0.002350 | 0.749200 | 6/8 | 20/20 | SIM | 0.286520 | NÃO |

Todos os holdouts passaram detecção. Nenhum passou identificação de forma.

## 5. Resultado por forma e contexto

| Estrato | Controle | Banco |
|---|---:|---:|
| `exponential__clean` | 0.989880 | 0.988000 |
| `exponential__concurrent` | 0.546600 | 0.536280 |
| `linear__clean` | 0.986000 | 0.983840 |
| `linear__concurrent` | 0.503680 | 0.494960 |
| `logistic__clean` | 0.989120 | 0.989160 |
| `logistic__concurrent` | 0.540840 | 0.553880 |
| `power_law__clean` | 0.989360 | 0.988040 |
| `power_law__concurrent` | 0.529840 | 0.522280 |

O banco preservou os contextos clean próximos de 99%. Nos contextos concurrent, o recall variou de 49,50% a 55,39%. Mesmo com alguns estratos agregados próximos da fronteira, cada holdout manteve pelo menos 6/8 estratos aprovados.

## 6. Identificação da forma

- detecções primárias do banco: `151411`;
- formas corretas: `43842`;
- acurácia: `0.289556`;
- limite inferior unilateral de 95%: `0.287639`;
- limite superior unilateral de 95%: `0.291480`;
- holdouts aprovados no gate de 70%: `0/10`.

A acurácia de aproximadamente 28,96% é apenas modestamente superior ao acaso de 25% e está muito abaixo do gate pré-registrado de 70%.

Assim, o banco remove o rótulo de forma da detecção, mas a forma escolhida no primeiro alerta não pode ser interpretada como classificação física confiável.

### Matriz de confusão entre detecções primárias

| Forma verdadeira | Linear | Power-law | Exponencial | Logística | Acurácia da linha |
|---|---:|---:|---:|---:|---:|
| `exponential` | 11911 | 9172 | 9559 | 7465 | 0.250846 |
| `linear` | 14841 | 6665 | 8139 | 7325 | 0.401434 |
| `logistic` | 8374 | 9797 | 9370 | 11035 | 0.286059 |
| `power_law` | 11886 | 8407 | 9262 | 8203 | 0.222655 |

A forma linear foi a mais identificável, com aproximadamente 40,14% de acerto. Power-law foi a menos identificável, com aproximadamente 22,27%.

## 7. Temporalidade do banco

| Categoria | Contagem | Fração |
|---|---:|---:|
| `success_onset_through_t50_plus4` | 151411 | 0.757055 |
| `early_before_onset` | 123 | 0.000615 |
| `late_after_t50_plus4` | 40064 | 0.200320 |
| `no_alert` | 8402 | 0.042010 |

Entre os `191598` alertas do banco, a latência mediana foi `-2.0` cadências em relação a t50; q05 `-13.0`, q25 `-6.0`, q75 `3.0` e q95 `20.0`.

Gatilhos antes do onset continuaram sendo misses e foram raros.

## 8. Falso alerta

O limiar do banco foi calibrado diretamente sobre o máximo conjunto de 396 hipóteses por curva.

Os dois métodos controlaram FPR em 10/10 holdouts, sem violação extrema.

| Método | Família | Taxa agregada | Maior limite superior unilateral 95% |
|---|---|---:|---:|
| `rolling_exact_shape_latency4` | `quiet` | 0.003020 | 0.006277 |
| `rolling_exact_shape_latency4` | `shared_bump` | 0.003680 | 0.006744 |
| `rolling_exact_shape_latency4` | `shared_oscillation` | 0.003480 | 0.006744 |
| `rolling_exact_shape_latency4` | `shared_ramp` | 0.005440 | 0.009497 |
| `rolling_exact_shape_latency4` | `shared_step` | 0.004640 | 0.007900 |
| `rolling_four_shape_bank_latency4` | `quiet` | 0.002800 | 0.005807 |
| `rolling_four_shape_bank_latency4` | `shared_bump` | 0.003700 | 0.006976 |
| `rolling_four_shape_bank_latency4` | `shared_oscillation` | 0.003480 | 0.006511 |
| `rolling_four_shape_bank_latency4` | `shared_ramp` | 0.005480 | 0.009724 |
| `rolling_four_shape_bank_latency4` | `shared_step` | 0.004860 | 0.008129 |

## 9. Detecções pareadas

- nenhum método: `47388`;
- somente banco: `729`;
- somente controle: `1201`;
- ambos: `150682`.

## 10. Previsão

- controle na faixa: `CONFIRMADO`;
- banco entre 66% e 75%: `REFUTADO`;
- diferença na faixa: `CONFIRMADA`;
- controle válido: `CONFIRMADO`;
- FPR robusto: `CONFIRMADO`;
- limiar entre 7,2 e 8,6: `REFUTADO`;
- 3–8 passes: `REFUTADOS`;
- acurácia entre 45% e 75%: `REFUTADA`;
- veredito inconclusivo previsto: `REFUTADO`.

Previsão integralmente confirmada: `False`.

A detecção foi muito mais robusta que o previsto, enquanto a capacidade de identificar a forma foi muito pior.

## 11. Conclusão permitida

> Dentro do modelo sintético atual, sob duração e parâmetro latente exatos, o rótulo discreto da forma não é necessário para a detecção. O banco causal de quatro formas alcançou recall de 75,71%, limite inferior agregado de 75,54%, FPR robusto e aprovação em 10/10 holdouts.

Também é necessário afirmar:

> A forma selecionada no primeiro alerta não é uma classificação confiável. A acurácia foi de 28,96%, com 0/10 holdouts aprovados no gate de identificação.

Portanto, o banco deve ser interpretado como um mecanismo de detecção marginalizado sobre formas, não como classificador físico da morfologia.

## 12. Próximo passo correto

O próximo oráculo é a duração exata.

Uma remoção completa exigiria considerar todos os 37 valores inteiros de duração entre 24 e 60, produzindo:

\[
99\text{ endpoints}\times4\text{ formas}\times37\text{ durações}
=14\,652\text{ hipóteses por curva}.

Antes dessa execução pesada, o M37 deve ser pré-registrado como banco completo de duração, não como uma grade escolhida depois dos dados. O parâmetro latente permanecerá exato. O máximo negativo deverá incorporar conjuntamente endpoint, forma e duração.