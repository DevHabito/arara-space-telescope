# ARARA From Zero — Relatório do M30 Reference-Common-Mode-Only Projection

**Estado:** concluído  
**Calibração:** 50.000 negativos por família  
**Holdouts:** 10/10  
**Comparação:** prospectiva e pareada nas mesmas curvas  
**Veredito:** `PASS_REFERENCE_PROJECTION_CANDIDATE`  
**Decisão:** promover a projeção exclusiva do modo comum das referências a candidato, pendente de confirmação independente

## 1. Pergunta

Remover somente a direção temporal observada nas estrelas de referência preserva o sinal target-local e reduz a cauda de artefatos compartilhados?

O M30 alterou uma única coisa em relação ao baseline:

\[
v_\perp=v-q\frac{q^\top v}{q^\top q}.
\]

Não foram usados constante, rampa, centralização adicional ou t parcial.

## 2. Resultado agregado

| Método | Limiar | Família determinante | Recall | Limite inferior unilateral 95% | Limite superior unilateral 95% | Passes | FPR |
|---|---:|---|---:|---:|---:|---:|---:|
| `baseline8` | 16.193054 | `shared_step` | 0.309820 | 0.307460 | 0.312195 | 0/10 | 10/10 |
| `reference_projected8` | 4.052855 | `shared_step` | 0.798225 | 0.796400 | 0.800035 | 10/10 | 10/10 |

O candidato passou o contrato em todos os holdouts:

`10/10`.

O limite inferior agregado permaneceu muito acima de 0,60.

## 3. Superioridade pareada

\[
R_{\rm baseline}=0.309820,
\]

\[
R_{\rm candidate}=0.798225.
\]

\[
\Delta R=0.488405.
\]

Limites unilaterais de 95% da diferença:

\[
0.485815
\leq\Delta R\leq
0.490970.
\]

O limite inferior foi aproximadamente 48,58 pontos percentuais, muito acima do gate pré-registrado de 10 pontos.

O candidato superou o baseline por pelo menos oito pontos percentuais em 10/10 holdouts.

## 4. Resultado por holdout

| Holdout | Baseline | Candidato | Diferença | Limite inferior do candidato | Estratos bons | Lotes bons | Passou |
|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | 0.307950 | 0.798100 | 0.490136 | 0.793950 | 8/8 | 20/20 | SIM |
| 1 | 0.309200 | 0.796900 | 0.487738 | 0.792750 | 8/8 | 20/20 | SIM |
| 2 | 0.306450 | 0.794700 | 0.488215 | 0.790450 | 8/8 | 20/20 | SIM |
| 3 | 0.304750 | 0.797600 | 0.492820 | 0.793550 | 8/8 | 20/20 | SIM |
| 4 | 0.313050 | 0.794750 | 0.481731 | 0.790700 | 8/8 | 20/20 | SIM |
| 5 | 0.315650 | 0.801150 | 0.485565 | 0.797100 | 8/8 | 20/20 | SIM |
| 6 | 0.307400 | 0.796900 | 0.489503 | 0.792900 | 8/8 | 20/20 | SIM |
| 7 | 0.312400 | 0.799850 | 0.487430 | 0.795750 | 8/8 | 20/20 | SIM |
| 8 | 0.312250 | 0.802800 | 0.490528 | 0.798800 | 8/8 | 20/20 | SIM |
| 9 | 0.309100 | 0.799500 | 0.490380 | 0.795450 | 8/8 | 20/20 | SIM |

## 5. Resultado por forma e contexto

| Estrato | Baseline | Candidato | Retenção média de energia | Mediana dos lotes |
|---|---:|---:|---:|---:|
| `exponential__clean` | 0.249920 | 0.992560 | 0.790703 | 0.874664 |
| `exponential__concurrent` | 0.413960 | 0.587200 | 0.220447 | 0.091892 |
| `linear__clean` | 0.283640 | 0.992560 | 0.788076 | 0.873720 |
| `linear__concurrent` | 0.444200 | 0.582200 | 0.199641 | 0.082969 |
| `logistic__clean` | 0.139400 | 0.988600 | 0.796775 | 0.876373 |
| `logistic__concurrent` | 0.303440 | 0.654440 | 0.247353 | 0.152742 |
| `power_law__clean` | 0.241480 | 0.992280 | 0.790759 | 0.872575 |
| `power_law__concurrent` | 0.402520 | 0.595960 | 0.222314 | 0.097585 |

