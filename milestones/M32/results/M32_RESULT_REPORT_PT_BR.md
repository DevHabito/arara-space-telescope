# ARARA From Zero — Relatório do M32 Split-Onset Feeding Confirmed Reference Projection

**Estado:** concluído  
**Natureza:** retirada prospectiva do onset-oráculo  
**Endpoint, forma e duração:** ainda exatos  
**Calibração:** 50.000 negativos por família  
**Holdouts:** 10/10  
**Veredito:** `PASS_DETECTION_ONSET_UNRELIABLE`  

## 1. Resultado principal

O downstream confirmado do M31 continuou operacional quando o template passou a usar o onset estimado no bloco causal anterior.

Entretanto, o instante estimado não foi localizado com precisão confiável.

| Método | Limiar | Família determinante | Recall | Limite inferior unilateral 95% | Limite superior unilateral 95% | Passes | FPR |
|---|---:|---|---:|---:|---:|---:|---:|
| `exact_reference_projected8` | 4.088747 | `shared_step` | 0.795285 | 0.793840 | 0.796730 | 10/10 | 10/10 |
| `split_onset_reference_projected8` | 4.280668 | `shared_step` | 0.765470 | 0.763825 | 0.767155 | 10/10 | 10/10 |

O controle exato foi válido e repetiu o M31. O candidato estimado passou o contrato em 10/10 holdouts.

## 2. Custo de retirar o onset exato

- recall exato: `0.795285`;
- recall estimado: `0.765470`;
- diferença candidato−exato: `-0.029815`;
- limite inferior unilateral de 95%: `-0.030710`;
- limite superior unilateral de 95%: `-0.028955`.

A perda foi de aproximadamente 2,98 pontos percentuais, muito menor que a faixa pré-registrada de 10–35 pontos.

## 3. Resultado por holdout

| Holdout | Exato | Estimado | Diferença | Limite inferior estimado | Estratos | Lotes | Onset correto entre alertas | Passou detecção |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | 0.794750 | 0.764150 | -0.030600 | 0.759950 | 8/8 | 20/20 | 0.250736 | SIM |
| 1 | 0.797250 | 0.768550 | -0.028700 | 0.764350 | 8/8 | 20/20 | 0.246503 | SIM |
| 2 | 0.793350 | 0.763500 | -0.029850 | 0.759350 | 8/8 | 20/20 | 0.254879 | SIM |
| 3 | 0.794650 | 0.765650 | -0.029000 | 0.761400 | 8/8 | 20/20 | 0.258538 | SIM |
| 4 | 0.794850 | 0.766150 | -0.028700 | 0.761900 | 8/8 | 20/20 | 0.253018 | SIM |
| 5 | 0.796150 | 0.767850 | -0.028300 | 0.763600 | 8/8 | 20/20 | 0.252133 | SIM |
| 6 | 0.794500 | 0.762600 | -0.031900 | 0.758400 | 7/8 | 20/20 | 0.253409 | SIM |
| 7 | 0.797250 | 0.766300 | -0.030950 | 0.762050 | 8/8 | 20/20 | 0.253360 | SIM |
| 8 | 0.794900 | 0.763900 | -0.031000 | 0.759800 | 8/8 | 20/20 | 0.251931 | SIM |
| 9 | 0.795200 | 0.766050 | -0.029150 | 0.761900 | 8/8 | 20/20 | 0.248352 | SIM |

## 4. Localização do onset

- alertas candidatos: `153094`;
- alertas dentro de [-2,+1]: `38623`;
- acurácia entre alertas: `0.252283`;
- limite inferior unilateral de 95%: `0.250457`;
- limite superior unilateral de 95%: `0.254115`;
- acurácia entre todos os positivos: `0.248105`;
- holdouts que passaram localização: `0/10`;
- estimativas precoces demais entre alertas: `38734`;
- estimativas tardias demais entre alertas: `75737`.

A localização falhou de forma clara:

\[
A_{\rm onset}=25{,}23\% \ll 90\%.
\]

Portanto, o timestamp produzido pela dobradiça não pode ser tratado como uma estimativa física confiável do início do evento.

## 5. Resultado por forma e contexto

