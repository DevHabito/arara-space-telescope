# ARARA From Zero — Relatório do M37 Full Duration × Shape Rolling Bank

**Estado:** execução concluída  
**Banco candidato:** 37 durações × 4 formas × 99 endpoints = 14.652 hipóteses por curva  
**Calibração:** 50.000 negativos por família  
**Holdouts:** 10/10  
**Veredito congelado:** `INVALID_M37_EXACT_DURATION_CONTROL`  

## 1. Resultado principal

O M37 não autoriza classificar o banco completo de duração como passe, falha forte ou resultado inconclusivo, porque o controle de duração exata falhou o gate de validade.

O pré-registro exigia pelo menos 8/10 holdouts aprovados no controle. Foram observados:

\[
1/10.
\]

Logo:

\[
\boxed{\text{INVALID\_M37\_EXACT\_DURATION\_CONTROL}}.
\]

Essa regra tem precedência sobre os números do candidato.

## 2. Resultados agregados

| Método | Limiar | Família determinante | Recall | Limite inferior unilateral 95% | Limite superior unilateral 95% | Passes | FPR |
|---|---:|---|---:|---:|---:|---:|---:|
| `rolling_four_shape_exact_duration_latency4` | 7.280584 | `shared_step` | 0.744795 | 0.743040 | 0.746560 | 1/10 | 10/10 |
| `rolling_four_shape_full_duration_bank_latency4` | 7.537209 | `shared_step` | 0.734580 | 0.732895 | 0.736320 | 0/10 | 10/10 |

O recall agregado de ambos os métodos ficou acima de 60%, todos os lotes foram estáveis e o falso alerta foi controlado. A invalidação veio do gate de cobertura por estrato do próprio controle.

## 3. Controle inválido

- recall agregado: `0.744795`;
- limite inferior unilateral de 95%: `0.743040`;
- holdouts aprovados: `1/10`;
- FPR aprovado: `10/10`.

O controle teve apenas 4–6 estratos bons por holdout. Somente o holdout 0 atingiu o mínimo de 6/8.

## 4. Auditoria contra bug de implementação

A invalidação não foi simplesmente aceita sem auditoria.

- testes congelados: `8/8` aprovados;
- hashes pré-calibração e pré-holdout: `53/53` coincidentes;
- controle M37 comparado diretamente ao banco M36 nas mesmas curvas;
- maior diferença absoluta de score: `2,3e-13`;
- divergências na forma vencedora: `0`.

Portanto, não foi encontrada evidência de erro na vetorização do controle.

## 5. Comparação M36–M37

- limiar M36 do banco de quatro formas: `7.105932`;
- limiar M37 do controle equivalente: `7.280584`;
- aumento do limiar: `0.174652`;
- recall M36: `0.757055`;
- recall do controle M37: `0.744795`;
- diferença: `-0.012260`;
- passes M36: `10/10`;
- passes do controle M37: `1/10`.

O diagnóstico pós-hoc de blocos de calibração mostra sensibilidade relevante da cauda de 0,5%, mas não constitui intervalo de confiança e não permite substituir o limiar congelado.

## 6. Candidato de duração completa — somente descrição

Como o controle é inválido, os números abaixo não são um veredito científico sobre a retirada da duração:

- recall: `0.734580`;
- limite inferior unilateral de 95%: `0.732895`;
- passes: `0/10`;
- FPR: `10/10`;
- AUROC médio: `0.999032`;
- AP média: `0.998818`.

A comparação pareada descritiva foi:

\[
\Delta R=R_{\rm full}-R_{\rm control}=-0.010215.
\]

Limites unilaterais de 95%:

\[
-0.010790\leq\Delta R\leq-0.009650.
\]

A perda descritiva foi de aproximadamente 1,02 ponto percentual, mas não pode ser promovida como evidência confirmatória.

## 7. Resultado por holdout

| Holdout | Controle | Banco completo | Diferença | Estratos controle | Estratos banco | Lotes controle | Lotes banco | Controle passou | Banco passou |
|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 0 | 0.747700 | 0.736500 | -0.011200 | 6/8 | 5/8 | 20/20 | 20/20 | SIM | NÃO |
| 1 | 0.748450 | 0.738400 | -0.010050 | 5/8 | 5/8 | 20/20 | 20/20 | NÃO | NÃO |
| 2 | 0.741250 | 0.731200 | -0.010050 | 4/8 | 4/8 | 20/20 | 20/20 | NÃO | NÃO |
| 3 | 0.743900 | 0.734150 | -0.009750 | 5/8 | 4/8 | 20/20 | 20/20 | NÃO | NÃO |
| 4 | 0.743450 | 0.734800 | -0.008650 | 5/8 | 4/8 | 20/20 | 20/20 | NÃO | NÃO |
| 5 | 0.742750 | 0.732400 | -0.010350 | 5/8 | 4/8 | 20/20 | 20/20 | NÃO | NÃO |
| 6 | 0.743100 | 0.733050 | -0.010050 | 5/8 | 4/8 | 20/20 | 20/20 | NÃO | NÃO |
| 7 | 0.746350 | 0.735600 | -0.010750 | 5/8 | 4/8 | 20/20 | 20/20 | NÃO | NÃO |
| 8 | 0.745700 | 0.734450 | -0.011250 | 5/8 | 5/8 | 20/20 | 20/20 | NÃO | NÃO |
| 9 | 0.745300 | 0.735250 | -0.010050 | 5/8 | 5/8 | 20/20 | 20/20 | NÃO | NÃO |

