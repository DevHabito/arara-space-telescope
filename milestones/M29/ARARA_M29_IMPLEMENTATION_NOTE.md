# ARARA-M29 — Nota de implementação congelada

**Versão:** 29.0  
**Estado:** congelada antes da calibração.

## 1. Compatibilidade com o baseline

`baseline8` usa exatamente a equação e a janela do comprimento 8 do M28.

Um teste unitário compara as duas implementações numericamente.

## 2. Modo comum de referência

A normalização, estimação de beta e whitening repetem exatamente o SBW congelado.

O modo comum é:

\[
q_k=\operatorname{mediana}_{j\in\mathrm{referências}}x_{jk}.
\]

Ele é centrado pela mediana do baseline e transformado para o espaço whitened:

\[
q'_0=\frac{q_0-\widetilde q_{\rm base}}{\widehat\sigma_e},
\]

\[
q'_k=
\frac{
(q_k-\widetilde q_{\rm base})
-\widehat\phi(q_{k-1}-\widetilde q_{\rm base})
}
{\widehat\sigma_e}.
\]

Essa coluna não contém o sinal injetado apenas no alvo.

## 3. Projeção batelada

Para cada curva, a matriz \(B\) tem forma \(8\times3\).

A pseudoinversa e o rank são calculados em lote. Não há regularização ajustável. A tolerância fixa de rank é:

`1e-10`.

## 4. Bootstrap pareado

As quatro categorias de detecção são preservadas por holdout e estrato:

- nenhum;
- somente candidato;
- somente baseline;
- ambos.

O bootstrap hierárquico:

1. reamostra holdouts;
2. dentro de cada holdout selecionado, reamostra as quatro categorias por estrato;
3. calcula a diferença candidato menos baseline.

## 5. Escopo

O modo comum das referências é uma nuisance operacional, não uma variável latente verdadeira. M29 não utiliza a família do artefato nem seu onset.
