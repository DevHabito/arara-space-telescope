# ARARA-M25 — Nota de implementação congelada

**Versão:** 25.0  
**Estado:** congelada antes da calibração.

## 1. Separação em dados brutos

Com endpoint \(e\):

- seleção termina em \(e-9\);
- \(e-8\) é guarda;
- confirmação usa \(e-7,\ldots,e\).

O residual confirmado em \(e-7\) depende, pelo filtro AR(1), de \(y_{e-8}\), que é a guarda. Ele não depende de nenhuma amostra usada na seleção, cujo último ponto bruto é \(e-9\).

## 2. Estimador

A implementação reutiliza exatamente o hinge scan testado no M24, alterando somente o endpoint entregue ao scan para o fim da janela de seleção.

## 3. Confirmação

O score não é uma correlação t reotimizada. É um matched-filter unilateral padronizado sobre oito amostras fixas:

\[
Z=\frac{r^\top h}{\|h\|_2}.
\]

Não há intercepto, busca, maximização ou seleção na janela confirmatória.

## 4. Template

O onset de referência da representação sintética é usado apenas para transladar a forma relativa conhecida até \(\widehat\tau\). A decisão depende da forma/duração oráculo e do onset estimado, não do onset verdadeiro absoluto.

## 5. Calibração

O pipeline inteiro — hinge na seleção e matched filter na confirmação — é calibrado em 50.000 negativos por família antes dos holdouts.

## 6. Escopo

M25 mede se a separação temporal reduz o custo de seleção. O endpoint, a forma e a duração continuam como oráculos.