| Estrato | Exato | Estimado | Energia exata média | Energia deslocada média |
|---|---:|---:|---:|---:|
| `exponential__clean` | 0.991160 | 0.988920 | 0.788783 | 0.789152 |
| `exponential__concurrent` | 0.587360 | 0.542760 | 0.220464 | 0.218585 |
| `linear__clean` | 0.993320 | 0.991440 | 0.789116 | 0.789065 |
| `linear__concurrent` | 0.574360 | 0.542040 | 0.197339 | 0.196436 |
| `logistic__clean` | 0.986520 | 0.976280 | 0.794482 | 0.795318 |
| `logistic__concurrent` | 0.651800 | 0.560880 | 0.249665 | 0.245773 |
| `power_law__clean` | 0.991080 | 0.988360 | 0.787910 | 0.790317 |
| `power_law__concurrent` | 0.586680 | 0.533080 | 0.222265 | 0.232610 |

## 6. Detecções pareadas

- nenhum método: `40814`;
- somente onset estimado: `129`;
- somente onset exato: `6092`;
- ambos: `152965`.

A maior parte das detecções foi compartilhada pelos dois métodos.

## 7. Falso alerta

Os dois métodos controlaram o FPR em 10/10 holdouts, sem violação extrema.

| Método | Família | Taxa agregada | Maior limite superior unilateral 95% |
|---|---|---:|---:|
| `exact_reference_projected8` | `quiet` | 0.002480 | 0.005096 |
| `exact_reference_projected8` | `shared_bump` | 0.003620 | 0.006976 |
| `exact_reference_projected8` | `shared_oscillation` | 0.002440 | 0.005334 |
| `exact_reference_projected8` | `shared_ramp` | 0.005540 | 0.009950 |
| `exact_reference_projected8` | `shared_step` | 0.004840 | 0.009270 |
| `split_onset_reference_projected8` | `quiet` | 0.001880 | 0.004856 |
| `split_onset_reference_projected8` | `shared_bump` | 0.002540 | 0.005334 |
| `split_onset_reference_projected8` | `shared_oscillation` | 0.001800 | 0.003886 |
| `split_onset_reference_projected8` | `shared_ramp` | 0.004160 | 0.008358 |
| `split_onset_reference_projected8` | `shared_step` | 0.004680 | 0.008358 |

## 8. Previsão

- controle exato na faixa: `CONFIRMADO`;
- candidato entre 45% e 70%: `REFUTADO`;
- perda entre 10 e 35 pontos: `REFUTADA`;
- controle válido: `CONFIRMADO`;
- FPR robusto: `CONFIRMADO`;
- acurácia de onset na faixa: `CONFIRMADA`;
- falha de localização: `CONFIRMADA`;
- passes de detecção previstos: `REFUTADOS`;
- veredito inconclusivo previsto: `REFUTADO`.

Previsão integralmente confirmada: `False`.

O resultado de detecção foi muito melhor que o previsto, enquanto a previsão de baixa precisão temporal foi confirmada.

## 9. Conclusão permitida

> No modelo sintético atual, com endpoint t50, forma e duração exatos, o downstream reference-projected8 mantém recall de 76,55%, FPR robusto e 10/10 holdouts aprovados ao receber o onset causal estimado. Porém, somente 25,23% dos alertas localizam o onset dentro de [-2,+1].

Isso permite afirmar:

- o onset exato não é necessário para a detecção sob os demais oráculos;
- o estimador hinge não fornece um timestamp de onset confiável.

Não permite afirmar que o ARARA já possua onset autônomo fisicamente válido.

## 10. Controle obrigatório antes de retirar outro oráculo

O resultado é surpreendente: erros temporais grandes custaram apenas cerca de três pontos de recall.

Antes de avançar para endpoint autônomo, é necessário testar se o estimador hinge realmente acrescenta informação específica da curva.

O M33 deve comparar prospectivamente, nas mesmas curvas:

- onset hinge;
- os mesmos onsets hinge permutados entre curvas do mesmo estrato ou família.

A permutação preserva a distribuição marginal dos onsets, mas destrói a associação curva–estimativa.

Se o onset permutado tiver desempenho semelhante, o downstream é simplesmente pouco sensível ao onset e o sucesso do M32 não valida o estimador. Se o hinge superar claramente a permutação, existe informação temporal útil apesar da baixa precisão absoluta.