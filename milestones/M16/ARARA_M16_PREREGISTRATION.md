# ARARA From Zero — Pré-registro M16 Calibration-Size Stability at 12σ, t50

**Versão:** M16.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** teste causal do efeito do tamanho da calibração negativa.

---

## 1. Pergunta pequena

A instabilidade observada em \(12\sigma\), \(t_{50}\), vem principalmente do uso de apenas 2.000 negativos por família para calibrar o limiar?

---

## 2. Condição científica fixa

\[
A/\sigma_0=12,
\qquad
f=0.50.
\]

São mantidos:

- o gerador sintético;
- as quatro formas positivas;
- os contextos clean e concurrent;
- as cinco famílias negativas;
- o preprocessing SBW;
- onset e template exatos;
- uma hipótese por curva;
- o contrato de falso alerta e recall.

---

## 3. Tamanhos de calibração

Serão comparados:

\[
n_{\mathrm{cal}}\in\{2\,000,\ 10\,000,\ 50\,000\}
\]

negativos por família.

---

## 4. Mundos independentes

Serão gerados três mundos prospectivos independentes.

Cada mundo terá:

1. um superpool de calibração com 50.000 scores negativos por família;
2. um holdout positivo com 2.500 curvas por cada um dos oito estratos;
3. um holdout negativo com 5.000 curvas por família;
4. 20 lotes de holdout.

Root seeds:

- mundos: `2026081101`;
- reamostragem de calibração: `2026081102`;
- bootstrap de recall: `2026081103`.

Todas as seeds filhas serão congeladas antes da geração.

---

## 5. Emparelhamento

Dentro de cada mundo:

- os três tamanhos usam o mesmo superpool;
- os três tamanhos usam o mesmo holdout;
- somente a amostra usada para calibrar o limiar muda.

Para cada tamanho serão feitas 100 reamostragens estratificadas com reposição, separadamente dentro de cada família negativa.

Total:

\[
3\text{ mundos}\times
3\text{ tamanhos}\times
100
=
900
\]

calibrações prospectivamente definidas.

---

## 6. Limiar

Em cada reamostragem e família:

\[
a=\left\lfloor0.005n_{\mathrm{cal}}\right\rfloor.
\]

O limiar familiar é o próximo número representável acima do \((a+1)\)-ésimo maior score.

O limiar global é:

\[
\theta=\max_j\theta_j.
\]

---

## 7. Avaliação de cada calibração

Cada limiar será aplicado ao holdout fixo daquele mundo.

Uma calibração passa somente se:

1. em cada família negativa:
\[
FPR_{\mathrm{upper}}^{95\%}\leq0.01;
\]

2. recall global:
\[
R_{\mathrm{lower}}^{95\%}\geq0.60;
\]

3. pelo menos seis dos oito estratos:
\[
R_{h,\mathrm{lower}}^{95\%}\geq0.50;
\]

4. pelo menos 15 dos 20 lotes:
\[
R_{\mathrm{batch}}\geq0.55.
\]

---

## 8. Métricas primárias

Para cada tamanho:

1. distribuição do limiar;
2. largura do intervalo central de 90%:
\[
W_n=Q_{0.95}(\theta)-Q_{0.05}(\theta);
\]

3. proporção de calibrações aprovadas;
4. distribuição do recall;
5. distribuição do limite inferior do recall;
6. proporção com FPR aprovado.

O resumo principal usa peso igual aos três mundos.

---

## 9. Hipótese “calibração insuficiente é a causa principal”

Essa hipótese passa somente se todos ocorrerem:

1. estabilização:
\[
\operatorname{mediana}_{mundos}
\frac{W_{50k}}{W_{2k}}
\leq0.50;
\]

2. resgate:
em pelo menos dois dos três mundos, pelo menos 80% das calibrações de 50k passam;

3. a proporção agregada de passe em 50k possui limite inferior binomial de 95% maior ou igual a 0,70;

4. a proporção agregada de passe em 2k é menor ou igual a 0,40.

Veredito:

`PASS_CALIBRATION_PRIMARY`.

---

## 10. Falha forte da hipótese

A hipótese falha fortemente se:

1. o limiar estabiliza:
\[
\operatorname{mediana}_{mundos}
\frac{W_{50k}}{W_{2k}}
\leq0.50;
\]

mas

2. a proporção agregada de passe em 50k é menor ou igual a 0,20;

3. o percentil 90 do limite inferior de recall em 50k permanece abaixo de 0,60.

Veredito:

`STRONG_FAIL_CALIBRATION_NOT_PRIMARY`.

---

## 11. Inconclusivo

Qualquer resultado intermediário será:

`INCONCLUSIVE`.

---

## 12. Previsão anterior aos resultados

Prevê-se:

1. redução forte da largura do limiar:
\[
W_{50k}/W_{2k}\leq0.40;
\]

2. proporção de passe menor ou igual a 20% nos três tamanhos;

3. recall mediano em 50k entre 0,50 e 0,56;

4. veredito:
`STRONG_FAIL_CALIBRATION_NOT_PRIMARY`.

Interpretação prevista:

> O conjunto de 2.000 negativos aumenta a variabilidade do limiar, mas o quantil verdadeiro exigido pelo FPR ainda deixa recall insuficiente em 12σ e t50.

---

## 13. Regras contra puxadinho

1. Exatamente três mundos.
2. Exatamente 100 reamostragens por tamanho e mundo.
3. Nenhum mundo será excluído.
4. Nenhuma família será excluída.
5. Nenhum tamanho será adicionado ou removido.
6. O mesmo holdout será usado entre tamanhos dentro do mundo.
7. Nenhuma alteração após gerar o primeiro superpool.
8. Bug pós-abertura invalida a execução.
9. Resultados individuais serão preservados.
10. Código, seeds e dependências serão congelados por hash.
