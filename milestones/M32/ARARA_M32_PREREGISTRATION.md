# ARARA From Zero — Pré-registro M32 Split-Onset Feeding Confirmed Reference Projection

**Versão:** M32.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** retirada prospectiva de um único oráculo do downstream confirmado M30–M31.

## 1. Pergunta pequena

Mantendo endpoint \(t_{50}\), forma e duração exatos, o downstream confirmado `reference_projected8` continua operacional quando o onset exato é substituído pelo estimador causal dividido do M25?

Pergunta separada:

O onset estimado é localizado com precisão suficiente para ser reportado como instante físico confiável?

## 2. Princípio causal

O M32 altera somente:

\[
\tau_{\rm exato}\rightarrow\widehat{\tau}_{\rm hinge}.
\]

Permanecem idênticos ao M31:

- normalização SBW;
- modo comum processado das referências;
- projeção de uma dimensão;
- janela final de oito cadências;
- condição \(13.75\sigma\);
- endpoint \(t_{50}\);
- forma e duração;
- gates de detecção;
- calibração por família.

## 3. Métodos pareados

### Controle oracular

`exact_reference_projected8`

usa o template no onset verdadeiro.

### Candidato

`split_onset_reference_projected8`

usa o mesmo template deslocado por:

\[
\Delta\tau=\widehat{\tau}-\tau.
\]

O template deslocado é submetido ao mesmo operador de sinal SBW e à mesma projeção do modo comum das referências.

## 4. Estimação causal do onset

Para cada endpoint \(e=t_{50}\):

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

O onset é estimado somente na região de seleção.

As oito cadências usadas pelo score e a cadência de guarda não participam da estimação.

A busca de onset permanece congelada em:

\[
70\leq\widehat{\tau}\leq120.
\]

A função de dobradiça e todas as regras numéricas são importadas diretamente do M25.

## 5. Score confirmado

Para o controle e o candidato:

\[
v_\perp
=
v-q\frac{q^\top v}{q^\top q},
\]

\[
Z_{q\perp}
=
\frac{
r_\perp^\top h_\perp
}{
\lVert h_\perp\rVert_2
}.
\]

Não serão adicionadas constante, rampa, transformação t ou regularização.

## 6. Calibração

Serão gerados 50.000 negativos por cada uma das cinco famílias.

Cada negativo recebe:

- template virtual;
- onset virtual de referência;
- endpoint virtual \(t_{50}\);
- onset estimado no bloco causal anterior.

Cada curva produzirá os dois scores pareados.

Cada método terá limiar próprio, calibrado para FPR empírico máximo de 0,5% por família.

Root seed:

`2026082701`.

## 7. Dez holdouts

Cada holdout terá:

- 2.500 positivos por cada um dos oito estratos;
- 5.000 negativos por família;
- 20 lotes;
- 10.000 réplicas de bootstrap;
- os dois métodos nas mesmas curvas.

Root seeds:

- holdouts: `2026082702`;
- bootstrap agregado: `2026082703`;
- bootstrap pareado da diferença: `2026082704`.

## 8. Convenção de confiança

Os gates usam limites unilaterais de 95%:

- inferior: quantil 0,05;
- superior: quantil 0,95.

## 9. Gate de validade do controle

O M32 será interpretável somente se `exact_reference_projected8` repetir o contrato do M31:

1. pelo menos 8/10 holdouts passam;
2. limite inferior agregado do recall \(\geq0.60\);
3. FPR robusto.

Falha do controle produz:

`INVALID_EXACT_CONTROL_FAILURE`.

## 10. Gate operacional do candidato

O candidato passa detecção num holdout somente se:

1. cada família:
\[
FPR_{\mathrm{upper}}^{95\%,\,unilateral}\leq0.01;
\]

2. recall:
\[
R_{\mathrm{lower}}^{95\%,\,unilateral}\geq0.60;
\]

3. pelo menos 6/8 estratos têm limite inferior \(\geq0.50\);

4. pelo menos 15/20 lotes têm recall \(\geq0.55\).

