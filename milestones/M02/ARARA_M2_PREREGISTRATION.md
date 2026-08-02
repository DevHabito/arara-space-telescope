# ARARA From Zero — Pré-registro M2 Common-Mode

**Versão:** M2.0  
**Estado:** congelado antes da implementação e da geração de dados  
**Escopo:** detecção fotométrica multissérie; não inclui óptica, FLOCK, energia ou céu real.

---

## 1. Pergunta pequena

Em um campo sintético contendo um alvo e oito estrelas de referência observadas simultaneamente, a remoção causal de uma perturbação comum ao campo melhora o recall precoce de rises localizados no alvo, mantendo o falso alerta controlado em perturbações instrumentais compartilhadas?

---

## 2. Hipótese

Se um artefato afeta simultaneamente muitas estrelas, enquanto o evento astrofísico aparece apenas no alvo, as referências carregam informação que não existe na curva do alvo isolada.

A hipótese operacional é:

\[
H_1:
R_{\mathrm{CM}}-R_{\mathrm{TO}}>0,
\]

onde:

- \(R_{\mathrm{CM}}\): recall precoce após remoção common-mode;
- \(R_{\mathrm{TO}}\): recall do mesmo detector aplicado apenas ao alvo.

---

## 3. Previsão registrada antes dos resultados

1. O detector common-mode terá ganho absoluto de recall precoce entre 0,20 e 0,45 sobre o detector target-only.
2. Em eventos limpos, sem perturbação compartilhada concorrente, a perda de recall do common-mode será menor que 0,05.
3. O maior ganho ocorrerá quando um rise localizado coincidir com rampas ou steps compartilhados.
4. O método continuará vulnerável quando a maioria das referências estiver contaminada ou quando o artefato for exclusivo do alvo. Esses casos não são resolvidos pelo M2.
5. A remoção common-mode não transformará o detector em classificador astrofísico; ela testará apenas a separação entre sinal localizado e perturbação compartilhada.

A previsão quantitativa de promoção exige ganho mínimo confirmado de 0,15.

---

## 4. Campo observado

Cada curva contém:

- uma estrela-alvo, índice \(j=0\);
- oito estrelas de referência, índices \(j=1,\ldots,8\);
- 180 cadências;
- baseline causal nas cadências 0–49;
- avaliação nas cadências 50–179.

O modelo é:

\[
y_{j,k}
=
a_j c_k
+
s_{j,k}
+
\epsilon_{j,k},
\]

onde:

- \(c_k\) é o componente comum ao campo;
- \(a_j\) é o acoplamento individual ao common-mode;
- \(s_{j,k}\) é o sinal localizado ou o artefato injetado;
- \(\epsilon_{j,k}\) é ruído individual.

---

## 5. Common-mode de fundo

O componente comum de fundo existe também durante a baseline:

\[
c_k=\phi_c c_{k-1}+u_k,
\qquad
\phi_c\sim U(0.2,0.8).
\]

A inovação \(u_k\) é normal, com desvio-padrão 0,5.

Os acoplamentos são:

\[
a_j\sim U(0.7,1.3).
\]

Depois do início de uma perturbação compartilhada, cada acoplamento recebe uma variação multiplicativa independente:

\[
a'_{j}=a_j d_j,
\qquad
d_j\sim U(0.9,1.1).
\]

Assim, o common-mode não é removível de maneira perfeita.

---

## 6. Ruído individual

Para cada estrela:

\[
\epsilon_{j,k}
=
\phi_j\epsilon_{j,k-1}
+
\eta_{j,k},
\qquad
\phi_j\sim U(0,0.5).
\]

O desvio-padrão da inovação varia entre 0,8 e 1,2.

Com probabilidade 1/2, a inovação é normal. Caso contrário, é Student-t com 5 graus de liberdade, reescalada para a mesma variância.

São usadas 200 cadências de burn-in.

---

## 7. Eventos positivos

O evento existe apenas no alvo:

\[
s_{0,k}=A f(k),
\qquad
s_{j,k}=0\quad(j>0).
\]

