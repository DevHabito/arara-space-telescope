# ARARA From Zero — Pré-registro M30 Reference-Common-Mode-Only Projection

**Versão:** M30.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** controle prospectivo do M29, removendo somente o modo comum observado nas referências.

## 1. Pergunta pequena

Mantendo onset, endpoint, forma, duração e janela de oito cadências exatos, projetar somente o modo comum das estrelas de referência reduz a cauda de `shared_step` sem apagar o sinal target-local?

## 2. Condição fixa

\[
A/\sigma_0=13.75,
\qquad
f=0.50,
\qquad
L=8.
\]

Continuam como oráculos:

- onset verdadeiro;
- endpoint verdadeiro \(t_{50}\);
- forma e duração exatas.

## 3. Baseline congelado

O baseline será exatamente o matched filter não centrado de oito cadências:

\[
Z_8=
\frac{r^\top h}{\lVert h\rVert_2}.
\]

## 4. Única nuisance

Na mesma janela de oito cadências, será usado apenas o modo comum processado das estrelas de referência:

\[
q.
\]

Esse modo é construído operacionalmente:

1. normalizar cada estrela pelo baseline;
2. calcular a mediana das referências;
3. centralizar pela mediana do baseline das referências;
4. aplicar o mesmo whitening AR(1) usado no residual do alvo.

Não serão incluídas:

- constante;
- rampa;
- polinômio;
- família verdadeira do artefato;
- onset verdadeiro do artefato.

## 5. Projeção congelada

Para cada curva:

\[
P_{q\perp}
=
I-q(q^\top q)^+q^\top.
\]

Em forma escalar:

\[
P_{q\perp}v
=
v-q\frac{q^\top v}{q^\top q}.
\]

Se:

\[
q^\top q\leq10^{-12},
\]

a projeção será a identidade.

## 6. Score candidato

Definem-se:

\[
r_\perp=P_{q\perp}r,
\qquad
h_\perp=P_{q\perp}h.
\]

O score será:

\[
Z_{q\perp}
=
\frac{r_\perp^\top h_\perp}
{\lVert h_\perp\rVert_2}.
\]

Se:

\[
\lVert h_\perp\rVert_2\leq10^{-12},
\]

o score será zero.

Não haverá centralização adicional, normalização pela norma do residual ou transformação t.

## 7. Pareamento

Cada curva será gerada uma única vez.

Nas mesmas curvas serão calculados:

- `baseline8`;
- `reference_projected8`.

Cada método terá limiar próprio.

## 8. Calibração

Antes dos holdouts serão gerados:

\[
50\,000
\]

negativos por cada uma das cinco famílias.

Cada curva produzirá os dois scores pareados.

Os limiares serão calibrados para FPR empírico máximo de 0,5% por família e congelados.

Root seed:

`2026082501`.

## 9. Dez holdouts

Cada holdout terá:

- 2.500 positivos por cada um dos oito estratos;
- 5.000 negativos por família;
- 20 lotes;
- os dois scores calculados nas mesmas curvas;
- 10.000 réplicas de bootstrap.

Root seeds:

- holdouts: `2026082502`;
- bootstrap agregado: `2026082503`;
- bootstrap pareado da diferença: `2026082504`.

## 10. Convenção de confiança

Todos os gates usam limites unilaterais de 95%:

- inferior: quantil 0,05;
- superior: quantil 0,95.

Quando exibidos conjuntamente, correspondem numericamente ao intervalo central de 90%.

## 11. Passe operacional por holdout

Um método passa num holdout somente se:

1. cada família negativa:
\[
FPR_{\mathrm{upper,unilateral}}^{95\%}\leq0.01;
\]

2. recall global:
\[
R_{\mathrm{lower,unilateral}}^{95\%}\geq0.60;
\]

3. pelo menos 6/8 estratos têm limite inferior unilateral:
\[
R_h\geq0.50;
\]

4. pelo menos 15/20 lotes:
\[
R_{\mathrm{batch}}\geq0.55.
\]

