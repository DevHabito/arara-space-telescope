# ARARA From Zero — Pré-registro M22 Controlled Onset-Error Tolerance

**Versão:** M22.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** primeira retirada controlada da informação-oráculo de onset.

## 1. Pergunta pequena

Em \(13.75\sigma\) e com avaliação até \(t_{50}\), o contrato sobrevive quando o onset fornecido ao score possui erro determinístico de até duas cadências em qualquer direção?

## 2. Condição fixa

\[
A/\sigma_0=13.75,\qquad f=0.50.
\]

O nível foi confirmado independentemente no M21.

## 3. Erros de onset congelados

\[
\delta\in\{-4,-2,0,+2,+4\}.
\]

O onset usado pelo score será:

\[
\widehat\tau=\tau+\delta.
\]

Não haverá clipping: a faixa geradora garante que todos os valores permanecem válidos.

## 4. Template usado

O formato e a duração verdadeiros continuam conhecidos.

Para cada \(\delta\), o template bruto inteiro é deslocado pelo mesmo valor:

\[
\widehat s_k=s_{k-\delta},
\]

com preenchimento por zero fora do domínio.

O template deslocado é submetido ao mesmo operador linear de normalização e whitening estimado apenas no baseline.

O score usa:

\[
[\widehat\tau,t_{50}].
\]

O endpoint \(t_{50}\) verdadeiro permanece fornecido. Portanto, M22 remove apenas o onset exato; não remove ainda o endpoint nem a forma/duração exatas.

## 5. Dez replicações completas

Cada replicação terá:

- calibração negativa própria;
- um limiar próprio para cada \(\delta\);
- holdout próprio;
- 2.000 negativos por família no desenvolvimento;
- 2.500 positivos por cada um dos oito estratos no holdout;
- 5.000 negativos por família no holdout;
- 20 lotes;
- bootstrap estratificado com 10.000 réplicas por \(\delta\).

Root seeds:

- replicações: `2026081701`;
- bootstraps agregados: `2026081702`.

Os mesmos campos são emparelhados entre os cinco erros dentro de cada replicação.

## 6. Calibração

Cada \(\delta\) recebe limiar independente, calibrado somente nos negativos daquela condição para FPR empírico máximo de 0,5% por família no desenvolvimento.

A calibração captura a alteração da distribuição nula provocada pelo erro de onset.

## 7. Passe por replicação e por erro

Para um \(\delta\), uma replicação passa somente se:

1. \(FPR_{\mathrm{upper}}^{95\%}\leq0.01\) em cada família;
2. \(R_{\mathrm{lower}}^{95\%}\geq0.60\);
3. pelo menos 6/8 estratos têm limite inferior \(\geq0.50\);
4. pelo menos 15/20 lotes têm recall \(\geq0.55\).

## 8. Passe agregado por erro

Um erro \(\delta\) passa se:

1. pelo menos 8/10 replicações passam;
2. limite inferior hierárquico do recall agregado \(\geq0.60\);
3. pelo menos 9/10 replicações controlam FPR;
4. nenhuma família ultrapassa limite superior de 1,5%.

## 9. Vitória do M22

M22 passa somente se:

- \(\delta=0\) passa;
- \(\delta=-2\) passa;
- \(\delta=+2\) passa.

Rótulo:

`PASS_ONSET_TOLERANCE_PM2`.

## 10. Falha forte

`STRONG_FAIL_ONSET_TOLERANCE` se:

- \(\delta=0\) falha fortemente; ou
- tanto \(-2\) quanto \(+2\) falham fortemente.

Qualquer resultado intermediário será `INCONCLUSIVE`.

## 11. Previsão anterior aos dados

Prevê-se:

1. \(\delta=0\) passará;
2. \(\delta=-2\) e \(+2\) passarão;
3. pelo menos um dos erros de magnitude 4 não passará;
4. recall agregado será máximo em \(\delta=0\);
5. M22 terá veredito `PASS_ONSET_TOLERANCE_PM2`.

Faixas previstas de recall agregado:

\[
R(0)\in[0.64,0.70],
\]

\[
R(-2),R(+2)\in[0.60,0.68],
\]

\[
R(-4),R(+4)\in[0.50,0.64].
\]

## 12. Limite da afirmação

Um passe não demonstra detecção autônoma do onset. Demonstra somente tolerância a uma estimativa externa cujo erro absoluto não exceda duas cadências.

## 13. Regras contra puxadinho

1. Exatamente cinco erros e dez replicações.
2. Nenhum erro, seed, estrato, família ou lote será excluído.
3. Nenhum limiar será compartilhado entre erros.
4. Nenhuma alteração após iniciar a primeira replicação.
5. O endpoint e a forma continuam explicitamente classificados como oráculos.
6. Código, seeds e dependências congelados por hash.