Parâmetros:

- onset \(\tau\sim\operatorname{Unif}\{80,\ldots,110\}\);
- duração \(T\sim\operatorname{Unif}\{24,\ldots,60\}\);
- amplitude \(A/\sigma_0\sim U(3,7)\).

Formas:

1. linear;
2. power-law, \(\gamma\sim U(1.5,3)\);
3. exponencial normalizada, \(\beta\sim U(1,4)\);
4. logística normalizada, \(q\sim U(6,12)\).

Cada forma aparece em dois contextos:

- **clean:** sem artefato compartilhado adicional;
- **concurrent:** com uma perturbação compartilhada cujo onset fica entre \(\tau-10\) e \(\tau+10\).

Há, portanto, oito estratos positivos.

---

## 8. Famílias negativas

1. quiet: somente common-mode de fundo e ruído;
2. shared_ramp: rampa positiva compartilhada;
3. shared_step: step positivo compartilhado;
4. shared_bump: bump simétrico compartilhado;
5. shared_oscillation: oscilação compartilhada.

A amplitude da perturbação compartilhada satisfaz:

\[
A_c/\sigma_0\sim U(3,7).
\]

Ramp, step e bump começam entre as cadências 80 e 110. A oscilação possui período entre 16 e 48 cadências.

Em 30% das curvas, uma referência escolhida aleatoriamente recebe também um impulso independente de 1–2 cadências. A mediana entre oito referências deverá ser robusta a essa contaminação minoritária.

---

## 9. Normalização causal

Cada estrela é normalizada usando somente a baseline 0–49:

\[
\widehat{\mu}_j
=
\operatorname{median}(y_{j,0:49}),
\]

\[
\widehat{\sigma}_j
=
1.4826\operatorname{median}
|y_{j,k}-\widehat{\mu}_j|.
\]

Um coeficiente AR(1) \(\widehat{\phi}_j\) é estimado por Yule–Walker na baseline e limitado a \([0,0.8]\).

A série branqueada é:

\[
z_{j,k}
=
\frac{
(y_{j,k}-\widehat{\mu}_j)
-
\widehat{\phi}_j(y_{j,k-1}-\widehat{\mu}_j)
}{
\widehat{\sigma}_j
}.
\]

---

## 10. Estimativa causal do common-mode

A referência do campo é a mediana robusta:

\[
q_k
=
\operatorname{median}_{j=1,\ldots,8}
z_{j,k}.
\]

O acoplamento do alvo ao common-mode é estimado somente na baseline:

\[
\widehat{\beta}
=
\frac{
\sum_{k=1}^{49}(q_k-\bar q)(z_{0,k}-\bar z_0)
}{
\sum_{k=1}^{49}(q_k-\bar q)^2
},
\]

limitado a:

\[
0\leq\widehat{\beta}\leq3.
\]

O resíduo common-mode é:

\[
r_k
=
z_{0,k}
-
\widehat{\beta}q_k.
\]

---

## 11. Detectores comparados

Os dois detectores usam exatamente a mesma estatística causal de inclinação e as mesmas janelas:

\[
w\in\{8,16,32\}.
\]

### Target-only

Aplica a estatística à série \(z_{0,k}\).

### Common-mode

Aplica a mesma estatística ao resíduo \(r_k\).

Para cada janela:

\[
T_w(k)
=
\max\left(
0,
\frac{\widehat b_w}{SE(\widehat b_w)}
\right).
\]

O score é:

\[
S(k)=\max_w T_w(k).
\]

O alerta é o primeiro cruzamento do limiar.

---

## 12. Detecção precoce

Defina:

\[
t_{25}
=
\min\{k:s_{0,k}\geq0.25A\}.
\]

Uma detecção correta exige:

\[
\tau
\leq
t_{\mathrm{alert}}
\leq
t_{25}.
\]

Disparos anteriores a \(\tau\) contam como falsos disparos e não como detecção.

---

## 13. Desenvolvimento

Para cada estrato:

- 2.000 curvas por estrato positivo;
- 2.000 curvas por família negativa.

