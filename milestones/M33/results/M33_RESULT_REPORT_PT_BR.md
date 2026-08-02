# ARARA From Zero — Relatório do M33 Hinge-versus-Permuted-Onset Association Control

**Estado:** concluído  
**Calibração:** 50.000 negativos por família  
**Holdouts:** 10/10  
**Permutação:** dentro do mesmo grupo e lote, sem pontos fixos  
**Veredito:** `PASS_CURVE_SPECIFIC_ONSET_INFORMATION`  

## 1. Pergunta

O hinge melhora a detecção porque contém informação específica da própria curva, ou apenas porque fornece uma distribuição plausível de onsets?

O controle permutado preservou exatamente o multiconjunto de onsets hinge em cada grupo, mas atribuiu cada onset a outra curva.

## 2. Integridade da permutação

- pontos fixos na calibração: `0`;
- pontos fixos nos holdouts positivos: `0`;
- multiconjunto de onsets preservado em todos os grupos: `SIM`;
- nenhuma mistura entre estratos, famílias ou lotes.

## 3. Resultado agregado

| Método | Limiar | Família determinante | Recall | Limite inferior unilateral 95% | Limite superior unilateral 95% | Passes | FPR |
|---|---:|---|---:|---:|---:|---:|---:|
| `exact_reference_projected8` | 4.119858 | `shared_ramp` | 0.793785 | 0.792030 | 0.795425 | 10/10 | 10/10 |
| `hinge_reference_projected8` | 4.181726 | `shared_step` | 0.774860 | 0.773190 | 0.776440 | 10/10 | 10/10 |
| `permuted_hinge_reference_projected8` | 4.223289 | `shared_step` | 0.698805 | 0.696700 | 0.700860 | 0/10 | 10/10 |

Os controles exato e hinge foram válidos. O onset permutado manteve recall global acima de 60%, mas falhou o contrato em todos os holdouts por cobertura insuficiente dos estratos.

## 4. Informação específica da curva

\[
\Delta_{\rm assoc}=0.076055.
\]

Limites unilaterais de 95%:

\[
0.074670
\leq\Delta_{\rm assoc}\leq
0.077455.
\]

O ganho foi de aproximadamente 7,61 pontos percentuais. O limite inferior de 7,47 pontos ficou muito acima da margem pré-registrada de 2 pontos.

O hinge superou o permutado por pelo menos 1,5 ponto em `10/10` holdouts.

Assim, a hipótese de equivalência operacional foi refutada.

## 5. Resultado por holdout

| Holdout | Exato | Hinge | Permutado | Hinge−permutado | Estratos hinge | Estratos permutado | Hinge passou | Permutado passou |
|---:|---:|---:|---:|---:|---:|---:|---|---|
| 0 | 0.793850 | 0.775250 | 0.697200 | 0.078050 | 8/8 | 4/8 | SIM | NÃO |
| 1 | 0.788300 | 0.769850 | 0.692250 | 0.077600 | 8/8 | 4/8 | SIM | NÃO |
| 2 | 0.796150 | 0.776750 | 0.701600 | 0.075150 | 8/8 | 5/8 | SIM | NÃO |
| 3 | 0.792500 | 0.773450 | 0.696400 | 0.077050 | 8/8 | 4/8 | SIM | NÃO |
| 4 | 0.795150 | 0.776600 | 0.697850 | 0.078750 | 8/8 | 4/8 | SIM | NÃO |
| 5 | 0.793750 | 0.775100 | 0.702150 | 0.072950 | 8/8 | 4/8 | SIM | NÃO |
| 6 | 0.794050 | 0.774900 | 0.699000 | 0.075900 | 8/8 | 4/8 | SIM | NÃO |
| 7 | 0.795250 | 0.776350 | 0.701100 | 0.075250 | 8/8 | 4/8 | SIM | NÃO |
| 8 | 0.793800 | 0.775300 | 0.700950 | 0.074350 | 8/8 | 5/8 | SIM | NÃO |
| 9 | 0.795050 | 0.775050 | 0.699550 | 0.075500 | 8/8 | 5/8 | SIM | NÃO |

## 6. Resultado por forma e contexto

| Estrato | Exato | Hinge | Permutado |
|---|---:|---:|---:|
| `exponential__clean` | 0.992040 | 0.990840 | 0.938800 |
| `exponential__concurrent` | 0.585040 | 0.563320 | 0.511240 |
| `linear__clean` | 0.993440 | 0.992840 | 0.914880 |
| `linear__concurrent` | 0.572960 | 0.560320 | 0.481600 |
| `logistic__clean` | 0.987480 | 0.979560 | 0.867320 |
| `logistic__concurrent` | 0.640720 | 0.571480 | 0.478240 |
| `power_law__clean` | 0.990760 | 0.988880 | 0.907480 |
| `power_law__concurrent` | 0.587840 | 0.551640 | 0.490880 |

