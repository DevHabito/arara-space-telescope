# ARARA-M30 — Nota de implementação congelada

**Versão:** 30.0  
**Estado:** congelada antes da calibração.

## 1. Dependências

A normalização SBW, o modo comum processado das referências, o baseline \(L=8\) e os bootstraps pareados reutilizam implementações congeladas do M29.

## 2. Projeção de uma dimensão

Na janela de oito pontos, para qualquer vetor \(v\):

\[
v_\perp
=
v-q\frac{q^\top v}{q^\top q}.
\]

Quando \(q^\top q\leq10^{-12}\), usa-se \(v_\perp=v\).

Não há pseudoinversa matricial, regularização ajustável ou seleção de rank.

## 3. Retenção de energia

Para cada template:

\[
E_h=
\frac{\lVert h_\perp\rVert_2^2}
{\lVert h\rVert_2^2}.
\]

O valor é limitado numericamente ao intervalo \([0,1]\). Template original com norma nula recebe retenção zero e é marcado como degenerado.

## 4. Comparação pareada

Os dois métodos recebem exatamente o mesmo residual, template, endpoint e modo comum. As categorias pareadas são preservadas por holdout e estrato.

## 5. Escopo

O teste não estima onset, endpoint, forma ou duração. Ele testa apenas se remover a direção temporal observada nas referências melhora o downstream-oráculo de oito cadências.