Cada detector recebe seu próprio limiar, escolhido para manter FPR empírico de no máximo 0,5% em **cada** família negativa.

Nenhum limiar usa positivos.

---

## 14. Holdout

O holdout contém, no total:

- 5.000 curvas por cada um dos oito estratos positivos;
- 5.000 curvas por cada uma das cinco famílias negativas;
- 20 lotes independentes;
- 250 curvas por estrato em cada lote.

Total:

\[
8(5000)+5(5000)=65\,000
\]

campos sintéticos.

O holdout será gerado apenas depois de código, testes, seeds, métricas e limiares terem sido congelados.

---

## 15. Métrica primária

Recall precoce global com pesos iguais entre os oito estratos:

\[
R
=
\frac{1}{8}
\sum_{h=1}^{8}R_h.
\]

Diferença emparelhada:

\[
\Delta R
=
R_{\mathrm{CM}}-R_{\mathrm{TO}}.
\]

Intervalos serão obtidos por bootstrap estratificado e emparelhado com 10.000 réplicas.

---

## 16. Controle de falso alerta

Para cada família negativa:

\[
FPR_j
=
P(\exists k\in[50,179]:S(k)\geq\theta\mid j).
\]

Será usado limite superior unilateral de Clopper–Pearson a 95%.

Não haverá média entre famílias para decidir aprovação.

---

## 17. Não inferioridade em eventos limpos

Nos quatro estratos clean:

\[
\Delta R_{\mathrm{clean}}
=
R_{\mathrm{CM,clean}}
-
R_{\mathrm{TO,clean}}.
\]

A remoção common-mode não pode destruir substancialmente eventos limpos. Exigimos:

\[
\Delta R_{\mathrm{clean,lower}}^{95\%}
\geq-0.05.
\]

---

## 18. Vitória

O M2 passa somente se todos os critérios ocorrerem:

1. Em cada família negativa do detector common-mode:
\[
FPR_{\mathrm{upper}}^{95\%}\leq0.01.
\]

2. Recall common-mode:
\[
R_{\mathrm{CM,lower}}^{95\%}\geq0.30.
\]

3. Ganho global:
\[
\Delta R_{\mathrm{lower}}^{95\%}\geq0.15.
\]

4. Não inferioridade clean:
\[
\Delta R_{\mathrm{clean,lower}}^{95\%}\geq-0.05.
\]

5. Pelo menos 7 dos 8 estratos possuem diferença pontual não negativa.

6. Pelo menos 15 dos 20 lotes possuem:
\[
\Delta R>0.
\]

---

## 19. Falha forte

O M2 é rejeitado nesta forma se:

- qualquer família negativa viola o limite de FPR; ou
- o limite superior de 95% de \(\Delta R\) é menor ou igual a zero; ou
- o limite superior de 95% de \(\Delta R_{\mathrm{clean}}\) é menor que \(-0.05\).

---

## 20. Inconclusivo

Qualquer resultado que não satisfaça vitória nem falha forte é inconclusivo.

Para engenharia:

> PASS promove; STRONG_FAIL e INCONCLUSIVE não promovem.

---

## 21. Resultados secundários

Sem poder de promoção:

- AUROC;
- Average Precision;
- recall por forma e contexto;
- tempo de alerta;
- estimativa de \(\widehat{\beta}\);
- resíduos common-mode;
- resultado por seed;
- custo computacional;
- teste de estresse com duas, três e cinco referências contaminadas.

O teste de estresse é exploratório e não altera o veredito primário.

---

## 22. Regras contra puxadinho

1. Nenhum ajuste após abrir o holdout.
2. Nenhuma exclusão de família ou lote.
3. Nenhum uso do M1 como conjunto de ajuste.
4. Nenhuma alteração da definição de early detection.
5. Nenhuma troca de métrica primária.
6. Todo bug pré-holdout será corrigido e registrado.
7. Bug pós-holdout invalida a execução; não autoriza ajuste silencioso.
8. Resultados negativos serão preservados.
9. O escopo da conclusão será limitado ao modelo efetivamente testado.
