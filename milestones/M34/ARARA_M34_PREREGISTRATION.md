# ARARA From Zero — Pré-registro M34 Rolling Causal Endpoint Search

**Versão:** M34.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** retirada prospectiva do endpoint-oráculo \(t_{50}\).

## 1. Pergunta pequena

Mantendo forma, duração e parâmetros do template exatos, o pipeline hinge + reference projection continua operacional quando o endpoint \(t_{50}\) é substituído por uma busca causal de primeiro cruzamento?

## 2. Única alteração

\[
e=t_{50,\mathrm{exato}}
\quad\longrightarrow\quad
\widehat e
=
\min\{e:Z(e)\geq\theta\}.
\]

O hinge, a normalização SBW, a projeção do modo comum e a janela de oito cadências permanecem congelados.

## 3. Métodos pareados

### Controle

`hinge_exact_t50`

- estima o hinge causalmente usando a divisão anterior ao \(t_{50}\);
- calcula o score no endpoint exato \(t_{50}\).

### Candidato

`rolling_hinge_first_crossing`

- avalia endpoints inteiros de 81 a 179, inclusive;
- em cada endpoint estima o hinge usando somente o bloco causal anterior;
- emite alerta no primeiro cruzamento do limiar.

Os dois métodos usam as mesmas curvas.

## 4. Divisão temporal em cada endpoint candidato

Para cada \(e\):

- seleção:
\[
[50,e-9];
\]

- guarda:
\[
e-8;
\]

- confirmação:
\[
[e-7,e].
\]

Nenhuma amostra da confirmação participa da estimação do hinge.

## 5. Grade temporal

\[
\mathcal E=\{81,82,\ldots,179\}.
\]

São 99 endpoints.

O início 81 é o primeiro endpoint para o qual existe ao menos um candidato de onset com três amostras posteriores na seleção.

A busca segue até o fim da curva sintética. Não haverá horizonte oculto menor nos negativos.

## 6. Definição de detecção positiva

Seja \(e_{\rm alert}\) o primeiro cruzamento.

A detecção primária é verdadeira somente se:

\[
\tau_{\rm true}
\leq
e_{\rm alert}
\leq
t_{50}.
\]

Consequências:

- cruzamento antes do onset verdadeiro é gatilho precoce e conta como miss;
- cruzamento depois de \(t_{50}\) é alerta tardio e conta como miss;
- ausência de cruzamento é miss.

Será reportada secundariamente, sem alterar gates, a detecção até \(t_{50}+4\).

## 7. Falso alerta e look-elsewhere

Para cada curva negativa:

\[
Z_{\max}
=
\max_{e\in\mathcal E} Z(e).
\]

O limiar rolling será calibrado diretamente sobre \(Z_{\max}\).

Logo, o falso alerta é definido por curva:

\[
P(\exists e:Z(e)\geq\theta).
\]

Não será usado FPR por endpoint.

## 8. Calibração

Serão gerados 50.000 negativos por cada família.

Cada curva produz:

- score controle no endpoint virtual \(t_{50}\);
- máximo rolling nos 99 endpoints.

Cada método terá limiar próprio para FPR empírico máximo de 0,5% por família.

Root seed:

`2026082901`.

## 9. Dez holdouts

Cada holdout terá:

- 2.500 positivos por cada um dos oito estratos;
- 5.000 negativos por família;
- 20 lotes;
- 10.000 réplicas de bootstrap;
- métodos pareados nas mesmas curvas.

Root seeds:

- curvas: `2026082902`;
- bootstrap agregado: `2026082903`;
- bootstrap da diferença: `2026082904`.

## 10. Convenção de confiança

Todos os gates usam limites unilaterais de 95%:

- inferior: quantil 0,05;
- superior: quantil 0,95.

## 11. Validade do controle

O teste é interpretável somente se `hinge_exact_t50`:

1. passa em pelo menos 8/10 holdouts;
2. possui limite inferior agregado \(\geq0.60\);
3. controla FPR em pelo menos 9/10 holdouts;
4. não apresenta violação extrema.

Falha produz:

`INVALID_M34_EXACT_ENDPOINT_CONTROL`.

## 12. Gate operacional rolling por holdout

O candidato passa se:

1. cada família:
\[
FPR_{\mathrm{upper}}^{95\%,unilateral}\leq0.01;
\]

2. recall primário:
\[
R_{\mathrm{lower}}^{95\%,unilateral}\geq0.60;
\]

3. pelo menos 6/8 estratos têm limite inferior \(\geq0.50\);

4. pelo menos 15/20 lotes têm recall \(\geq0.55\).

## 13. Gate agregado rolling

O candidato passa agregado se:

1. pelo menos 8/10 holdouts passam;
2. limite inferior agregado \(\geq0.60\);
3. pelo menos 9/10 holdouts controlam FPR;
4. nenhuma violação extrema de FPR acima de 1,5%.

## 14. Comparação pareada

Será reportada:

\[
\Delta R
=
R_{\mathrm{rolling}}
-
R_{\mathrm{exact}}.
\]

Não existe gate adicional de não inferioridade. O contrato absoluto é primário.

## 15. Veredito

### Passe

`PASS_ROLLING_CAUSAL_ENDPOINT_CANDIDATE`

se:

- controle válido;
- rolling passa operacionalmente.

### Falha forte

`STRONG_FAIL_ROLLING_CAUSAL_ENDPOINT`

se o controle é válido e qualquer ocorre:

- rolling passa em no máximo 2/10 holdouts;
- limite superior agregado do recall rolling \(\leq0.60\);
- violação extrema de FPR.

### Inconclusivo

`INCONCLUSIVE_ROLLING_CAUSAL_ENDPOINT`

nos demais casos.

## 16. Diagnósticos congelados

Sem alterar gates:

- limiar e família determinante;
- primeiro endpoint de alerta;
- gatilhos antes do onset;
- alertas entre onset e \(t_{50}\);
- alertas entre \(t_{50}+1\) e \(t_{50}+4\);
- alertas depois de \(t_{50}+4\);
- ausência de alerta;
- latência \(e_{\rm alert}-t_{50}\);
- erro do hinge no instante do alerta;
- recall por estrato;
- detecções pareadas;
- AUROC/AP usando o máximo rolling como ranking;
- correlação entre score exato e máximo rolling.

## 17. Previsão antes dos dados

O look-elsewhere de 99 endpoints deve elevar substancialmente o limiar.

Prevê-se:

\[
R_{\mathrm{exact}}\in[0.74,0.80],
\]

\[
R_{\mathrm{rolling}}\in[0.20,0.55],
\]

\[
\Delta R\in[-0.58,-0.20].
\]

Prevê-se:

- controle válido;
- FPR robusto nos dois métodos;
- 0–3 holdouts rolling aprovados;
- limiar rolling entre 5,5 e 10;
- veredito:

`STRONG_FAIL_ROLLING_CAUSAL_ENDPOINT`.

## 18. Limites da interpretação

Mesmo um passe não demonstra autonomia completa. Permanecem oraculares:

- forma;
- duração;
- parâmetros do template.

## 19. Regras contra puxadinho

1. Exatamente dois métodos.
2. Exatamente 99 endpoints rolling.
3. Primeiro cruzamento, nunca argmax, define o alerta.
4. FPR rolling por curva após toda a busca.
5. Exatamente 50.000 negativos por família.
6. Exatamente dez holdouts.
7. Limiar próprio por método.
8. Nenhum holdout antes do congelamento.
9. Nenhuma seed, família, estrato, endpoint ou lote será removido.
10. Nenhum gate será alterado após os dados.
11. Código, seeds, dependências e limiares serão congelados por hash.
