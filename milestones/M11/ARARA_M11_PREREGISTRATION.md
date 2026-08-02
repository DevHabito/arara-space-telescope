# ARARA From Zero — Pré-registro M11 SNR Threshold at t75

**Versão:** M11.0  
**Estado:** congelado antes da implementação e dos dados

## 1. Pergunta pequena

Com janela fixada em \(t_{75}\), qual é o menor SNR final entre 8σ e 10σ que satisfaz o contrato?

## 2. Grade congelada

\[
A/\sigma_0 \in \{8.0,8.5,9.0,9.5,10.0\}.
\]

Apenas a amplitude final muda. Os campos são emparelhados entre níveis.

## 3. Elementos mantidos

- janela \(t_{75}\);
- gerador, ruído e artefatos anteriores;
- SBW;
- onset e template exatos;
- uma hipótese por curva;
- FPR por família;
- oito estratos positivos;
- cinco famílias negativas.

Seeds:

- desenvolvimento: `2026080601`;
- holdout: `2026080602`;
- bootstrap: `2026080603`.

## 4. Previsão anterior aos resultados

\[
R(8.0)\in[0.55,0.62],
\]

\[
R(8.5)\in[0.61,0.69],
\]

\[
R(9.0)\in[0.66,0.74],
\]

\[
R(9.5)\in[0.70,0.79],
\]

\[
R(10.0)\in[0.74,0.83].
\]

Previsão principal:

> O primeiro nível aprovado será \(8.5\sigma\).

## 5. Vitória de um nível

Um nível passa se:

1. FPR superior de 95% menor ou igual a 1% em cada família;
2. limite inferior global de recall maior ou igual a 60%;
3. pelo menos seis de oito estratos com limite inferior maior ou igual a 50%;
4. pelo menos 15 de 20 lotes com recall maior ou igual a 55%.

## 6. Vitória do M11

M11 passa se pelo menos um nível passa e a curva pontual não cai mais de 0,02 entre níveis adjacentes.

O nível recomendado é o menor aprovado.

## 7. Falha forte

M11 falha fortemente se nenhum nível passa e o limite superior de recall em 10σ é menor ou igual a 50%.

## 8. Regras contra puxadinho

- nenhum nível será adicionado ou removido;
- nenhuma alteração após abrir o holdout;
- nenhuma exclusão de forma, contexto, seed ou lote;
- limiar calibrado somente nos negativos;
- resultado negativo será preservado.
