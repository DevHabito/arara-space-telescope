# ARARA From Zero — Relatório do M35 Independent Rolling Endpoint Latency-4 Test

**Estado:** concluído  
**Natureza:** teste prospectivo independente da hipótese t50+4  
**Grade rolling:** 81–179, 99 endpoints  
**Calibração:** 50.000 negativos por família, FPR por curva após toda a busca  
**Holdouts:** 10/10  
**Veredito:** `PASS_ROLLING_ENDPOINT_LATENCY4`  

## 1. Pergunta

A mesma busca rolling que falhou no M34 sob latência zero satisfaz o contrato quando o primeiro cruzamento pode ocorrer até quatro cadências depois de t50?

Nenhuma equação, endpoint candidato, nuisance, limiar-alvo ou gate foi alterado. Somente a definição prospectiva de sucesso positivo mudou para:

\[
\tau_{\rm true}\leq e_{\rm alert}\leq t_{50}+4.
\]

## 2. Resultado agregado

| Método | Limiar | Família determinante | Recall | Limite inferior unilateral 95% | Limite superior unilateral 95% | Passes | FPR |
|---|---:|---|---:|---:|---:|---:|---:|
| `hinge_exact_t50` | 4.235359 | `shared_step` | 0.770085 | 0.768250 | 0.771865 | 10/10 | 10/10 |
| `rolling_hinge_first_crossing` | 7.002527 | `shared_step` | 0.754990 | 0.753075 | 0.757020 | 9/10 | 10/10 |

O controle exato foi válido.

O rolling passou o contrato agregado em:

\[
9/10\text{ holdouts}.
\]

O requisito congelado era pelo menos 8/10.

## 3. Custo em relação ao endpoint exato

- controle no t50 exato: `0.770085`;
- rolling até t50+4: `0.754990`;
- diferença rolling−controle: `-0.015095`;
- limite inferior unilateral de 95%: `-0.017040`;
- limite superior unilateral de 95%: `-0.013160`.

A perda foi de aproximadamente 1,51 ponto percentual.

## 4. Curva de recall versus latência

| Latência máxima após t50 | Recall |
|---:|---:|
| +0 | 0.626870 |
| +1 | 0.669350 |
| +2 | 0.702870 |
| +3 | 0.730630 |
| +4 | 0.754990 |

O ganho de permitir quatro cadências não foi aplicado ao score ou ao limiar. Ele apenas reconhece como sucesso cruzamentos prospectivos que chegam pouco depois de t50.

## 5. Resultado por holdout

| Holdout | Controle t50 | Rolling t50 | Rolling t50+1 | t50+2 | t50+3 | t50+4 | Estratos bons | Lotes bons | Passou |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | 0.772400 | 0.625900 | 0.668600 | 0.703800 | 0.730300 | 0.755750 | 6/8 | 20/20 | SIM |
| 1 | 0.769650 | 0.630500 | 0.671250 | 0.705550 | 0.730950 | 0.753850 | 7/8 | 20/20 | SIM |
| 2 | 0.767550 | 0.627550 | 0.671550 | 0.703800 | 0.732850 | 0.756500 | 7/8 | 20/20 | SIM |
| 3 | 0.769650 | 0.623150 | 0.665700 | 0.699250 | 0.727250 | 0.750400 | 5/8 | 20/20 | NÃO |
| 4 | 0.774800 | 0.629750 | 0.672250 | 0.706650 | 0.735300 | 0.760350 | 8/8 | 20/20 | SIM |
| 5 | 0.767350 | 0.627800 | 0.670200 | 0.703100 | 0.731450 | 0.754950 | 7/8 | 20/20 | SIM |
| 6 | 0.771800 | 0.626950 | 0.672050 | 0.704400 | 0.732650 | 0.758650 | 7/8 | 20/20 | SIM |
| 7 | 0.768600 | 0.626000 | 0.667050 | 0.700850 | 0.728150 | 0.753500 | 7/8 | 20/20 | SIM |
| 8 | 0.772000 | 0.628450 | 0.668500 | 0.701950 | 0.729850 | 0.752450 | 6/8 | 20/20 | SIM |
| 9 | 0.767050 | 0.622650 | 0.666350 | 0.699350 | 0.727550 | 0.753500 | 7/8 | 20/20 | SIM |

O holdout 3 foi o único reprovado. Seu recall global e os vinte lotes passaram, mas somente cinco estratos atingiram o gate inferior de 50%.

| Estrato no holdout 3 | Recall | Limite inferior unilateral 95% |
|---|---:|---:|
| `linear__clean` | 0.985200 | 0.980575 |
| `linear__concurrent` | 0.496400 | 0.479761 |
| `power_law__clean` | 0.989600 | 0.985598 |
| `power_law__concurrent` | 0.507200 | 0.490553 |
| `exponential__clean` | 0.988800 | 0.984676 |
| `exponential__concurrent` | 0.507600 | 0.490953 |
| `logistic__clean` | 0.990400 | 0.986525 |
| `logistic__concurrent` | 0.538000 | 0.521372 |

A reprovação isolada foi preservada; nenhum estrato, seed ou holdout foi substituído.

## 6. Resultado agregado por forma e contexto

