# ARARA From Zero — Pré-registro M37R Validity-First Pooled Calibration Replication

**Versão:** M37R.0  
**Estado:** congelado antes da implementação, calibração e holdouts  
**Natureza:** repetição independente do M37, priorizando a validade do controle por estabilização prospectiva da cauda de calibração.

## 1. Motivação

O M37 foi executado integralmente, mas recebeu:

`INVALID_M37_EXACT_DURATION_CONTROL`

porque o controle de duração exata passou somente 1/10 holdouts.

A auditoria demonstrou equivalência numérica entre o controle M37 e o banco M36 nas mesmas curvas, com diferença máxima de score de aproximadamente \(2,3\times10^{-13}\). A hipótese operacional para o M37R é, portanto, sensibilidade da cauda empírica de calibração, e não correção da equação do detector.

O M37R não reclassifica o M37.

## 2. Pergunta científica

Mantendo o parâmetro latente de inclinação exato, a detecção rolling continua operacional quando a duração verdadeira é substituída pelo banco completo:

\[
\mathcal D=\{24,25,\ldots,60\},
\]

com:

\[
37\times4\times99=14.652
\]

hipóteses por curva?

## 3. Matemática congelada

Toda a matemática é importada do M37 sem alteração:

- quatro formas;
- 37 durações;
- endpoints 81–179;
- seleção até \(e-9\);
- guarda em \(e-8\);
- confirmação em \(e-7,\ldots,e\);
- hinge causal;
- projeção das referências;
- primeiro cruzamento;
- contrato de latência até \(t_{50}+4\);
- amplitude/SNR 13,75;
- parâmetro latente contínuo exato;
- mesma ordem de desempate.

## 4. Métodos

### Controle

`rolling_four_shape_exact_duration_latency4`

Avalia quatro formas usando a duração verdadeira.

### Candidato

`rolling_four_shape_full_duration_bank_latency4`

Avalia todas as 14.652 combinações de endpoint, forma e duração.

## 5. Única mudança metodológica

A calibração anterior usou 50.000 negativos por família.

O M37R usará quatro blocos independentes:

\[
B_1,B_2,B_3,B_4,
\]

cada um com:

\[
50.000\text{ negativos por família}.
\]

Logo:

\[
N_{\rm calib}=200.000
\]

por família e:

\[
1.000.000
\]

de curvas negativas no total.

Os blocos terão seeds independentes. Eles não serão selecionados, descartados ou ponderados segundo seus resultados.

## 6. Limiar agrupado

Para cada família e método, os quatro blocos serão concatenados antes da escolha do limiar.

Com alvo de FPR empírico de 0,5%, o número máximo permitido em cada família será:

\[
\lfloor0,005\times200.000\rfloor=1.000
\]

alertas.

O limiar global de cada método será o maior limiar específico entre as cinco famílias, como nos protocolos anteriores.

Os limiares específicos de cada bloco serão reportados apenas como diagnóstico de estabilidade. Não serão usados para votação, média, mediana, exclusão de blocos ou alteração do limiar agrupado.

## 7. Sequência de abertura

1. Pré-registro, código, testes e seeds são congelados por hash.
2. Os vinte blocos família×bloco são gerados.
3. Cada bloco deve conter exatamente 50.000 registros finitos.
4. Cada família deve conter exatamente 200.000 registros depois da concatenação.
5. Os limiares agrupados são congelados.
6. Um segundo manifesto de hashes é criado.
7. Somente então os holdouts podem ser abertos.

## 8. Seeds independentes

Root seeds:

- calibração em blocos: `2026090301`;
- holdouts: `2026090302`;
- bootstrap agregado: `2026090303`;
- bootstrap pareado: `2026090304`.

Cada combinação bloco×família recebe uma child seed distinta.

## 9. Holdouts

Serão executados dez holdouts independentes.

Cada holdout terá:

- 2.500 positivos por cada um dos oito estratos;
- 5.000 negativos por família;
- 20 lotes;
- métodos pareados nas mesmas curvas;
- 10.000 réplicas de bootstrap.

Nada nos holdouts é ampliado ou reduzido em relação ao M37.

## 10. Convenção de confiança

Os gates usam limites unilaterais de 95%:

- inferior: quantil 0,05;
- superior: quantil 0,95.

Os dois limites apresentados em conjunto formam intervalo central de 90%.

## 11. Validade do controle

O teste é interpretável somente se o controle:

