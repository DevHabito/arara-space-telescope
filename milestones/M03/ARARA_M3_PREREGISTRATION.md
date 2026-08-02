# ARARA From Zero — Pré-registro M3 Subtract-Before-Whiten

**Versão:** M3.0  
**Estado:** congelado antes da implementação e da geração de dados  
**Dependência:** o gerador físico-sintético é idêntico ao M2, mas usa seeds inteiramente novas.

---

## 1. Pergunta pequena

Ao estimar uma perturbação comum a partir de oito estrelas de referência, subtrair o common-mode antes do branqueamento AR(1) melhora o recall precoce em relação a branquear cada estrela antes da subtração?

---

## 2. Motivação matemática

No M2, cada estrela foi transformada por:

\[
z_{j,k}
\propto
(1-\widehat{\phi}_jL)y_{j,k}.
\]

Para uma componente compartilhada \(a_jc_k\), isso produz:

\[
(1-\widehat{\phi}_jL)a_jc_k.
\]

Como \(\widehat{\phi}_j\) varia entre estrelas, a componente comum deixa de possuir exatamente a mesma forma em todas elas. A mediana posterior pode não representar o componente transformado do alvo.

A hipótese M3 é que a ordem correta para o modelo:

\[
y_{j,k}=a_jc_k+s_{j,k}+\epsilon_{j,k}
\]

é:

\[
\text{estimar }c
\rightarrow
\text{subtrair }c
\rightarrow
\text{branquear o resíduo}.
\]

---

## 3. Detectores comparados

### WBS — Whiten Before Subtract

É exatamente o método M2:

1. normalizar e branquear cada estrela;
2. calcular mediana das referências branqueadas;
3. estimar beta na baseline;
4. subtrair.

### SBW — Subtract Before Whiten

1. centralizar e escalar robustamente cada estrela, sem filtro AR:
   \[
   x_{j,k}
   =
   \frac{y_{j,k}-\widehat\mu_j}{\widehat\sigma_j}.
   \]

2. estimar common-mode:
   \[
   q_k=\operatorname{median}_{j=1,\ldots,8}x_{j,k}.
   \]

3. estimar na baseline:
   \[
   \widehat\beta
   =
   \frac{\operatorname{Cov}(x_0,q)}
   {\operatorname{Var}(q)},
   \qquad
   0\leq\widehat\beta\leq3.
   \]

4. formar:
   \[
   e_k=x_{0,k}-\widehat\beta q_k.
   \]

5. estimar mediana, MAD e AR(1) do resíduo somente na baseline;

6. branquear:
   \[
   r_k
   =
   \frac{
   (e_k-\widehat\mu_e)
   -
   \widehat\phi_e(e_{k-1}-\widehat\mu_e)
   }{\widehat\sigma_e}.
   \]

Os dois métodos usam o mesmo detector causal de inclinação e as mesmas janelas:

\[
w\in\{8,16,32\}.
\]

---

## 4. Dados

O modelo de campo, os oito estratos positivos, as cinco famílias negativas, amplitudes, ruídos, contaminação de uma referência e definição de \(t_{25}\) são idênticos ao pré-registro M2.

Não serão reutilizadas curvas M2.

Seeds:

- desenvolvimento: `2026072901`;
- holdout: `2026072902`;
- bootstrap: `2026072903`.

---

## 5. Previsão anterior aos resultados

1. SBW terá ganho absoluto de recall precoce entre 0,10 e 0,30 sobre WBS.
2. SBW terá limiar de desenvolvimento menor que WBS.
3. O maior ganho aparecerá nos estratos concurrent.
4. Em clean, SBW não perderá mais de 0,03 de recall.
5. A família shared_oscillation continuará sendo a mais difícil, mas seu score residual mediano diminuirá.

A promoção exige ganho confirmado mínimo de 0,10.

---

## 6. Desenvolvimento

- 2.000 campos por estrato positivo;
- 2.000 por família negativa;
- limiar próprio para WBS e SBW;
- máximo de 0,5% de falsos alertas em cada família negativa;
- positivos não participam da seleção de limiar.

---

## 7. Holdout

- 5.000 campos por cada um dos oito estratos positivos;
- 5.000 por cada uma das cinco famílias negativas;
- 20 lotes independentes;
- 65.000 campos no total.

O holdout será aberto uma única vez após congelamento de código, testes, limiares e hashes.

---

## 8. Métrica primária

\[
\Delta R
=
R_{\mathrm{SBW}}
-
R_{\mathrm{WBS}}.
\]

Recall global usa peso igual entre os oito estratos.

Bootstrap emparelhado e estratificado:

- 10.000 réplicas;
- limites unilaterais de 95% pelos percentis 5% e 95%.

---

## 9. Não inferioridade clean

\[
\Delta R_{\mathrm{clean}}
=
R_{\mathrm{SBW,clean}}
-
R_{\mathrm{WBS,clean}}.
\]

Exigência:

\[
\Delta R_{\mathrm{clean,lower}}^{95\%}
\geq-0.03.
\]

---

## 10. Vitória

M3 passa somente se:

1. em toda família negativa SBW:
   \[
   FPR_{\mathrm{upper}}^{95\%}\leq0.01;
   \]

2. recall SBW:
   \[
   R_{\mathrm{SBW,lower}}^{95\%}\geq0.20;
   \]

3. ganho:
   \[
   \Delta R_{\mathrm{lower}}^{95\%}\geq0.10;
   \]

4. não inferioridade clean:
   \[
   \Delta R_{\mathrm{clean,lower}}^{95\%}\geq-0.03;
   \]

5. pelo menos 7 de 8 estratos possuem diferença pontual não negativa;

6. pelo menos 15 de 20 lotes possuem \(\Delta R>0\);

7. o limiar SBW de desenvolvimento é menor que o limiar WBS.

---

## 11. Falha forte

M3 é rejeitado nesta forma se:

- qualquer FPR SBW viola o limite; ou
- o limite superior de 95% do ganho é menor ou igual a zero; ou
- o limite superior clean é menor que \(-0.03\).

---

## 12. Inconclusivo

Resultados entre vitória e falha forte são inconclusivos.

Regra de engenharia:

> somente PASS promove.

---

## 13. Resultados secundários

- AUROC e AP;
- cruzamentos antes, durante e depois da janela precoce;
- erro de beta;
- limiar por família;
- score residual de shared_oscillation;
- tempo computacional.

Nenhum resultado secundário substitui os critérios primários.

---

## 14. Regras contra puxadinho

1. O holdout M2 não será consultado para ajuste.
2. O gerador M2 será reutilizado sem alteração e identificado por hash.
3. Nenhuma alteração após abertura do holdout.
4. Nenhuma família, seed ou lote será excluído.
5. Bug pré-holdout será registrado e corrigido.
6. Bug pós-holdout invalida a execução.
7. Resultado negativo permanece arquivado.
