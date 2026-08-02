# ARARA From Zero — Pré-registro M14 Refined SNR Threshold at t50

**Versão:** M14.0  
**Estado:** congelado antes da implementação e dos dados

## 1. Pergunta pequena

Com janela fixada em \(t_{50}\), algum nível abaixo de 12σ satisfaz o contrato?

## 2. Grade congelada

\[
A/\sigma_0 \in \{10.5,11.0,11.5,12.0\}.
\]

Os campos são emparelhados entre níveis. Apenas a amplitude final muda.

## 3. Elementos mantidos

- janela \(t_{50}\);
- gerador e ruído anteriores;
- SBW;
- onset e template exatos;
- uma hipótese por curva;
- FPR por família;
- oito estratos positivos;
- cinco famílias negativas.

Seeds:

- desenvolvimento: `2026080901`;
- holdout: `2026080902`;
- bootstrap: `2026080903`.

## 4. Previsão anterior aos resultados

\[
R(10.5)\in[0.46,0.53],
\]

\[
R(11.0)\in[0.51,0.58],
\]

\[
R(11.5)\in[0.56,0.63],
\]

\[
R(12.0)\in[0.61,0.67].
\]

Previsão principal:

> O primeiro nível aprovado continuará sendo \(12\sigma\).

## 5. Vitória de um nível

Um nível passa se:

1. FPR superior de 95% menor ou igual a 1% em cada família;
2. limite inferior global de recall maior ou igual a 60%;
3. pelo menos seis de oito estratos com limite inferior maior ou igual a 50%;
4. pelo menos 15 de 20 lotes com recall maior ou igual a 55%.

## 6. Vitória do M14

M14 passa se pelo menos um nível passa e a curva pontual não cai mais de 0,02 entre níveis adjacentes.

O menor nível aprovado será o requisito refinado provisório em \(t_{50}\).

## 7. Falha forte

M14 falha fortemente se nenhum nível passa.

## 8. Regras contra puxadinho

- nenhum nível será adicionado ou removido;
- nenhuma alteração após abrir o holdout;
- nenhuma exclusão de forma, contexto, seed ou lote;
- limiar calibrado somente nos negativos;
- código e dependências congelados por hash;
- resultado negativo preservado.