| Estrato | Controle exato | Rolling até t50+4 |
|---|---:|---:|
| `exponential__clean` | 0.991400 | 0.990040 |
| `exponential__concurrent` | 0.545320 | 0.534440 |
| `linear__clean` | 0.991520 | 0.985320 |
| `linear__concurrent` | 0.552560 | 0.502200 |
| `logistic__clean` | 0.979280 | 0.988280 |
| `logistic__concurrent` | 0.566040 | 0.530760 |
| `power_law__clean` | 0.988040 | 0.987680 |
| `power_law__concurrent` | 0.546520 | 0.521200 |

Os contextos clean permaneceram próximos de 99%. Os contextos concurrent ficaram entre 50,22% e 53,44%. O estrato linear concurrent ficou próximo da fronteira, explicando a variação de 5–8 estratos bons entre holdouts.

## 7. Categorias temporais

| Categoria | Contagem | Fração |
|---|---:|---:|
| `success_onset_through_t50_plus4` | 150998 | 0.754990 |
| `late_after_t50_plus4` | 40530 | 0.202650 |
| `early_before_onset` | 93 | 0.000465 |
| `no_alert` | 8379 | 0.041895 |

Entre os `191621` alertas, a latência mediana em relação a t50 foi `-2.0` cadências; q05 `-13.0`, q25 `-6.0`, q75 `3.0` e q95 `21.0`.

Gatilhos antes do onset verdadeiro continuam sendo misses e não foram convertidos em sucessos.

## 8. Falso alerta e look-elsewhere

O limiar rolling independente foi `7.002527`, determinado por `shared_step`.

Ele foi calibrado sobre o máximo dos 99 endpoints por curva.

O rolling controlou FPR em 10/10 holdouts, sem violação extrema.

| Método | Família | Taxa agregada | Maior limite superior unilateral 95% |
|---|---|---:|---:|
| `hinge_exact_t50` | `quiet` | 0.001860 | 0.003886 |
| `hinge_exact_t50` | `shared_bump` | 0.004040 | 0.007208 |
| `hinge_exact_t50` | `shared_oscillation` | 0.002300 | 0.005571 |
| `hinge_exact_t50` | `shared_ramp` | 0.003720 | 0.006744 |
| `hinge_exact_t50` | `shared_step` | 0.004540 | 0.007900 |
| `rolling_hinge_first_crossing` | `quiet` | 0.002740 | 0.005571 |
| `rolling_hinge_first_crossing` | `shared_bump` | 0.003820 | 0.006744 |
| `rolling_hinge_first_crossing` | `shared_oscillation` | 0.003460 | 0.007208 |
| `rolling_hinge_first_crossing` | `shared_ramp` | 0.004500 | 0.007900 |
| `rolling_hinge_first_crossing` | `shared_step` | 0.004680 | 0.009043 |

## 9. Consistência M34–M35

- diagnóstico t50+4 do M34: `0.757625`;
- teste primário independente M35: `0.754990`;
- diferença M35−M34: `-0.002635`;
- limiar M34: `6.945625`;
- limiar M35: `7.002527`.

A diferença de recall foi de aproximadamente -0,26 ponto percentual. O efeito observado no diagnóstico do M34 reproduziu-se em novos dados.

O M34 continua sendo falha forte sob latência zero. O passe do M35 não altera essa classificação.

## 10. Ranking

- AUROC controle: `0.978574`;
- AUROC rolling: `0.999130`;
- AP controle: `0.979827`;
- AP rolling: `0.998941`.

## 11. Detecções pareadas

- nenhum método: `34808`;
- somente rolling t50+4: `11175`;
- somente controle exato: `14194`;
- ambos: `139823`.

## 12. Previsão

- controle na faixa: `CONFIRMADO`;
- rolling na faixa: `CONFIRMADO`;
- diferença na faixa: `CONFIRMADA`;
- controle válido: `CONFIRMADO`;
- FPR robusto: `CONFIRMADO`;
- 8–10 passes: `CONFIRMADOS`;
- limiar previsto: `CONFIRMADO`;
- veredito previsto: `CONFIRMADO`.

Previsão integralmente confirmada: `True`.

## 13. Conclusão permitida

> No modelo sintético atual, sob forma e duração exatas, a busca rolling causal com 99 endpoints dispensa o endpoint exato t50 quando se aceita latência algorítmica máxima de quatro cadências. O método alcançou recall de 75,50%, limite inferior agregado de 75,31%, FPR robusto e aprovação em 9/10 holdouts.

Isso não significa:

- que quatro cadências já tenham duração física definida;
- que o evento seja detectado sempre antes de t50;
- que forma ou duração sejam autônomas;
- que o resultado esteja validado em dados astronômicos reais.

## 14. Próximo passo correto

O próximo oráculo a retirar é a forma do template, mantendo a duração exata.

O M36 deve comparar o controle com forma exata contra um banco causal congelado das quatro formas existentes. O alerta será o primeiro endpoint em que qualquer forma ultrapassar o limiar.

A calibração deverá usar o máximo por curva sobre:

\[
99\text{ endpoints}\times4\text{ formas}=396\text{ hipóteses}.
\]

Assim, o look-elsewhere temporal e o look-elsewhere de forma serão controlados conjuntamente.