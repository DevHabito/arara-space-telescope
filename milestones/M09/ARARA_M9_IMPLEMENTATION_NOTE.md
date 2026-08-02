# ARARA-M9 — Nota de implementação congelada

**Versão:** 9.0  
**Estado:** congelada antes da geração de desenvolvimento e holdout.

## 1. Campo-base emparelhado

Cada forma/contexto gera uma única realização de campo-base:

\[
y^{(0)}_{j,k}
=
a_jc_k+\epsilon_{j,k}+u_{j,k},
\]

incluindo common-mode, ruído, impulso eventual em uma referência e artefato concurrent quando aplicável.

Para cada nível \(a\in\{4,6,8,10,12\}\):

\[
y^{(a)}_{0,k}
=
y^{(0)}_{0,k}
+
a\,\sigma_{0}\,f_k.
\]

As referências e todas as variáveis latentes permanecem idênticas entre níveis.

## 2. Unidade de amplitude

\(\sigma_0\) é o desvio-padrão estacionário do ruído individual do alvo:

\[
\sigma_0
=
\frac{\sigma_{\eta,0}}
{\sqrt{1-\phi_0^2}}.
\]

É a mesma unidade usada pelo gerador M2 original.

## 3. Janela

Todos os positivos são avaliados entre onset e a primeira chegada à amplitude final:

\[
[\tau,t_{100}].
\]

## 4. Negativos

Negativos são independentes dos positivos e recebem uma hipótese virtual por curva, como no M8. O mesmo limiar é usado para todos os níveis de SNR.

## 5. Bootstrap

Para cada nível:

- oito estratos com peso igual;
- 10.000 réplicas;
- limites nos percentis 5% e 95%.

## 6. Monotonicidade

A curva global pontual passa o gate de monotonicidade se:

\[
R(a_{i+1})-R(a_i)\geq-0.02
\]

para todos os níveis adjacentes.

## 7. Holdout

O arquivo `HOLDOUT_OPENED.json` será criado antes da geração. Uma segunda execução será recusada.
