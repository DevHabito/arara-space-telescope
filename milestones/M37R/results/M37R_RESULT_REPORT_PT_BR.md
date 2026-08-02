# ARARA From Zero — Relatório do M37R Validity-First Pooled Calibration Replication

**Estado:** concluído  
**Calibração:** 4 blocos independentes × 50.000 negativos por família  
**Calibração agrupada:** 200.000 por família; 1.000.000 no total  
**Banco candidato:** 37 durações × 4 formas × 99 endpoints = 14.652 hipóteses por curva  
**Holdouts:** 10/10  
**Veredito:** `PASS_M37R_DETECTION_DURATION_UNRELIABLE`  

## 1. Resultado principal

O controle de duração exata foi válido em 10/10 holdouts. Portanto, ao contrário do M37, o M37R é confirmatoriamente interpretável.

O banco completo de duração passou em 8/10 holdouts, exatamente o mínimo pré-registrado.

\[
\boxed{\text{PASS\_M37R\_DETECTION\_DURATION\_UNRELIABLE}}.
\]

## 2. Resultados agregados

| Método | Limiar | Família determinante | Recall | Limite inferior unilateral 95% | Limite superior unilateral 95% | Passes | FPR |
|---|---:|---|---:|---:|---:|---:|---:|
| `rolling_four_shape_exact_duration_latency4` | 7.094576 | `shared_step` | 0.755310 | 0.753575 | 0.757040 | 10/10 | 10/10 |
| `rolling_four_shape_full_duration_bank_latency4` | 7.323737 | `shared_step` | 0.746855 | 0.745260 | 0.748475 | 8/10 | 10/10 |

Os limites inferior e superior são unilaterais de 95%; apresentados juntos, formam intervalo central de 90%.

## 3. Efeito da calibração agrupada

- limiar agrupado do controle: `7.094576`;
- limiar agrupado do banco: `7.323737`;

| Método | Menor limiar de bloco | Maior limiar de bloco | Amplitude entre blocos | Limiar agrupado |
|---|---:|---:|---:|---:|
| `rolling_four_shape_exact_duration_latency4` | 7.033789 | 7.206356 | 0.172566 | 7.094576 |
| `rolling_four_shape_full_duration_bank_latency4` | 7.250729 | 7.424101 | 0.173372 | 7.323737 |

Os quatro blocos não foram usados como votação. Todas as 200.000 curvas por família foram concatenadas antes da escolha do limiar.

A amplitude de aproximadamente 0,17 entre limiares de blocos confirma que uma única calibração de 50.000 podia deslocar materialmente um detector cujos estratos concurrent estavam próximos da fronteira.

## 4. Custo de retirar a duração exata

- controle: `0.755310`;
- banco completo: `0.746855`;
- diferença banco−controle: `-0.008455`;
- limite inferior unilateral de 95%: `-0.009045`;
- limite superior unilateral de 95%: `-0.007875`.

A perda foi de aproximadamente 0,846 ponto percentual.

## 5. Resultado por holdout

| Holdout | Controle | Banco completo | Diferença | Estratos controle | Estratos banco | Lotes controle | Lotes banco | Controle passou | Banco passou |
|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 0 | 0.751700 | 0.744350 | -0.007350 | 6/8 | 5/8 | 20/20 | 20/20 | SIM | NÃO |
| 1 | 0.753100 | 0.745650 | -0.007450 | 6/8 | 6/8 | 20/20 | 20/20 | SIM | SIM |
| 2 | 0.758050 | 0.748700 | -0.009350 | 7/8 | 6/8 | 20/20 | 20/20 | SIM | SIM |
| 3 | 0.754050 | 0.745100 | -0.008950 | 6/8 | 6/8 | 20/20 | 20/20 | SIM | SIM |
| 4 | 0.756500 | 0.748550 | -0.007950 | 6/8 | 6/8 | 20/20 | 20/20 | SIM | SIM |
| 5 | 0.753500 | 0.744800 | -0.008700 | 6/8 | 5/8 | 20/20 | 20/20 | SIM | NÃO |
| 6 | 0.754500 | 0.746500 | -0.008000 | 7/8 | 6/8 | 20/20 | 20/20 | SIM | SIM |
| 7 | 0.756250 | 0.746650 | -0.009600 | 7/8 | 6/8 | 20/20 | 20/20 | SIM | SIM |
| 8 | 0.757950 | 0.749900 | -0.008050 | 7/8 | 6/8 | 20/20 | 20/20 | SIM | SIM |
| 9 | 0.757500 | 0.748350 | -0.009150 | 7/8 | 6/8 | 20/20 | 20/20 | SIM | SIM |

