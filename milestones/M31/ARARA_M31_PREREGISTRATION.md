# ARARA From Zero — Pré-registro M31 Independent Confirmation of Reference Projection

**Versão:** M31.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** réplica confirmatória integralmente independente do M30.

## 1. Pergunta

O candidato `reference_projected8`, descoberto no M30, satisfaz novamente os mesmos gates operacionais e de superioridade em nova calibração e dez novos holdouts?

## 2. Regra central

O M31 repete exatamente o M30.

Não serão alterados:

- equação;
- janela de oito cadências;
- modo comum das referências;
- normalização SBW;
- condição \(A/\sigma_0=13.75\);
- endpoint \(t_{50}\);
- baseline;
- calibração por família;
- gates de recall;
- gates de falso alerta;
- gate de superioridade pareada;
- número de curvas;
- número de lotes;
- bootstrap.

Mudam somente:

- seeds;
- curvas sintéticas;
- calibração;
- holdouts.

## 3. Condição fixa

\[
A/\sigma_0=13.75,\qquad f=0.50,\qquad L=8.
\]

Permanecem como oráculos:

- onset;
- endpoint \(t_{50}\);
- forma;
- duração;
- parâmetros exatos do template.

## 4. Métodos

### Baseline

\[
Z_8=\frac{r^\top h}{\lVert h\rVert_2}.
\]

### Candidato

\[
v_\perp=v-q\frac{q^\top v}{q^\top q},
\]

\[
Z_{q\perp}
=
\frac{r_\perp^\top h_\perp}
{\lVert h_\perp\rVert_2}.
\]

Se \(q^\top q\leq10^{-12}\), a projeção é a identidade.

Se \(\lVert h_\perp\rVert_2\leq10^{-12}\), o score é zero.

## 5. Calibração independente

Serão gerados 50.000 negativos por cada uma das cinco famílias.

Cada curva produzirá os dois scores pareados.

Cada método terá limiar próprio, calibrado para FPR empírico máximo de 0,5% por família.

Root seed:

`2026082601`.

## 6. Dez holdouts independentes

Cada holdout terá:

- 2.500 positivos por cada um dos oito estratos;
- 5.000 negativos por família;
- 20 lotes;
- 10.000 réplicas de bootstrap;
- os dois métodos avaliados nas mesmas curvas.

Root seeds:

- holdouts: `2026082602`;
- bootstrap agregado: `2026082603`;
- bootstrap pareado da diferença: `2026082604`.

## 7. Convenção de confiança

Os gates usam limites unilaterais de 95%:

- inferior: quantil 0,05;
- superior: quantil 0,95.

## 8. Gates por holdout

Um método passa somente se:

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

## 9. Gate operacional agregado

O candidato passa operacionalmente se:

1. pelo menos 8/10 holdouts passam;
2. limite inferior agregado unilateral de 95% \(\geq0.60\);
3. pelo menos 9/10 holdouts controlam FPR;
4. nenhuma família ultrapassa limite superior de FPR de 1,5%.

## 10. Gate de superioridade

\[
\Delta R=R_{\mathrm{candidate}}-R_{\mathrm{baseline}}.
\]

A superioridade passa somente se:

1. limite inferior unilateral de 95%:
\[
\Delta R_{\mathrm{lower}}\geq0.10;
\]

2. diferença de pelo menos 0,08 em pelo menos 8/10 holdouts.

## 11. Veredito confirmatório

### Confirmação

`CONFIRMED_REFERENCE_PROJECTION`

se o candidato passa o gate operacional e o gate de superioridade.

### Ganho parcial

`PARTIAL_GAIN_NOT_OPERATIONAL`

se o limite inferior da diferença é pelo menos 0,10, mas o candidato não passa operacionalmente.

### Falha forte

`STRONG_FAIL_REFERENCE_PROJECTION_REPLICATION`

se qualquer ocorrer:

- limite superior da diferença \(\leq0\);
- limite superior agregado do recall candidato \(\leq0.30\);
- violação extrema de FPR.

### Inconclusivo

`INCONCLUSIVE_REFERENCE_PROJECTION_REPLICATION` nos demais casos.

## 12. Previsão antes dos dados

Com base no M30, prevê-se:

\[
R_{\mathrm{baseline}}\in[0.27,0.34],
\]

\[
R_{\mathrm{candidate}}\in[0.75,0.85],
\]

\[
\Delta R\in[0.43,0.55].
\]

Prevê-se:

- 8–10 holdouts aprovados pelo candidato;
- FPR robusto nos dois métodos;
- nenhuma degeneração relevante do template;
- veredito `CONFIRMED_REFERENCE_PROJECTION`.

## 13. Critério de promoção

Somente `CONFIRMED_REFERENCE_PROJECTION` permite afirmar:

> o downstream sintético reference-projected8 foi confirmado em réplica independente sob oráculos completos.

Isso não valida detector autônomo, instrumento ou missão.

## 14. Regras contra puxadinho

1. Código matemático do M30 importado sem alteração.
2. Exatamente duas estatísticas.
3. Exatamente uma nuisance.
4. Exatamente oito cadências.
5. Exatamente 50.000 negativos por família.
6. Exatamente dez holdouts.
7. Nenhum holdout antes do congelamento dos limiares.
8. Nenhuma seed, família, estrato ou lote será substituído.
9. Nenhuma mudança de gate após os dados.
10. Código, seeds, dependências e limiares serão congelados por hash.