O permutado preservou bom desempenho nos contextos `clean`, mas perdeu cobertura nos quatro contextos `concurrent`. Em cada holdout, apenas quatro ou cinco estratos satisfizeram o limite inferior de 50%; o contrato exige seis.

## 7. Precisão temporal

| Atribuição | Alertas | Dentro de [-2,+1] | Acurácia entre alertas | Acurácia em todos os positivos |
|---|---:|---:|---:|---:|
| Hinge da própria curva | 154972 | 39105 | 0.252336 | 0.249225 |
| Hinge permutado | 139761 | 15790 | 0.112979 | 0.100165 |

A precisão absoluta do hinge próprio continuou baixa, cerca de 25,23%. Portanto, o M33 não transforma o hinge em um timestamp físico confiável.

Mas a permutação derrubou a acurácia para aproximadamente 11,30% e reduziu substancialmente o recall. Isso demonstra que a estimativa original contém associação temporal útil com a própria curva.

## 8. Detecções pareadas

- nenhum: `43210`;
- somente hinge próprio: `17029`;
- somente permutado: `1818`;
- ambos: `137943`.

## 9. Falso alerta

Todos os três métodos controlaram o FPR em 10/10 holdouts, sem violação extrema.

| Método | Família | Taxa agregada | Maior limite superior unilateral 95% |
|---|---|---:|---:|
| `exact_reference_projected8` | `quiet` | 0.002700 | 0.005571 |
| `exact_reference_projected8` | `shared_bump` | 0.003520 | 0.006976 |
| `exact_reference_projected8` | `shared_oscillation` | 0.002520 | 0.005807 |
| `exact_reference_projected8` | `shared_ramp` | 0.004740 | 0.008587 |
| `exact_reference_projected8` | `shared_step` | 0.004340 | 0.007900 |
| `hinge_reference_projected8` | `quiet` | 0.002400 | 0.005096 |
| `hinge_reference_projected8` | `shared_bump` | 0.003520 | 0.007670 |
| `hinge_reference_projected8` | `shared_oscillation` | 0.002200 | 0.006042 |
| `hinge_reference_projected8` | `shared_ramp` | 0.004200 | 0.007670 |
| `hinge_reference_projected8` | `shared_step` | 0.005140 | 0.007900 |
| `permuted_hinge_reference_projected8` | `quiet` | 0.002120 | 0.004856 |
| `permuted_hinge_reference_projected8` | `shared_bump` | 0.003220 | 0.006744 |
| `permuted_hinge_reference_projected8` | `shared_oscillation` | 0.002060 | 0.005334 |
| `permuted_hinge_reference_projected8` | `shared_ramp` | 0.003460 | 0.007208 |
| `permuted_hinge_reference_projected8` | `shared_step` | 0.004780 | 0.009497 |

## 10. Previsão

- exato na faixa: `CONFIRMADO`;
- hinge na faixa: `CONFIRMADO`;
- permutado na faixa: `REFUTADO`;
- diferença entre -1 e +1 ponto: `REFUTADA`;
- controles válidos: `CONFIRMADOS`;
- permutado operacional: `REFUTADO`;
- equivalência: `REFUTADA`;
- precisão permutada não superior: `CONFIRMADA`;
- veredito previsto `ONSET_DISTRIBUTION_ONLY`: `REFUTADO`.

Previsão integralmente confirmada: `False`.

A previsão principal estava errada: a associação curva–onset foi muito mais importante do que o esperado.

## 11. Conclusão permitida

> Sob endpoint t50, forma e duração exatos, o onset hinge da própria curva alcançou recall de 77,49%, enquanto os mesmos onsets permutados dentro do grupo alcançaram 69,88%. O ganho pareado foi de 7,61 pontos, com limite inferior unilateral de 7,47 pontos e superioridade em 10/10 holdouts.

Portanto:

- o sucesso do M32 não é explicado apenas pela distribuição marginal dos onsets;
- o hinge contém informação curva-específica útil para alinhar o detector;
- essa informação ainda não é precisa o bastante para representar o onset físico.

A denominação metodologicamente correta neste estágio é:

`âncora causal de alinhamento`

e não `timestamp físico de onset confirmado`.

## 12. Próximo passo correto

O próximo oráculo a retirar é o endpoint t50. Isso deve ser feito sem alterar hinge, projeção, forma ou duração.

O M34 deverá substituir o endpoint exato por uma busca causal de primeiro cruzamento em endpoints sucessivos. Em cada endpoint candidato, o bloco de seleção termina nove cadências antes, seguido por uma guarda e oito cadências de confirmação.

A calibração deverá controlar o falso alerta por curva após toda a busca temporal, incorporando explicitamente o look-elsewhere. A métrica positiva deverá exigir alerta até t50 ou dentro de uma latência prospectivamente congelada.