# ARARA From Zero — Relatório do M34 Rolling Causal Endpoint Search

**Estado:** concluído  
**Grade rolling:** 81–179, 99 endpoints  
**Calibração:** 50.000 negativos por família, FPR por curva após toda a busca  
**Holdouts:** 10/10  
**Veredito:** `STRONG_FAIL_ROLLING_CAUSAL_ENDPOINT`  

## 1. Pergunta

O pipeline hinge + reference projection continua operacional quando o endpoint exato t50 é substituído pelo primeiro cruzamento numa busca causal completa?

O teste usou o primeiro cruzamento, não o argmax. Nos negativos, o limiar foi calibrado sobre o máximo dos 99 endpoints, incorporando integralmente o look-elsewhere.

## 2. Resultado agregado primário

| Método | Limiar | Família determinante | Recall | Limite inferior unilateral 95% | Limite superior unilateral 95% | Passes | FPR |
|---|---:|---|---:|---:|---:|---:|---:|
| `hinge_exact_t50` | 4.179630 | `shared_ramp` | 0.772385 | 0.770770 | 0.774115 | 10/10 | 10/10 |
| `rolling_hinge_first_crossing` | 6.945625 | `shared_ramp` | 0.630655 | 0.628535 | 0.632870 | 0/10 | 10/10 |

O controle exato foi válido. O rolling alcançou recall global acima de 60%, mas falhou o contrato em 10/10 holdouts porque somente quatro dos oito estratos satisfizeram o gate de cobertura.

Pela regra congelada de no máximo 2/10 passes, o veredito é falha forte.

## 3. Custo do endpoint autônomo estrito

- controle t50: `0.772385`;
- rolling até t50: `0.630655`;
- diferença rolling−controle: `-0.141730`;
- limite inferior unilateral 95%: `-0.143790`;
- limite superior unilateral 95%: `-0.139615`.

A perda foi de aproximadamente 14,17 pontos percentuais.

## 4. Resultado por holdout

| Holdout | Controle t50 | Rolling até t50 | Rolling até t50+4 (diagnóstico) | Diferença | Estratos bons | Lotes bons | Passou |
|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | 0.770300 | 0.631200 | 0.757650 | -0.139100 | 4/8 | 20/20 | NÃO |
| 1 | 0.774100 | 0.636700 | 0.759350 | -0.137400 | 4/8 | 20/20 | NÃO |
| 2 | 0.771500 | 0.628650 | 0.757150 | -0.142850 | 4/8 | 20/20 | NÃO |
| 3 | 0.770800 | 0.627700 | 0.754750 | -0.143100 | 4/8 | 20/20 | NÃO |
| 4 | 0.770100 | 0.634000 | 0.759350 | -0.136100 | 4/8 | 20/20 | NÃO |
| 5 | 0.777250 | 0.634050 | 0.761300 | -0.143200 | 4/8 | 20/20 | NÃO |
| 6 | 0.772550 | 0.627600 | 0.754500 | -0.144950 | 4/8 | 20/20 | NÃO |
| 7 | 0.772000 | 0.627600 | 0.753100 | -0.144400 | 4/8 | 20/20 | NÃO |
| 8 | 0.771300 | 0.627850 | 0.759800 | -0.143450 | 4/8 | 20/20 | NÃO |
| 9 | 0.773950 | 0.631200 | 0.759300 | -0.142750 | 4/8 | 20/20 | NÃO |

Todos os vinte lotes passaram em cada holdout. A falha foi de cobertura entre formas/contextos, não de instabilidade entre lotes.

## 5. Decomposição temporal dos 200.000 positivos

| Categoria do primeiro cruzamento | Contagem | Fração |
|---|---:|---:|
| `primary_on_time_onset_through_t50` | 126131 | 0.630655 |
| `late_t50_plus1_to4` | 25394 | 0.126970 |
| `late_after_t50_plus4` | 40264 | 0.201320 |
| `early_before_onset` | 102 | 0.000510 |
| `no_alert` | 8109 | 0.040545 |

O diagnóstico pré-registrado até t50+4 alcançou `0.757625` de recall.

Esse número não altera o veredito: a janela primária congelada terminava em t50. Ele serve somente para localizar o mecanismo da falha e formular um novo teste independente.

## 6. Resultado por forma e contexto

| Estrato | Controle t50 | Rolling até t50 | Rolling até t50+4 |
|---|---:|---:|---:|
| `exponential__clean` | 0.991120 | 0.929240 | 0.989920 |
| `exponential__concurrent` | 0.553560 | 0.364280 | 0.543800 |
| `linear__clean` | 0.991200 | 0.939760 | 0.985080 |
| `linear__concurrent` | 0.554840 | 0.396440 | 0.504120 |
| `logistic__clean` | 0.978640 | 0.843600 | 0.986800 |
| `logistic__concurrent` | 0.570360 | 0.296320 | 0.536560 |
| `power_law__clean` | 0.989880 | 0.925160 | 0.989160 |
| `power_law__concurrent` | 0.549480 | 0.350440 | 0.525560 |

