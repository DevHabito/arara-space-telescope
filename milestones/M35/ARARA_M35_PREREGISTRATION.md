# ARARA From Zero — Pré-registro M35 Independent Rolling Endpoint Latency-4 Test

**Versão:** M35.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** teste prospectivo independente da hipótese de latência máxima de quatro cadências, motivada pelo diagnóstico pré-registrado do M34.

## 1. Pergunta

Sem alterar a busca causal rolling do M34, o candidato satisfaz o contrato operacional quando uma detecção positiva é definida por primeiro cruzamento entre o onset verdadeiro e \(t_{50}+4\)?

## 2. Relação com o M34

O M34 permanece classificado como `STRONG_FAIL_ROLLING_CAUSAL_ENDPOINT` sob latência zero.

O M35 não reclassifica, corrige ou substitui esse resultado. Ele testa em novos dados:

\[
\tau_{\rm true}\leq e_{\rm alert}\leq t_{50}+4.
\]

## 3. Única mudança

Em relação ao M34, altera-se apenas a janela de sucesso positivo.

M34:

\[
\tau_{\rm true}\leq e_{\rm alert}\leq t_{50}.
\]

M35:

\[
\tau_{\rm true}\leq e_{\rm alert}\leq t_{50}+4.
\]

Permanecem idênticos:

- endpoints 81–179;
- 99 tentativas por curva;
- primeiro cruzamento;
- hinge causal;
- guarda de uma cadência;
- confirmação de oito cadências;
- projeção do modo comum das referências;
- forma, duração e parâmetros do template exatos;
- calibração do máximo rolling por curva;
- gates de FPR, recall, estratos e lotes.

## 4. Métodos

### Controle

`hinge_exact_t50` usa o hinge causal e o score no endpoint exato \(t_{50}\).

### Candidato

`rolling_hinge_first_crossing` avalia os 99 endpoints e usa o primeiro cruzamento.

O score e o limiar não conhecem \(t_{50}+4\). A janela de latência é usada somente para rotular o sucesso positivo.

## 5. Falso alerta

Para cada negativo:

\[
Z_{\max}=\max_{81\leq e\leq179}Z(e).
\]

O limiar é calibrado por curva sobre \(Z_{\max}\), para FPR empírico máximo de 0,5% por família. Não haverá FPR por endpoint.

## 6. Calibração independente

Serão gerados 50.000 negativos por família.

Root seed: `2026083001`.

## 7. Dez holdouts independentes

Cada holdout terá:

- 2.500 positivos por cada um dos oito estratos;
- 5.000 negativos por família;
- 20 lotes;
- os dois métodos nas mesmas curvas;
- 10.000 réplicas de bootstrap.

Root seeds:

- holdouts: `2026083002`;
- bootstrap agregado: `2026083003`;
- bootstrap pareado: `2026083004`.

## 8. Convenção de confiança

Os gates usam limites unilaterais de 95%:

- inferior: quantil 0,05;
- superior: quantil 0,95.

Quando apresentados juntos, correspondem ao intervalo central de 90%.

## 9. Validade do controle

O teste é interpretável somente se o controle:

1. passa em pelo menos 8/10 holdouts;
2. possui limite inferior agregado \(\geq0.60\);
3. controla FPR em pelo menos 9/10 holdouts;
4. não apresenta violação extrema.

Falha produz `INVALID_M35_EXACT_ENDPOINT_CONTROL`.

## 10. Gate do candidato por holdout

O rolling passa se:

1. cada família:
\[
FPR_{\rm upper}^{95\%,unilateral}\leq0.01;
\]

2. recall até \(t_{50}+4\):
\[
R_{\rm lower}^{95\%,unilateral}\geq0.60;
\]

3. pelo menos 6/8 estratos têm limite inferior \(\geq0.50\);

4. pelo menos 15/20 lotes têm recall \(\geq0.55\).

## 11. Gate agregado

O rolling passa agregado se:

1. pelo menos 8/10 holdouts passam;
2. limite inferior agregado \(\geq0.60\);
3. pelo menos 9/10 holdouts controlam FPR;
4. nenhuma violação extrema acima de 1,5%.

## 12. Veredito

`PASS_ROLLING_ENDPOINT_LATENCY4` se controle válido e rolling passa agregado.

`STRONG_FAIL_ROLLING_ENDPOINT_LATENCY4` se o controle é válido e qualquer ocorre:

- no máximo 2/10 holdouts passam;
- limite superior agregado do recall \(\leq0.60\);
- violação extrema de FPR.

`INCONCLUSIVE_ROLLING_ENDPOINT_LATENCY4` nos demais casos.

## 13. Diagnósticos congelados

Sem alterar gates:

- recall com latência zero;
- recall com latência \(+1,+2,+3,+4\);
- distribuição do primeiro cruzamento;
- gatilhos antes do onset;
- alertas depois de \(t_{50}+4\);
- ausência de alerta;
- recall por estrato;
- detecções pareadas;
- AUROC/AP do máximo rolling;
- FPR por família.

## 14. Previsão

\[
R_{\rm exact}\in[0.74,0.80],
\]

\[
R_{\rm rolling,+4}\in[0.73,0.79],
\]

\[
R_{\rm rolling,+4}-R_{\rm exact}\in[-0.08,+0.01].
\]

Prevê-se ainda:

- limiar rolling entre 6,3 e 7,6;
- FPR robusto;
- 8–10 holdouts rolling aprovados;
- pelo menos 6/8 estratos bons em cada holdout aprovado;
- veredito `PASS_ROLLING_ENDPOINT_LATENCY4`.

## 15. Interpretação permitida em caso de passe

> Dentro do modelo sintético e sob forma e duração exatas, o endpoint \(t_{50}\) não é necessário para disparar o alerta, desde que o contrato aceite latência algorítmica máxima de quatro cadências.

Isso não converte quatro cadências em tempo físico e não demonstra autonomia de forma ou duração.

## 16. Regras contra puxadinho

1. Implementação matemática importada do M34 sem alteração.
2. Exatamente 99 endpoints.
3. Primeiro cruzamento, nunca argmax, define o alerta.
4. Exatamente 50.000 negativos por família.
5. Exatamente dez holdouts.
6. Nova calibração e novas seeds.
7. Nenhum holdout antes do congelamento.
8. Nenhuma seed, família, estrato, endpoint ou lote será removido.
9. Nenhum gate será alterado após os dados.
10. O resultado M34 não será reclassificado.