1. passa em pelo menos 8/10 holdouts;
2. possui limite inferior agregado de recall \(\geq0,60\);
3. controla FPR em pelo menos 9/10 holdouts;
4. não apresenta violação extrema acima de 1,5%.

Falha produz:

`INVALID_M37R_EXACT_DURATION_CONTROL`.

Esse gate tem precedência absoluta sobre o candidato.

## 12. Gate operacional do candidato

Por holdout, o candidato passa se:

1. cada família tem limite superior unilateral de FPR \(\leq0,01\);
2. limite inferior unilateral do recall \(\geq0,60\);
3. pelo menos 6/8 estratos têm limite inferior \(\geq0,50\);
4. pelo menos 15/20 lotes têm recall \(\geq0,55\).

Agregado, passa se:

1. pelo menos 8/10 holdouts passam;
2. limite inferior agregado \(\geq0,60\);
3. pelo menos 9/10 holdouts controlam FPR;
4. não há violação extrema.

## 13. Identificação da duração

Entre detecções primárias corretas:

- acurácia exata: \(\widehat d=d_{\rm true}\);
- acurácia tolerante: \(|\widehat d-d_{\rm true}|\leq2\).

A identificação passa se:

1. limite inferior unilateral agregado da acurácia tolerante \(\geq0,70\);
2. pelo menos 8/10 holdouts têm limite inferior unilateral \(\geq0,70\).

A acurácia exata é diagnóstica.

## 14. Veredito

### Controle inválido

`INVALID_M37R_EXACT_DURATION_CONTROL`

### Detecção e identificação passam

`PASS_M37R_FULL_DURATION_BANK_AND_IDENTIFICATION`

### Detecção passa, duração não

`PASS_M37R_DETECTION_DURATION_UNRELIABLE`

### Falha forte

`STRONG_FAIL_M37R_FULL_DURATION_BANK`

se o controle é válido e qualquer ocorre:

- no máximo 2/10 holdouts passam o candidato;
- limite superior agregado do recall do candidato \(\leq0,60\);
- violação extrema de FPR.

### Inconclusivo

`INCONCLUSIVE_M37R_FULL_DURATION_BANK`

nos demais casos.

## 15. Diagnósticos congelados

Sem alterar gates:

- limiares agrupados e por bloco;
- família determinante;
- recall por estrato;
- comparação pareada;
- identificação exata e ±2 da duração;
- distribuição do erro de duração;
- forma escolhida;
- duração escolhida nos negativos;
- latência;
- AUROC/AP;
- retenção de energia.

## 16. Previsão

A combinação retrospectiva de duas calibrações anteriores de 50.000 sugere que o limiar do controle pode ficar entre os valores extremos observados no M36 e M37. Essa informação é usada somente para previsão.

Prevê-se:

\[
\theta_{\rm control}\in[7,10,7,24],
\]

\[
\theta_{\rm full}\in[7,40,7,65],
\]

\[
R_{\rm control}\in[0,745,0,765],
\]

\[
R_{\rm full}\in[0,725,0,750],
\]

\[
R_{\rm full}-R_{\rm control}\in[-0,035,-0,005].
\]

Também se prevê:

- controle válido, mas próximo da fronteira estratificada;
- 5–10 holdouts aprovados no controle;
- 2–9 holdouts aprovados no candidato;
- FPR robusto;
- identificação de duração muito abaixo de 70%;
- veredito mais provável:

`INCONCLUSIVE_M37R_FULL_DURATION_BANK`.

A previsão é deliberadamente ampla porque o objetivo principal é resolver a validade, não prometer um passe.

## 17. Interpretação

Um passe permitirá afirmar somente que, dentro do modelo sintético e mantendo o parâmetro latente exato, a duração verdadeira não é necessária para detectar o evento.

Não permitirá interpretar a duração vencedora como duração física, nem validar dados reais ou missão.

## 18. Regras contra puxadinho

1. A matemática M37 não será alterada.
2. Exatamente quatro blocos independentes.
3. Exatamente 50.000 negativos por bloco e família.
4. Exatamente 200.000 negativos agrupados por família.
5. Nenhum bloco será excluído.
6. O limiar será escolhido somente após concatenar os quatro blocos.
7. Exatamente dez holdouts.
8. Nenhum holdout será aberto antes do segundo congelamento.
9. Nenhuma seed, família, duração, forma, endpoint, estrato ou lote será removido.
10. Nenhum gate será alterado depois dos dados.
11. M36 e M37 permanecem com seus vereditos originais.
