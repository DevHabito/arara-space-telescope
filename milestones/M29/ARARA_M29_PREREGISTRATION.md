# ARARA From Zero — Pré-registro M29 Reference-Nuisance Projected Partial-t

**Versão:** M29.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** comparação prospectiva e pareada entre o baseline \(L=8\) do M28 e uma estatística com projeção de nuisance.

## 1. Pergunta pequena

Mantendo onset, endpoint, forma, duração e janela de oito cadências exatos, uma estatística t parcial que remove componentes de nuisance disponíveis nas estrelas de referência melhora materialmente o recall e satisfaz o contrato?

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

O baseline será exatamente o matched filter não centrado do M28 em oito cadências:

\[
Z_8=
\frac{r^\top h}{\lVert h\rVert_2}.
\]

Nenhum parâmetro do baseline será alterado.

## 4. Nuisance operacional

O candidato utilizará, na mesma janela de oito cadências, a matriz:

\[
B=
\begin{bmatrix}
\mathbf 1 & \mathbf t & \mathbf q
\end{bmatrix},
\]

onde:

- \(\mathbf 1\): constante;
- \(\mathbf t\): rampa linear centrada, com valores igualmente espaçados entre -1 e 1;
- \(\mathbf q\): modo comum mediano das estrelas de referência, normalizado e submetido ao mesmo whitening AR(1) do residual do alvo.

A coluna \(\mathbf q\) é observável operacionalmente e contém a forma temporal efetivamente vista nas referências, incluindo degraus, rampas, bumps e oscilações compartilhadas.

Nenhuma informação da classe negativa ou do onset do artefato é usada para construir \(B\).

## 5. Projeção

Seja:

\[
P_\perp=I-BB^+,
\]

onde \(B^+\) é a pseudoinversa de Moore–Penrose.

Definem-se:

\[
r_\perp=P_\perp r,
\qquad
h_\perp=P_\perp h.
\]

O rank de \(B\) será calculado por curva.

## 6. Score candidato

A correlação parcial é:

\[
\rho_\perp=
\frac{r_\perp^\top h_\perp}
{\lVert r_\perp\rVert_2\lVert h_\perp\rVert_2}.
\]

O score unilateral será:

\[
T_\perp=
\rho_\perp
\sqrt{
\frac{\nu}
{1-\rho_\perp^2}
},
\]

com:

\[
\nu=8-\operatorname{rank}(B)-1.
\]

Se ocorrer qualquer condição abaixo, o score será zero:

- \(\nu<1\);
- norma projetada do residual ou template \(\leq10^{-12}\);
- \(\rho_\perp\leq0\).

Correlação numericamente unitária produz score infinito, preservado até a calibração.

## 7. Pareamento

Cada curva será gerada uma única vez.

Do mesmo residual e do mesmo template serão calculados:

- `baseline8`;
- `projected_t8`.

Assim, as diferenças não serão confundidas por seed, ruído, forma, onset ou artefato.

## 8. Calibração

Antes dos holdouts serão gerados:

\[
50\,000
\]

negativos por cada uma das cinco famílias.

Cada curva produzirá os dois scores pareados.

Cada score terá limiar próprio, calibrado para FPR empírico máximo de 0,5% por família.

Root seed:

`2026082401`.

## 9. Dez holdouts

Cada holdout terá:

- 2.500 positivos por cada um dos oito estratos;
- 5.000 negativos por família;
- 20 lotes;
- os dois scores calculados nas mesmas curvas;
- 10.000 réplicas de bootstrap.

Root seeds:

- holdouts: `2026082402`;
- bootstrap agregado: `2026082403`;
- bootstrap pareado da diferença: `2026082404`.

## 10. Convenção de confiança

Todos os gates usam limites unilaterais de 95%:

- inferior: quantil 0,05;
- superior: quantil 0,95.

Quando mostrados conjuntamente, correspondem ao intervalo central de 90%.

## 11. Passe operacional por holdout