Passa agregado se:

1. pelo menos 8/10 holdouts passam detecção;
2. limite inferior agregado \(\geq0.60\);
3. pelo menos 9/10 holdouts controlam FPR;
4. nenhuma família ultrapassa limite superior de FPR de 1,5%.

## 11. Gate separado de localização do onset

O envelope operacional permanece:

\[
-2\leq\widehat{\tau}-\tau\leq+1.
\]

Acurácia primária de localização:

\[
A_{\rm onset}
=
\frac{
\text{alertas com erro dentro do envelope}
}{
\text{alertas emitidos pelo candidato}
}.
\]

A localização passa se:

1. limite inferior unilateral agregado de 95% \(\geq0.90\);
2. pelo menos 8/10 holdouts têm limite inferior unilateral \(\geq0.90\).

Também será reportada, sem alterar gates, a acurácia entre todos os positivos.

## 12. Comparação pareada com o controle

Será reportada:

\[
\Delta R
=
R_{\rm candidato}
-
R_{\rm exato}.
\]

Não existe gate de não inferioridade adicional: o requisito operacional absoluto de 60% é primário.

## 13. Veredito

### Passe completo

`PASS_SPLIT_ONSET_CANDIDATE`

se:

- controle válido;
- candidato passa operacionalmente;
- localização do onset passa.

### Detecção funcional, onset não confiável

`PASS_DETECTION_ONSET_UNRELIABLE`

se:

- controle válido;
- candidato passa operacionalmente;
- localização não passa.

### Falha forte de detecção

`STRONG_FAIL_SPLIT_ONSET_WITH_CONFIRMED_DOWNSTREAM`

se o controle é válido e qualquer ocorre:

- no máximo 2/10 holdouts passam detecção;
- limite superior agregado do recall candidato \(\leq0.60\);
- violação extrema de FPR.

### Inconclusivo

`INCONCLUSIVE_SPLIT_ONSET_WITH_CONFIRMED_DOWNSTREAM`

nos demais casos.

## 14. Diagnósticos congelados

Sem alterar os gates:

- erro de onset entre todos os positivos;
- erro entre alertas;
- mediana e mediana absoluta do erro;
- erros muito precoces e muito tardios;
- recall por estrato;
- matrizes pareadas de detecção;
- correlação dos scores;
- retenção de energia do template exato e deslocado;
- limiares e famílias determinantes.

## 15. Previsão antes dos dados

Com base no M25 e no downstream M31, prevê-se:

\[
R_{\rm exato}\in[0.75,0.85],
\]

\[
R_{\rm candidato}\in[0.45,0.70],
\]

\[
\Delta R\in[-0.35,-0.10].
\]

Prevê-se ainda:

- controle válido;
- FPR robusto nos dois métodos;
- acurácia do onset entre alertas em \([0.20,0.45]\);
- localização do onset não passará;
- entre 3 e 8 holdouts passarão detecção.

Veredito previsto:

`INCONCLUSIVE_SPLIT_ONSET_WITH_CONFIRMED_DOWNSTREAM`.

A faixa cruza deliberadamente a fronteira operacional; o teste foi desenhado para decidir, não para presumir o lado.

## 16. Limites da interpretação

Mesmo um passe completo não demonstra autonomia total, porque continuam oraculares:

- endpoint \(t_{50}\);
- forma;
- duração;
- parâmetros do template.

## 17. Regras contra puxadinho

1. Exatamente dois métodos.
2. Estimador de onset importado do M25 sem alteração.
3. Downstream importado do M31/M30 sem alteração matemática.
4. Exatamente oito cadências de confirmação.
5. Exatamente 50.000 negativos por família.
6. Exatamente dez holdouts.
7. Mesmas curvas para controle e candidato.
8. Limiar próprio para cada método.
9. Nenhum holdout antes do congelamento.
10. Nenhuma seed, família, estrato ou lote será substituído.
11. Nenhum gate será alterado após os dados.
12. Código, seeds, dependências e limiares serão congelados por hash.