Os holdouts 0 e 5 foram os únicos reprovados pelo banco. Ambos tiveram recall global, vinte lotes e FPR aprovados, mas somente 5/8 estratos satisfizeram o gate inferior de 50%. Nenhum foi substituído.

## 6. Resultado agregado por estrato

| Estrato | Controle | Banco completo |
|---|---:|---:|
| `exponential__clean` | 0.987880 | 0.985960 |
| `exponential__concurrent` | 0.533600 | 0.524640 |
| `linear__clean` | 0.983880 | 0.980960 |
| `linear__concurrent` | 0.495920 | 0.477080 |
| `logistic__clean` | 0.987080 | 0.985480 |
| `logistic__concurrent` | 0.549440 | 0.530320 |
| `power_law__clean` | 0.987200 | 0.985200 |
| `power_law__concurrent` | 0.517480 | 0.505200 |

Os quatro contextos clean permaneceram próximos de 98%–99%. O `linear__concurrent` ficou em 47,71% no banco e foi o estrato mais difícil. O passe agregado não significa que cada estrato individual superou 50% na soma dos holdouts; o contrato foi definido por limites dentro de cada holdout e exigia 6/8.

## 7. Identificação da duração

- detecções primárias: `149371`;
- duração exata correta: `3821`;
- acurácia exata: `0.025581`;
- limite inferior unilateral exato: `0.024912`;
- duração dentro de ±2: `17458`;
- acurácia dentro de ±2: `0.116877`;
- limite inferior unilateral ±2: `0.115512`;
- limite superior unilateral ±2: `0.118253`;
- holdouts aprovados no gate de identificação: `0/10`;
- erro mediano: `-4.0` cadências;
- erro absoluto mediano: `12.0` cadências.

A duração vencedora não é uma estimativa física confiável. O banco deve ser interpretado como marginalização sobre duração para detectar o evento.

A forma vencedora coincidiu com a forma verdadeira em `0.314385` das detecções primárias. Isso permanece diagnóstico e não reverte a conclusão do M36 sobre identificação morfológica fraca.

## 8. Temporalidade

| Categoria | Contagem | Fração |
|---|---:|---:|
| `success_onset_through_t50_plus4` | 149371 | 0.746855 |
| `early_before_onset` | 105 | 0.000525 |
| `late_after_t50_plus4` | 41168 | 0.205840 |
| `no_alert` | 9356 | 0.046780 |

Entre os `190644` alertas do banco, a latência mediana foi `-2.0` cadências em relação a t50; q05 `-12.0`, q25 `-6.0`, q75 `3.0` e q95 `20.0`.

Gatilhos anteriores ao onset verdadeiro continuaram sendo misses.

## 9. Falso alerta

O limiar do candidato foi calibrado sobre o máximo das 14.652 hipóteses por curva.

Os dois métodos controlaram FPR em 10/10 holdouts, sem violação extrema.