Para cada score, um holdout passa somente se:

1. cada família negativa:
\[
FPR_{\mathrm{upper,unilateral}}^{95\%}\leq0.01;
\]

2. recall global:
\[
R_{\mathrm{lower,unilateral}}^{95\%}\geq0.60;
\]

3. pelo menos 6/8 estratos têm limite inferior unilateral \(\geq0.50\);

4. pelo menos 15/20 lotes têm recall \(\geq0.55\).

## 12. Passe operacional agregado do candidato

`projected_t8` passa operacionalmente se:

1. pelo menos 8/10 holdouts passam;
2. limite inferior agregado unilateral de 95% \(\geq0.60\);
3. pelo menos 9/10 holdouts controlam FPR;
4. nenhuma família ultrapassa limite superior de FPR de 1,5%.

## 13. Gate de superioridade pareada

A diferença primária será:

\[
\Delta R
=
R_{\mathrm{projected}}
-
R_{\mathrm{baseline}}.
\]

O ganho material passa somente se:

1. limite inferior unilateral de 95% da diferença hierárquica pareada:
\[
\Delta R_{\mathrm{lower}}\geq0.10;
\]

2. o candidato supera o baseline por pelo menos 0,08 em pelo menos 8/10 holdouts.

## 14. Veredito global

### Candidato aprovado

`PASS_NUISANCE_PROJECTED_CANDIDATE`

se o candidato passa o contrato operacional e o gate de superioridade.

Esse resultado ainda exigirá confirmação independente no M30.

### Ganho parcial

`PARTIAL_GAIN_NOT_OPERATIONAL`

se:

- o limite inferior da diferença é pelo menos 0,10;
- mas o candidato não passa o contrato operacional.

### Falha forte

`STRONG_FAIL_NUISANCE_PROJECTION`

se qualquer ocorrer:

- limite superior unilateral de 95% da diferença \(\leq0\);
- limite superior agregado do recall candidato \(\leq0.30\);
- violação extrema de FPR.

### Inconclusivo

Qualquer resultado intermediário será:

`INCONCLUSIVE_NUISANCE_PROJECTION`.

## 15. Diagnósticos congelados

Serão reportados sem alterar gates:

- rank do nuisance por família e estrato;
- fração de templates degenerados;
- limiares e famílias determinantes;
- AUROC e AP;
- correlação dos scores;
- detecções exclusivas de cada método;
- recall por forma e contexto.

## 16. Previsão anterior aos dados

Prevê-se que a projeção reduza a dominância de `shared_step`, mas que oito amostras e poucos graus de liberdade ainda impeçam o contrato completo.

Faixas previstas:

\[
R_{\mathrm{baseline}}\in[0.27,0.34],
\]

\[
R_{\mathrm{projected}}\in[0.45,0.60],
\]

\[
\Delta R\in[0.15,0.30].
\]

Prevê-se:

- FPR robusto nos dois métodos;
- ganho material pareado;
- 0–5 holdouts operacionais aprovados pelo candidato;
- veredito:

`PARTIAL_GAIN_NOT_OPERATIONAL`.

Não se prevê qual família determinará o novo limiar.

## 17. Limite da interpretação

M29 testa uma única estatística e uma única janela.

Um fracasso não refuta toda projeção de nuisance. Um passe não retira os oráculos de onset, endpoint, forma ou duração.

## 18. Regras contra puxadinho

1. Exatamente dois scores.
2. Exatamente três colunas de nuisance.
3. Exatamente oito cadências.
4. Exatamente 50.000 negativos por família.
5. Exatamente dez holdouts.
6. Mesmas curvas para os dois scores.
7. Limiar próprio para cada score.
8. Nenhum holdout antes do congelamento.
9. Nenhuma coluna, janela, regularização ou score novo após os dados.
10. Nenhuma seed, família, estrato ou lote será excluído.
11. Código, seeds, limiares e dependências serão congelados por hash.
