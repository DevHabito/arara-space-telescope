# ARARA From Zero — Pré-registro M33 Hinge-versus-Permuted-Onset Association Control

**Versão:** M33.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** controle de associação curva–onset para interpretar o passe de detecção do M32.

## 1. Pergunta pequena

O onset hinge contém informação específica da curva que melhora a detecção, ou o desempenho do M32 é explicado apenas pela distribuição marginal dos onsets estimados e pela baixa sensibilidade do downstream ao onset?

## 2. Métodos pareados

Cada curva produzirá três scores:

1. `exact_reference_projected8`  
   usa o onset verdadeiro;

2. `hinge_reference_projected8`  
   usa o onset hinge estimado na própria curva;

3. `permuted_hinge_reference_projected8`  
   usa um onset hinge estimado em outra curva do mesmo grupo.

O downstream, endpoint \(t_{50}\), forma, duração, normalização e projeção permanecem idênticos ao M32.

## 3. Permutação congelada

A permutação será aplicada separadamente:

- dentro de cada estrato positivo e lote;
- dentro de cada família negativa e lote;
- dentro de cada família de calibração e lote.

Para cada grupo com \(n>1\):

1. gerar uma permutação aleatória;
2. rejeitar e sortear novamente se houver qualquer ponto fixo;
3. usar a primeira permutação sem pontos fixos.

Assim:

- o multiconjunto de onsets permanece exatamente igual;
- nenhum onset permanece ligado à própria curva;
- não há mistura entre estratos, famílias ou lotes.

A permutação usa RNG dedicado e seeds congeladas.

## 4. Condição fixa

\[
A/\sigma_0=13.75,\qquad f=0.50,\qquad L=8.
\]

Permanecem oraculares:

- endpoint \(t_{50}\);
- forma;
- duração;
- parâmetros do template.

## 5. Estimador e downstream

O onset hinge é importado diretamente do M25/M32.

O score é:

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

Nenhuma equação será alterada.

## 6. Calibração

Serão gerados:

\[
50\,000
\]

negativos por família.

Cada método terá limiar próprio calibrado para FPR empírico máximo de 0,5% por família.

Root seeds:

- curvas de calibração: `2026082801`;
- permutações de calibração: `2026082802`.

## 7. Dez holdouts

Cada holdout terá:

- 2.500 positivos por estrato;
- 5.000 negativos por família;
- 20 lotes;
- os três métodos nas mesmas curvas;
- 10.000 réplicas de bootstrap.

Root seeds:

- curvas dos holdouts: `2026082803`;
- permutações dos holdouts: `2026082804`;
- bootstrap agregado: `2026082805`;
- bootstrap hinge−permutado: `2026082806`.

## 8. Convenção de confiança

Os gates usam limites unilaterais de 95%:

- inferior: quantil 0,05;
- superior: quantil 0,95.

Quando apresentados juntos, correspondem ao intervalo central de 90%.

## 9. Validade dos controles

O teste é interpretável somente se:

### Controle exato

- pelo menos 8/10 holdouts passam;
- limite inferior agregado \(\geq0.60\);
- FPR robusto.

### Controle hinge

- pelo menos 8/10 holdouts passam;
- limite inferior agregado \(\geq0.60\);
- FPR robusto.

Falha de qualquer controle produz:

`INVALID_M33_CONTROL_FAILURE`.

## 10. Gate de informação específica da curva

Define-se:

\[
\Delta_{\rm assoc}
=
R_{\rm hinge}
-
R_{\rm permutado}.
\]

Existe ganho material de associação somente se:

1. limite inferior unilateral agregado:
\[
\Delta_{\rm assoc,lower}\geq0.02;
\]

2. hinge supera permutado por pelo menos 0,015 em pelo menos 8/10 holdouts.

## 11. Gate de equivalência operacional

Hinge e permutado serão considerados operacionalmente equivalentes se:

\[
-0.02
\leq
\Delta_{\rm assoc,lower}
\]

e

\[
\Delta_{\rm assoc,upper}
\leq
+0.02.
\]

Esse é um teste de equivalência por margem de dois pontos percentuais. Significância estatística menor que essa margem não será promovida como informação operacional relevante.

## 12. Gate operacional do permutado

O permutado passa agregado se:

1. pelo menos 8/10 holdouts passam;
2. limite inferior agregado \(\geq0.60\);
3. pelo menos 9/10 holdouts controlam FPR;
4. nenhuma violação extrema de FPR.

## 13. Veredito

### Informação específica confirmada

`PASS_CURVE_SPECIFIC_ONSET_INFORMATION`

se:

- controles válidos;
- hinge passa o gate de associação material.

### Distribuição marginal suficiente

`ONSET_DISTRIBUTION_ONLY`

se:

- controles válidos;
- permutado passa operacionalmente;
- equivalência operacional é demonstrada.

### Hinge não é melhor

`STRONG_FAIL_HINGE_ASSOCIATION`

se:

- controles válidos;
- limite superior unilateral de 95% de \(\Delta_{\rm assoc}\leq0\).

### Inconclusivo

`INCONCLUSIVE_HINGE_ASSOCIATION`

nos demais casos.

### Precedência dos vereditos

A ordem congelada é:

1. controle inválido;
2. informação específica confirmada;
3. distribuição marginal suficiente;
4. falha forte de associação;
5. inconclusivo.

Assim, uma diferença estatisticamente negativa, mas inteiramente contida na margem operacional de equivalência de ±0,02, será classificada como `ONSET_DISTRIBUTION_ONLY`, não como falha forte.

## 14. Diagnósticos congelados

Sem alterar gates:

- recall por estrato;
- matrizes pareadas hinge versus permutado;
- acurácia temporal de ambos os onsets atribuídos;
- mediana e erro absoluto;
- correlação de scores;
- retenção de energia;
- limiares e famílias determinantes;
- FPR por família.

## 15. Previsão antes dos dados

Prevê-se:

\[
R_{\rm exact}\in[0.75,0.85],
\]

\[
R_{\rm hinge}\in[0.74,0.79],
\]

\[
R_{\rm perm}\in[0.73,0.79],
\]

\[
\Delta_{\rm assoc}\in[-0.01,+0.01].
\]

Prevê-se:

- exato e hinge válidos;
- permutado operacional em 8–10 holdouts;
- equivalência dentro de \(\pm0.02\);
- acurácia temporal do permutado semelhante ou inferior à do hinge;
- veredito:

`ONSET_DISTRIBUTION_ONLY`.

## 16. Interpretação permitida

Se `ONSET_DISTRIBUTION_ONLY`:

> o passe de detecção do M32 não valida o estimador hinge como fonte de informação curva-específica; o downstream funciona principalmente porque tolera uma ampla distribuição de onsets plausíveis.

Se `PASS_CURVE_SPECIFIC_ONSET_INFORMATION`:

> o hinge contém informação temporal útil para a detecção, mesmo sem localizar o onset com precisão física.

## 17. Regras contra puxadinho

1. Exatamente três métodos.
2. Mesmo conjunto de onsets hinge no método hinge e no permutado.
3. Permutação sem pontos fixos.
4. Permutação somente dentro do grupo.
5. Exatamente 50.000 negativos por família.
6. Exatamente dez holdouts.
7. Limiar próprio por método.
8. Nenhum holdout antes do congelamento.
9. Nenhuma seed, família, estrato ou lote será substituído.
10. Nenhum gate será alterado após os dados.
11. Código, seeds, dependências e limiares serão congelados por hash.