| Método | Família | Taxa agregada | Maior limite superior unilateral 95% |
|---|---|---:|---:|
| `rolling_four_shape_exact_duration_latency4` | `quiet` | 0.002780 | 0.005571 |
| `rolling_four_shape_exact_duration_latency4` | `shared_bump` | 0.003720 | 0.007900 |
| `rolling_four_shape_exact_duration_latency4` | `shared_oscillation` | 0.003960 | 0.007439 |
| `rolling_four_shape_exact_duration_latency4` | `shared_ramp` | 0.005240 | 0.009270 |
| `rolling_four_shape_exact_duration_latency4` | `shared_step` | 0.005060 | 0.008358 |
| `rolling_four_shape_full_duration_bank_latency4` | `quiet` | 0.002460 | 0.005334 |
| `rolling_four_shape_full_duration_bank_latency4` | `shared_bump` | 0.003640 | 0.008129 |
| `rolling_four_shape_full_duration_bank_latency4` | `shared_oscillation` | 0.003500 | 0.006511 |
| `rolling_four_shape_full_duration_bank_latency4` | `shared_ramp` | 0.005100 | 0.009043 |
| `rolling_four_shape_full_duration_bank_latency4` | `shared_step` | 0.005080 | 0.008587 |

## 10. Detecções pareadas

- nenhum método: `48481`;
- somente banco completo: `457`;
- somente controle: `2148`;
- ambos: `148914`.

## 11. Relação M36–M37–M37R

- M36, controle equivalente: limiar `7.105932`, recall `0.757055`, `10/10`;
- M37, controle: limiar `7.280584`, recall `0.744795`, `1/10`, inválido;
- M37R, controle: limiar `7.094576`, recall `0.755310`, `10/10`, válido.

O M37 continua inválido. O M37R não reutilizou curvas, seeds ou limiares do M36/M37.

## 12. Previsão

- limiar do controle na faixa: `REFUTADO`;
- limiar do banco na faixa: `REFUTADO`;
- recall do controle na faixa: `CONFIRMADO`;
- recall do banco na faixa: `CONFIRMADO`;
- diferença na faixa: `CONFIRMADA`;
- passes do controle na faixa: `CONFIRMADOS`;
- passes do banco na faixa: `CONFIRMADOS`;
- FPR robusto: `CONFIRMADO`;
- identificação abaixo do gate: `CONFIRMADA`;
- veredito inconclusivo previsto: `REFUTADO`.

Previsão integralmente confirmada: `False`.

Os limiares agrupados ficaram abaixo das faixas previstas, e o candidato passou em vez de ficar inconclusivo.

## 13. Conclusão permitida

> Dentro do modelo sintético atual, mantendo o parâmetro latente contínuo exato, a duração verdadeira não é necessária para detectar o evento. O banco completo de 37 durações, quatro formas e 99 endpoints alcançou recall de 74,69%, limite inferior agregado de 74,53%, FPR robusto e aprovação em 8/10 holdouts.

Também é obrigatório afirmar:

> A duração selecionada não é uma estimativa confiável. A acurácia foi de 2,56% para o valor exato e 11,69% dentro de ±2 cadências, com 0/10 holdouts aprovados na identificação.

## 14. Limites

O M37R ainda não demonstra:

- autonomia do parâmetro latente contínuo u;
- funcionamento fora das quatro famílias sintéticas;
- conversão física da cadência;
- validade em dados astronômicos reais;
- desempenho instrumental ou de missão.

## 15. Próximo passo correto

O próximo oráculo é o parâmetro latente contínuo u. Não é rigoroso escolher arbitrariamente uma grade depois de olhar a detecção.

O M38A deve ser um teste estrutural sem outcomes de detecção:

1. congelar uma perda máxima admissível de SNR por mismatch de template;
2. calcular, para todas as formas, durações e geometrias temporais, a correlação normalizada entre cada u contínuo e o ponto mais próximo de uma grade candidata;
3. escolher a menor grade que satisfaça o contrato de aproximação no pior caso;
4. congelar essa grade antes de qualquer calibração negativa ou holdout.

Somente depois, o M38B poderá calibrar conjuntamente endpoint × forma × duração × grade de u.