## 8. Resultado agregado por estrato

| Estrato | Controle | Banco completo |
|---|---:|---:|
| `exponential__clean` | 0.986680 | 0.983520 |
| `exponential__concurrent` | 0.510640 | 0.500320 |
| `linear__clean` | 0.980640 | 0.975840 |
| `linear__concurrent` | 0.474640 | 0.454360 |
| `logistic__clean` | 0.985240 | 0.982320 |
| `logistic__concurrent` | 0.527480 | 0.506760 |
| `power_law__clean` | 0.985680 | 0.981800 |
| `power_law__concurrent` | 0.507360 | 0.491720 |

Os quatro contextos clean permaneceram próximos de 98%. Os contextos concurrent ficaram próximos da fronteira, e o `linear__concurrent` ficou abaixo de 50% até no controle.

## 9. Identificação da duração — diagnóstico

- detecções primárias do banco: `146916`;
- duração exata correta: `3796`;
- acurácia exata: `0.025838`;
- limite inferior unilateral exato: `0.025161`;
- duração dentro de ±2: `17057`;
- acurácia dentro de ±2: `0.116100`;
- limite inferior unilateral ±2: `0.114728`;
- holdouts aprovados no gate de identificação: `0/10`;
- erro mediano: `-4.0` cadências;
- erro absoluto mediano: `12.0` cadências.

A duração escolhida é claramente inadequada para interpretação física. Esse diagnóstico, porém, também permanece subordinado à invalidação do controle.

## 10. Temporalidade do candidato

| Categoria | Contagem | Fração |
|---|---:|---:|
| `success_onset_through_t50_plus4` | 146916 | 0.734580 |
| `early_before_onset` | 82 | 0.000410 |
| `late_after_t50_plus4` | 42330 | 0.211650 |
| `no_alert` | 10672 | 0.053360 |

Entre os `189328` alertas do banco, a latência mediana foi `-2.0` cadências em relação a t50; q05 `-12.0`, q25 `-5.0`, q75 `4.0` e q95 `21.0`.

## 11. Falso alerta

O candidato foi calibrado sobre o máximo conjunto das 14.652 hipóteses por curva.

Os dois métodos controlaram FPR em 10/10 holdouts, sem violação extrema.

| Método | Família | Taxa agregada | Maior limite superior unilateral 95% |
|---|---|---:|---:|
| `rolling_four_shape_exact_duration_latency4` | `quiet` | 0.002320 | 0.004616 |
| `rolling_four_shape_exact_duration_latency4` | `shared_bump` | 0.003760 | 0.006744 |
| `rolling_four_shape_exact_duration_latency4` | `shared_oscillation` | 0.003120 | 0.006042 |
| `rolling_four_shape_exact_duration_latency4` | `shared_ramp` | 0.003920 | 0.006976 |
| `rolling_four_shape_exact_duration_latency4` | `shared_step` | 0.004300 | 0.008129 |
| `rolling_four_shape_full_duration_bank_latency4` | `quiet` | 0.001980 | 0.004131 |
| `rolling_four_shape_full_duration_bank_latency4` | `shared_bump` | 0.003520 | 0.006042 |
| `rolling_four_shape_full_duration_bank_latency4` | `shared_oscillation` | 0.002720 | 0.005334 |
| `rolling_four_shape_full_duration_bank_latency4` | `shared_ramp` | 0.003880 | 0.006976 |
| `rolling_four_shape_full_duration_bank_latency4` | `shared_step` | 0.004320 | 0.008358 |

## 12. Detecções pareadas

- nenhum método: `50625`;
- somente banco completo: `416`;
- somente controle: `2459`;
- ambos: `146500`.

## 13. Previsão

- recall do controle na faixa: `CONFIRMADO`;
- recall do banco na faixa: `CONFIRMADO`;
- diferença na faixa: `CONFIRMADA`;
- controle válido: `REFUTADO`;
- FPR robusto: `CONFIRMADO`;
- limiar do banco na faixa: `CONFIRMADO`;
- 8–10 passes do banco: `REFUTADOS`;
- acurácia exata de duração na faixa: `REFUTADA`;
- acurácia ±2 na faixa: `REFUTADA`;
- veredito previsto: `REFUTADO`.

Previsão integralmente confirmada: `False`.

## 14. Conclusão rigorosa

> O M37 foi executado integralmente, mas é confirmatoriamente inválido porque o controle de duração exata passou somente 1/10 holdouts, abaixo do mínimo pré-registrado de 8/10.

> A equivalência numérica com o M36 foi verificada, portanto não há evidência de que a invalidação seja um artefato da implementação vetorizada.

> Os resultados do banco completo — recall descritivo de 73,46%, FPR robusto e perda pareada de 1,02 ponto — são informativos para diagnóstico, mas não demonstram nem refutam a retirada do oráculo de duração.

## 15. Próximo passo correto

Não é metodologicamente correto avançar para outro oráculo.

O próximo teste deve ser um `M37R` independente, mantendo:

- o banco completo de 14.652 hipóteses;
- os mesmos gates positivos e de FPR;
- o mesmo contrato de latência t50+4;
- novas seeds e novos holdouts.

A única mudança justificável é estabilizar prospectivamente a calibração da cauda, por exemplo com quatro blocos independentes de 50.000 negativos por família, combinados antes de congelar os limiares. Isso deverá ser pré-registrado como novo protocolo e não poderá reutilizar o limiar M36 ou M37.