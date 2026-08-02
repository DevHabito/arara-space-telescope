# ARARA From Zero — Pré-registro M37 Full Duration × Shape Rolling Bank

**Versão:** M37.0  
**Estado:** congelado antes da implementação, calibração e holdouts  
**Natureza:** retirada prospectiva somente do oráculo de duração.

## 1. Pergunta

Mantendo o parâmetro latente de inclinação exato, a detecção rolling confirmada no M36 permanece operacional quando a duração verdadeira é substituída pelo banco completo de durações inteiras permitidas?

## 2. Banco completo

O conjunto congelado é:

\[
\mathcal D=\{24,25,\ldots,60\},
\]

com 37 durações, combinado com quatro formas e 99 endpoints:

\[
37\times4\times99=14\,652
\]

hipóteses por curva.

Nenhuma grade esparsa ou duração será escolhida depois dos resultados.

## 3. Oráculo retirado

O controle recebe a duração verdadeira e marginaliza apenas sobre as quatro formas.

O candidato não recebe:

- o rótulo verdadeiro da forma;
- a duração verdadeira.

O candidato recebe ainda:

- o onset de referência usado para deslocar o template após a estimação hinge;
- o parâmetro latente contínuo \(u\in[0,1]\);
- a amplitude/SNR do contrato;
- o conjunto prospectivo das quatro formas e das 37 durações.

O onset físico verdadeiro continua proibido para a decisão; ele é usado somente para avaliar erro temporal.

## 4. Métodos pareados

### Controle

`rolling_four_shape_exact_duration_latency4`

Em cada endpoint, avalia as quatro formas na duração verdadeira.

### Candidato

`rolling_four_shape_full_duration_bank_latency4`

Em cada endpoint, avalia todas as combinações:

\[
(s,d)\in\mathcal S\times\mathcal D.
\]

O score do banco é:

\[
Z_{\rm bank}(e)=\max_{s,d} Z_{s,d}(e).
\]

O alerta é o primeiro endpoint em que o score ultrapassa o limiar próprio.

Empates numéricos exatos seguem a ordem congelada:

1. duração crescente de 24 a 60;
2. dentro de cada duração: linear, power-law, exponencial, logística.

## 5. Busca temporal

Permanece idêntica ao M35–M36:

- endpoints 81–179;
- 99 endpoints;
- seleção até \(e-9\);
- guarda em \(e-8\);
- confirmação em \(e-7,\ldots,e\);
- hinge causal estimado sem receber template;
- primeiro cruzamento, nunca argmax temporal.

## 6. Contrato positivo

Uma detecção é sucesso somente se:

\[
\tau_{\rm true}\le e_{\rm alert}\le t_{50}+4.
\]

Gatilhos antes do onset, alertas posteriores e ausência de alerta são misses.

## 7. Look-elsewhere conjunto

Nos negativos, o controle é calibrado sobre:

\[
\max_{99\times4} Z.
\]

O candidato é calibrado diretamente sobre:

\[
\max_{99\times4\times37} Z.
\]

O falso alerta é por curva após toda a busca. Não haverá correção analítica aproximada nem FPR por hipótese.

## 8. Geração negativa

Cada negativo recebe prospectivamente:

- uma forma virtual verdadeira uniforme entre quatro;
- uma duração virtual verdadeira uniforme entre 24 e 60;
- onset virtual;
- parâmetro latente \(u\);
- o banco completo com o mesmo \(u\).

O sinal virtual verdadeiro é usado somente para processar os templates; não é injetado nos dados negativos.

## 9. Calibração independente

Serão gerados 50.000 negativos por cada família.

Root seed:

`2026090201`.

## 10. Dez holdouts independentes

Cada holdout terá:

- 2.500 positivos por cada um dos oito estratos;
- 5.000 negativos por família;
- 20 lotes;
- métodos pareados nas mesmas curvas;
- 10.000 réplicas de bootstrap.

Root seeds:

- holdouts: `2026090202`;
- bootstrap agregado: `2026090203`;
- bootstrap pareado: `2026090204`.

## 11. Convenção de confiança

Os gates usam limites unilaterais de 95%:

- inferior: quantil 0,05;
- superior: quantil 0,95.

Quando apresentados juntos, formam intervalo central de 90%.

## 12. Validade do controle

O teste é interpretável somente se o controle:

1. passa em pelo menos 8/10 holdouts;
2. possui limite inferior agregado de recall \(\ge0,60\);
3. controla FPR em pelo menos 9/10 holdouts;
4. não apresenta violação extrema acima de 1,5%.

Falha produz:

`INVALID_M37_EXACT_DURATION_CONTROL`.

## 13. Gate operacional do banco

Por holdout, o candidato passa se:

1. cada família tem limite superior unilateral de FPR \(\le0,01\);
2. limite inferior unilateral do recall \(\ge0,60\);
3. pelo menos 6/8 estratos têm limite inferior \(\ge0,50\);
4. pelo menos 15/20 lotes têm recall \(\ge0,55\).

Agregado, passa se:

1. pelo menos 8/10 holdouts passam;
2. limite inferior agregado \(\ge0,60\);
3. pelo menos 9/10 holdouts controlam FPR;
4. nenhuma violação extrema.

## 14. Identificação da duração

Entre detecções primárias corretas, serão reportadas:

- acurácia exata: \(\widehat d=d_{\rm true}\);
- acurácia tolerante: \(|\widehat d-d_{\rm true}|\le2\).

O gate de identificação usa a tolerância de duas cadências e passa se:

1. limite inferior unilateral agregado de 95% \(\ge0,70\);
2. pelo menos 8/10 holdouts têm limite inferior unilateral \(\ge0,70\).

A acurácia exata é diagnóstica e não altera o veredito.

A forma selecionada continuará sendo reportada, mas não terá novo gate, pois o M36 já demonstrou que ela não é classificação confiável.

## 15. Comparação pareada

Será reportada:

\[
\Delta R=R_{\rm full\ duration}-R_{\rm exact\ duration}.
\]

O contrato absoluto permanece primário; não há gate adicional de não inferioridade.

## 16. Veredito

### Detecção e duração passam

`PASS_FULL_DURATION_BANK_AND_IDENTIFICATION`

se controle válido, detecção passa e identificação tolerante passa.

### Detecção passa, duração não

`PASS_DETECTION_DURATION_UNRELIABLE`

se controle válido e detecção passa, mas identificação tolerante não passa.

### Falha forte

`STRONG_FAIL_FULL_DURATION_BANK`

se o controle é válido e qualquer ocorre:

- no máximo 2/10 holdouts passam detecção;
- limite superior agregado do recall \(\le0,60\);
- violação extrema de FPR.

### Inconclusivo

`INCONCLUSIVE_FULL_DURATION_BANK`

nos demais casos.

## 17. Diagnósticos congelados

Sem alterar gates:

- limiares e famílias determinantes;
- recall por estrato e forma verdadeira;
- acurácia exata e ±2 da duração;
- distribuição do erro de duração;
- matriz forma verdadeira × forma selecionada;
- duração selecionada em negativos;
- latência do primeiro cruzamento;
- detecções pareadas;
- AUROC/AP;
- retenção de energia.

## 18. Previsão

Como as durações vizinhas geram templates altamente correlacionados, prevê-se aumento moderado do limiar, mas pequena perda de detecção:

\[
R_{\rm control}\in[0,73,0,79],
\]

\[
R_{\rm full}\in[0,72,0,77],
\]

\[
\Delta R\in[-0,05,0,00].
\]

Prevê-se ainda:

- limiar do banco entre 7,2 e 8,2;
- FPR robusto;
- 8–10 holdouts aprovados;
- acurácia exata de duração entre 0,03 e 0,20;
- acurácia ±2 entre 0,15 e 0,50;
- veredito `PASS_DETECTION_DURATION_UNRELIABLE`.

## 19. Limites

Mesmo um passe de detecção não retira:

- o parâmetro latente contínuo exato;
- amplitude/SNR fixa;
- modelo sintético;
- definição física da cadência;
- validação em dados astronômicos reais.

## 20. Regras contra puxadinho

1. Exatamente dois métodos.
2. Exatamente 37 durações inteiras.
3. Exatamente quatro formas.
4. Exatamente 99 endpoints.
5. Exatamente 14.652 hipóteses no banco candidato.
6. Primeiro cruzamento define o alerta.
7. Limiar próprio por método.
8. Exatamente 50.000 negativos por família.
9. Exatamente dez holdouts.
10. Nenhuma seed, duração, forma, família, estrato, endpoint ou lote será removido.
11. Nenhum gate será alterado após os dados.
12. M34, M35 e M36 permanecem classificados como antes.
