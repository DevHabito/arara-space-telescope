# ARARA From Zero — Pré-registro M5 Oracle-Aligned Information Bound

**Versão:** M5.0  
**Estado:** congelado antes da implementação e da geração de dados  
**Natureza:** teste de limite condicional; não é detector operacional.

---

## 1. Pergunta pequena

Se o onset e a forma exata do sinal forem conhecidos por um oráculo, o segmento observado entre o onset e \(t_{25}\) contém evidência estatística suficiente para detectar a maioria dos eventos sob falso alerta controlado?

---

## 2. Por que este teste existe

O M4 procurou muitas combinações de onset, duração e forma. Essa busca elevou o limiar por múltiplas comparações.

O M5 remove essa dificuldade. Para cada positivo, ele usa:

- onset verdadeiro;
- \(t_{25}\) verdadeiro;
- contribuição exata do sinal depois do preprocessing SBW.

Assim, o M5 testa a informação disponível no segmento, não a capacidade de busca autônoma.

---

## 3. Dados

O modelo sintético é idêntico ao M2–M4, com novas seeds:

- desenvolvimento: `2026073101`;
- holdout: `2026073102`;
- bootstrap: `2026073103`.

São mantidos:

- oito estratos positivos;
- cinco famílias negativas;
- 65.000 campos no holdout;
- preprocessing SBW;
- ruído, common-mode e contaminação de referência anteriores.

Nenhuma curva antiga será reutilizada.

---

## 4. Template positivo exato

O evento começa após a baseline. Portanto, os parâmetros de baseline do SBW não dependem do evento.

Seja \(L_{\mathrm{SBW}}\) o operador linear induzido pelos parâmetros congelados da baseline. A contribuição processada do evento é:

\[
g_k=L_{\mathrm{SBW}}[s_{0,k}].
\]

Para cada positivo, o teste usa somente:

\[
k\in[\tau,t_{25}].
\]

O template \(g_k\) é exato para aquela curva.

---

## 5. Hipótese negativa alinhada

Uma curva negativa não possui evento verdadeiro. Para medir falso alerta sob uma única hipótese alinhada:

1. sorteia-se independentemente uma forma entre as quatro famílias;
2. sorteiam-se onset, duração e parâmetros nas mesmas distribuições dos positivos;
3. constrói-se uma injeção virtual de amplitude unitária;
4. aplica-se o mesmo operador SBW da baseline para obter o template processado;
5. calcula-se um único score no intervalo pseudo-onset até pseudo-\(t_{25}\).

A injeção virtual não é adicionada à observação negativa. Ela define somente a hipótese testada.

Isso mantém uma hipótese por curva, como nos positivos.

---

## 6. Estatística

No segmento alinhado, ajusta-se:

\[
r_k=\alpha+A g_k+e_k.
\]

Com correlação \(c\) entre observação e template centralizados:

\[
T=
\begin{cases}
c\sqrt{\frac{L-2}{1-c^2}},&c>0,\\
0,&c\leq0.
\end{cases}
\]

O score é calculado uma única vez em \(t_{25}\).

---

## 7. Desenvolvimento

- 2.000 curvas por estrato positivo;
- 2.000 por família negativa;
- limiar calculado apenas nos negativos;
- máximo de 0,5% de falsos alertas em cada família;
- limiar global igual ao máximo dos limiares familiares.

---

## 8. Holdout

- 5.000 por cada um dos oito estratos positivos;
- 5.000 por cada família negativa;
- 20 lotes independentes;
- 65.000 campos.

O holdout será aberto uma única vez.

---

## 9. Métrica primária

\[
R_{\mathrm{oracle}}
=
\frac{1}{8}\sum_h R_h.
\]

Intervalo global por bootstrap estratificado com 10.000 réplicas.

Recall por estrato usa limite inferior unilateral de Clopper–Pearson a 95%.

---

## 10. Previsão anterior aos resultados

A previsão é:

\[
0.40\leq R_{\mathrm{oracle}}\leq0.75.
\]

Espera-se:

1. maior recall em linear e logística;
2. menor recall em power-law e exponencial;
3. pequena diferença entre clean e concurrent após SBW;
4. limiar muito menor que o M4 por ausência de busca múltipla.

---

## 11. Vitória

O segmento até \(t_{25}\) será considerado informativo se todos ocorrerem:

1. em cada família negativa:
\[
FPR_{\mathrm{upper}}^{95\%}\leq0.01;
\]

2. recall global:
\[
R_{\mathrm{oracle,lower}}^{95\%}\geq0.60;
\]

3. pelo menos seis dos oito estratos:
\[
R_{h,\mathrm{lower}}^{95\%}\geq0.50;
\]

4. pelo menos 15 dos 20 lotes:
\[
R_{\mathrm{oracle,batch}}\geq0.55.
\]

---

## 12. Falha forte

O segmento será considerado insuficiente mesmo sob alinhamento-oráculo se:

- qualquer família negativa viola o FPR; ou
- o limite superior de 95% do recall global é:
\[
R_{\mathrm{oracle,upper}}^{95\%}\leq0.30.
\]

---

## 13. Inconclusivo

Resultados entre vitória e falha forte são inconclusivos.

---

## 14. Interpretação permitida

### Se passar

Existe informação suficiente até \(t_{25}\), mas o problema operacional está na busca, no controle de múltiplas hipóteses ou na modelagem de negativos.

### Se falhar fortemente

Mesmo com alinhamento e forma exatos, o contrato atual oferece informação insuficiente. Deve-se rever ao menos um destes elementos:

- amplitude;
- definição de \(t_{25}\);
- cadência;
- ruído;
- falso alerta;
- fonte de informação adicional.

---

## 15. Interpretação proibida

O M5 não pode ser apresentado como detector implantável, porque usa informação verdadeira indisponível em operação.

---

## 16. Regras contra puxadinho

1. Uma hipótese por curva.
2. Nenhuma busca sobre onset em negativos ou positivos.
3. Nenhum ajuste após holdout.
4. Nenhuma exclusão de família, seed ou lote.
5. O operador SBW será calculado apenas da baseline.
6. Bug pré-holdout será registrado.
7. Bug pós-holdout invalida a execução.
8. Resultado negativo será preservado.