Nos estratos `clean`, o candidato detectou aproximadamente 99% dos positivos.

Nos estratos `concurrent`, a projeção removeu grande parte da energia do template, mas o recall permaneceu entre aproximadamente 58% e 65%. Isso foi suficiente para que todos os oito estratos e todos os vinte lotes satisfizessem os gates em cada holdout.

## 6. Retenção de energia

- retenção média ponderada nos positivos: `0.507008`;
- mediana das medianas por lote: `0.491788`;
- modo comum degenerado: `0.000000`;
- template projetado degenerado: `0.000000`.

A previsão de retenção mediana acima de 0,70 foi refutada. Mesmo retendo aproximadamente metade da energia em média, o candidato ganhou porque o limiar caiu muito mais do que a resposta positiva.

## 7. Limiar e falso alerta

- baseline: `16.193054`;
- candidato: `4.052855`.

A família determinante continuou sendo `shared_step`, mas o limiar caiu aproximadamente quatro vezes.

Os dois métodos controlaram o FPR em 10/10 holdouts, sem violação extrema.

| Método | Família | Taxa agregada | Maior limite superior unilateral 95% |
|---|---|---:|---:|
| `baseline8` | `quiet` | 0.000000 | 0.000599 |
| `baseline8` | `shared_bump` | 0.001420 | 0.003639 |
| `baseline8` | `shared_oscillation` | 0.000440 | 0.002101 |
| `baseline8` | `shared_ramp` | 0.001660 | 0.003886 |
| `baseline8` | `shared_step` | 0.005560 | 0.009497 |
| `reference_projected8` | `quiet` | 0.002660 | 0.005334 |
| `reference_projected8` | `shared_bump` | 0.004400 | 0.008129 |
| `reference_projected8` | `shared_oscillation` | 0.002800 | 0.004856 |
| `reference_projected8` | `shared_ramp` | 0.005160 | 0.009270 |
| `reference_projected8` | `shared_step` | 0.005200 | 0.008358 |

## 8. Contagens pareadas dos 200.000 positivos

- nenhum método: `26889`;
- somente candidato: `111147`;
- somente baseline: `13466`;
- ambos: `48498`.

O baseline detectou `61964` positivos.

O candidato detectou `159645` positivos.

## 9. Ranking

- AUROC baseline: `0.986766`;
- AUROC candidato: `0.984913`;
- AP baseline: `0.979891`;
- AP candidato: `0.984672`.

O ganho operacional não veio de inflar genericamente o AUROC. O AUROC permaneceu semelhante, enquanto a cauda extrema tornou-se muito mais utilizável.

## 10. Previsão

- baseline na faixa prevista: `CONFIRMADA`;
- candidato entre 48% e 68%: `REFUTADA`;
- ganho entre 18 e 38 pontos: `REFUTADA`;
- FPR robusto nos dois: `CONFIRMADA`;
- retenção mediana acima de 0,70: `REFUTADA`;
- ganho material pareado: `CONFIRMADO`;
- veredito inconclusivo previsto: `REFUTADO`.

Previsão integralmente confirmada: `False`.

O resultado foi substancialmente melhor que a previsão: não ficou inconclusivo, mas passou os gates de candidato.

## 11. Conclusão permitida

> No modelo sintético atual, sob onset, endpoint, forma e duração exatos, a projeção exclusiva do modo comum processado das estrelas de referência transforma o downstream de oito cadências de um baseline com recall de 30,98% em um candidato com recall de 79,82%, FPR robusto e 10/10 holdouts aprovados.

## 12. Limites

Este resultado ainda não demonstra um detector autônomo ou uma missão viável.

Permanecem como oráculos:

- onset;
- endpoint t50;
- forma;
- duração;
- parâmetros do template.

Além disso, M30 é o teste de descoberta deste candidato. A escolha da estatística foi motivada pelos resultados anteriores, portanto é obrigatória uma confirmação integralmente independente.

## 13. Próximo teste correto

O M31 deve repetir exatamente o M30, sem qualquer mudança de equação, janela, nuisance ou gate, usando:

- nova calibração de 50.000 negativos por família;
- dez novos holdouts;
- novas seeds;
- hashes congelados antes dos dados.

Somente se o M31 confirmar o passe, o `reference_projected8` poderá ser promovido a downstream sintético robustamente confirmado. Depois disso, o próximo gargalo volta a ser retirar o onset-oráculo.