Os quatro estratos `clean` permaneceram fortes antes de t50. Os quatro estratos `concurrent` ficaram entre aproximadamente 29,6% e 39,6%, explicando os quatro estratos bons por holdout.

Com quatro cadências adicionais, os contextos concurrent subiram para aproximadamente 50,4%–54,4%. Isso sugere atraso sistemático, mas ainda requer confirmação independente.

## 7. Latência

- `all_alerts`: n `191891`, q05 `-13.0`, q25 `-6.0`, mediana `-2.0`, q75 `3.0`, q95 `20.0` cadências em relação a t50; erro absoluto mediano do hinge no alerta `5.0`.
- `alerts_not_before_true_onset`: n `191789`, q05 `-13.0`, q25 `-6.0`, mediana `-2.0`, q75 `3.0`, q95 `20.0` cadências em relação a t50; erro absoluto mediano do hinge no alerta `5.0`.

A mediana de latência entre alertas foi -2 cadências, porque os contextos clean alertam cedo. A cauda tardia é concentrada nos contextos concurrent e é o que derruba a cobertura estratificada.

Gatilhos antes do onset verdadeiro foram raros: 102 em 200.000 positivos.

## 8. Falso alerta

O look-elsewhere elevou o limiar de aproximadamente 4,18 para 6,95.

Mesmo após 99 tentativas temporais por curva, o rolling controlou o FPR em 10/10 holdouts e não apresentou violação extrema.

| Método | Família | Taxa agregada | Maior limite superior unilateral 95% |
|---|---|---:|---:|
| `hinge_exact_t50` | `quiet` | 0.001900 | 0.005334 |
| `hinge_exact_t50` | `shared_bump` | 0.003880 | 0.006976 |
| `hinge_exact_t50` | `shared_oscillation` | 0.002260 | 0.004616 |
| `hinge_exact_t50` | `shared_ramp` | 0.004060 | 0.007208 |
| `hinge_exact_t50` | `shared_step` | 0.004660 | 0.008358 |
| `rolling_hinge_first_crossing` | `quiet` | 0.002780 | 0.007439 |
| `rolling_hinge_first_crossing` | `shared_bump` | 0.004240 | 0.007670 |
| `rolling_hinge_first_crossing` | `shared_oscillation` | 0.003640 | 0.006511 |
| `rolling_hinge_first_crossing` | `shared_ramp` | 0.005060 | 0.009270 |
| `rolling_hinge_first_crossing` | `shared_step` | 0.004980 | 0.008815 |

## 9. Ranking versus contrato temporal

- AUROC controle: `0.978786`;
- AUROC rolling: `0.999103`;
- AP controle: `0.979875`;
- AP rolling: `0.998910`.

O máximo rolling separa positivos e negativos quase perfeitamente como ranking, mas o contrato não pergunta apenas se a curva contém um evento: exige que o primeiro alerta ocorra até t50 e cubra pelo menos seis estratos.

Esse é um exemplo importante de AUROC excelente coexistindo com falha operacional temporal.

## 10. Detecções pareadas

- nenhum método: `41680`;
- somente rolling primário: `3843`;
- somente controle exato: `32189`;
- ambos: `122288`.

## 11. Previsão

- controle na faixa: `CONFIRMADO`;
- rolling entre 20% e 55%: `REFUTADO`;
- perda entre 20 e 58 pontos: `REFUTADA`;
- controle válido: `CONFIRMADO`;
- FPR robusto: `CONFIRMADO`;
- 0–3 passes rolling: `CONFIRMADO`;
- limiar entre 5,5 e 10: `CONFIRMADO`;
- veredito forte de falha: `CONFIRMADO`.

Previsão integralmente confirmada: `False`.

O veredito previsto foi confirmado, mas o recall rolling foi muito melhor e a perda muito menor que o esperado.

## 12. Conclusão permitida

> A busca causal rolling com 99 endpoints controlou corretamente o falso alerta e alcançou recall global de 63,07% até t50. Entretanto, falhou em 10/10 holdouts porque somente os quatro contextos clean satisfizeram a cobertura estratificada; portanto, o endpoint exato ainda não foi retirado sob o contrato de latência zero.

Também é permitido afirmar:

> O fracasso é principalmente de latência nos contextos concurrent, não de ausência de informação: 12,70% adicionais dos positivos cruzaram entre t50+1 e t50+4, elevando o diagnóstico pré-registrado para 75,76%.

## 13. Próximo teste correto

O M35 deve repetir exatamente a busca rolling do M34 com nova calibração e novos holdouts, mudando apenas o contrato prospectivo de sucesso para:

\[
\tau_{\rm true}\leq e_{\rm alert}\leq t_{50}+4.
\]

Esse não será um resgate retroativo do M34. Será um novo teste independente de uma hipótese motivada pelo diagnóstico que já estava pré-registrado.

Se o M35 passar, poderemos afirmar endpoint causal autônomo com latência algorítmica limitada a quatro cadências dentro do modelo sintético. A conversão dessas cadências para tempo físico continuará pendente.