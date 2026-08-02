# ARARA From Zero — Pré-registro M10 Earliest Fraction at 8σ

**Versão:** M10.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** curva emparelhada de informação temporal em SNR final fixo.

---

## 1. Pergunta pequena

Com amplitude final fixa em \(8\sigma\), qual é a primeira fração do evento que satisfaz o contrato: \(t_{25}\), \(t_{50}\), \(t_{75}\) ou \(t_{100}\)?

---

## 2. Variável alterada

\[
f\in\{0.25,0.50,0.75,1.00\}.
\]

Todo o restante permanece congelado.

---

## 3. Elementos mantidos

- amplitude final:
\[
A/\sigma_0=8;
\]
- mesmo gerador de campo;
- mesmas quatro formas;
- contextos clean e concurrent;
- mesmas cinco famílias negativas;
- mesmo SBW;
- onset verdadeiro;
- template processado exato;
- uma hipótese por curva;
- FPR por família.

Seeds novas:

- desenvolvimento: `2026080501`;
- holdout: `2026080502`;
- bootstrap: `2026080503`.

---

## 4. Emparelhamento

O mesmo campo, sinal, ruído, onset, duração, forma e artefato será avaliado nas quatro frações.

Para cada fração:

\[
t_f=\min\{k:s_k\geq fA\}.
\]

O score usa:

\[
[\tau,t_f].
\]

---

## 5. Desenvolvimento

- 1.000 campos-base por forma/contexto;
- quatro frações por campo;
- 2.000 negativos por família;
- um limiar independente por fração;
- no máximo 0,5% de alertas em cada família negativa.

---

## 6. Holdout

- 2.500 campos por forma/contexto;
- quatro frações por campo;
- 5.000 negativos por família;
- 20 lotes;
- 125 positivos por estrato em cada lote;
- 250 negativos por família em cada lote.

---

## 7. Previsão anterior aos resultados

\[
R(0.25)\in[0.01,0.08],
\]

\[
R(0.50)\in[0.15,0.35],
\]

\[
R(0.75)\in[0.50,0.70],
\]

\[
R(1.00)\in[0.70,0.82].
\]

Previsão principal:

> A primeira fração aprovada será \(t_{75}\).

Também se prevê:

1. recall pontual não decrescente;
2. logística terá maior recall;
3. exponencial terá menor recall;
4. \(t_{100}\) replicará aproximadamente o resultado de 8σ do M9;
5. ramp ou bump determinará os limiares tardios.

---

## 8. Vitória de uma fração

Uma fração passa somente se:

1. Em cada família negativa:
\[
FPR_{\mathrm{upper}}^{95\%}\leq0.01.
\]

2. Recall global:
\[
R_{\mathrm{lower}}^{95\%}\geq0.60.
\]

3. Pelo menos seis dos oito estratos:
\[
R_{h,\mathrm{lower}}^{95\%}\geq0.50.
\]

4. Pelo menos 15 dos 20 lotes:
\[
R_{\mathrm{batch}}\geq0.55.
\]

---

## 9. Vitória do M10

M10 passa como mapeamento se:

- pelo menos uma fração passa;
- a curva pontual não possui queda maior que 0,02 entre frações adjacentes.

Sucesso de janela antecipada exige adicionalmente:

\[
f_{\min}\leq0.75.
\]

A previsão “primeira fração = 0,75” será avaliada separadamente.

---

## 10. Falha forte

M10 falha fortemente se nenhuma fração passa.

---

## 11. Inconclusivo

Se apenas \(t_{100}\) passar, o mapeamento é válido, mas a janela antecipada falha. O resultado operacional será classificado como:

`PASS_MAPPING_ONLY`.

---

## 12. Regras contra puxadinho

1. Nenhuma fração adicionada após o desenvolvimento.
2. Nenhuma fração removida.
3. Nenhuma exclusão de forma, contexto, seed ou lote.
4. Nenhuma alteração após abrir o holdout.
5. Limiares calibrados apenas nos negativos.
6. Código e dependências congelados por hash.
7. Bug pós-holdout invalida a execução.
8. Resultado negativo preservado.