## 12. Passe operacional agregado do candidato

`reference_projected8` passa operacionalmente se:

1. pelo menos 8/10 holdouts passam;
2. limite inferior agregado unilateral de 95% \(\geq0.60\);
3. pelo menos 9/10 holdouts controlam FPR;
4. nenhuma família ultrapassa limite superior de FPR de 1,5%.

## 13. Gate de superioridade pareada

\[
\Delta R
=
R_{\mathrm{reference\ projected}}
-
R_{\mathrm{baseline}}.
\]

O ganho material passa somente se:

1. limite inferior unilateral de 95%:
\[
\Delta R_{\mathrm{lower}}\geq0.10;
\]

2. o candidato supera o baseline por pelo menos 0,08 em pelo menos 8/10 holdouts.

## 14. Veredito global

### Candidato aprovado

`PASS_REFERENCE_PROJECTION_CANDIDATE`

se o candidato passa o contrato operacional e o gate de superioridade.

Esse resultado exigirá confirmação independente posterior.

### Ganho parcial

`PARTIAL_GAIN_NOT_OPERATIONAL`

se:

- \(\Delta R_{\mathrm{lower}}\geq0.10\);
- mas o candidato não passa operacionalmente.

### Falha forte

`STRONG_FAIL_REFERENCE_PROJECTION`

se qualquer ocorrer:

- \(\Delta R_{\mathrm{upper}}\leq0\);
- limite superior agregado do recall candidato \(\leq0.30\);
- violação extrema de FPR.

### Inconclusivo

Qualquer resultado intermediário será:

`INCONCLUSIVE_REFERENCE_PROJECTION`.

## 15. Diagnósticos congelados

Serão reportados sem alterar os gates:

- fração de curvas com modo comum degenerado;
- fração de templates degenerados após projeção;
- retenção de energia:
\[
E_h=
\frac{\lVert h_\perp\rVert_2^2}
{\lVert h\rVert_2^2};
\]
- limiar e família determinante;
- recall por estrato;
- AUROC e AP;
- correlação dos scores;
- detecções exclusivas de cada método.

## 16. Previsão anterior aos dados

A projeção exclusiva do modo comum deve preservar muito mais sinal do que o M29 e reduzir a dominância de `shared_step`.

Prevê-se:

\[
R_{\mathrm{baseline}}\in[0.27,0.34],
\]

\[
R_{\mathrm{candidate}}\in[0.48,0.68],
\]

\[
\Delta R\in[0.18,0.38].
\]

Prevê-se ainda:

- FPR robusto nos dois métodos;
- retenção mediana de energia do template acima de 0,70;
- ganho material pareado;
- entre 3 e 10 holdouts operacionais aprovados pelo candidato.

Veredito previsto:

`INCONCLUSIVE_REFERENCE_PROJECTION`.

A escolha de `INCONCLUSIVE` é deliberadamente conservadora: prevê-se ganho grande, mas não se pré-afirma que o limite inferior agregado ultrapassará 0,60 e que 8/10 holdouts passarão simultaneamente.

## 17. Interpretação

- passe completo: o modo comum das referências é uma nuisance útil, e o candidato segue para confirmação independente;
- ganho parcial: melhora real, mas ainda insuficiente;
- falha forte: projeção direta do modo comum também é inadequada nessa janela;
- inconclusivo: evidência intermediária sem promoção.

## 18. Regras contra puxadinho

1. Exatamente dois scores.
2. Exatamente uma coluna de nuisance.
3. Exatamente oito cadências.
4. Exatamente 50.000 negativos por família.
5. Exatamente dez holdouts.
6. Mesmas curvas para os dois scores.
7. Limiar próprio para cada score.
8. Nenhum holdout antes do congelamento.
9. Nenhuma constante, rampa, regularização ou transformação nova após os dados.
10. Nenhuma seed, família, estrato ou lote será excluído.
11. Código, seeds, limiares e dependências serão congelados por hash.
