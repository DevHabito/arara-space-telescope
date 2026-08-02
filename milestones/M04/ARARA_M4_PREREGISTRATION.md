# ARARA From Zero — Pré-registro M4 Matched-Filter Viability

**Versão:** M4.0  
**Estado:** congelado antes da implementação e da geração de dados  
**Objetivo:** testar a viabilidade estatística do contrato de alerta precoce.

---

## 1. Pergunta pequena

Um banco causal de matched filters, construído para as quatro famílias de rise do gerador mas sem conhecer onset, duração ou parâmetros verdadeiros, consegue detectar pelo menos metade dos eventos antes de \(t_{25}\), mantendo falsos alertas rigorosamente controlados em cada família negativa?

---

## 2. Interpretação

O M4 não é proposto como detector operacional final. Ele é um teste de viabilidade.

Se um detector próximo do modelo do sinal não conseguir desempenho útil, não será lógico continuar ajustando detectores genéricos sob o mesmo contrato.

---

## 3. Dados

O modelo sintético de campo é idêntico ao M2/M3:

- uma estrela-alvo;
- oito referências;
- 180 cadências;
- baseline 0–49;
- avaliação 50–179;
- quatro formas positivas;
- contextos clean e concurrent;
- cinco famílias negativas;
- ruído AR(1), normal ou Student-t;
- common-mode;
- uma referência impulsiva em 30% dos campos.

Nenhuma curva anterior será reutilizada.

Seeds:

- desenvolvimento: `2026073001`;
- holdout: `2026073002`;
- bootstrap: `2026073003`.

O preprocessing será o SBW congelado no M3.

---

## 4. Banco causal de templates

O banco será criado antes dos dados.

### Durações candidatas

\[
D\in\{24,36,48,60\}.
\]

### Níveis finais do prefixo

\[
p\in\{0.10,0.15,0.20,0.25\}.
\]

Cada template representa somente o prefixo de um rise, terminando quando a forma alcança a fração \(p\) de sua amplitude final.

### Formas e parâmetros

1. Linear.
2. Power-law:
\[
\gamma\in\{1.5,2.25,3.0\}.
\]
3. Exponencial:
\[
\beta\in\{1.0,2.5,4.0\}.
\]
4. Logística:
\[
q\in\{6,9,12\}.
\]

O comprimento discreto será:

\[
L=\max\left(6,\left\lceil D x_p\right\rceil+1\right),
\]

onde \(x_p\) satisfaz \(f(x_p)=p\).

A sequência do template é:

\[
h_i=f\left(\frac{i}{L-1}x_p\right),
\qquad i=0,\ldots,L-1.
\]

Templates numericamente duplicados serão removidos antes da execução.

---

## 5. Estatística matched-filter

Para cada template e para cada janela causal terminando em \(k\), ajusta-se:

\[
r_i=\alpha+A h_i+e_i.
\]

Com correlação amostral \(c\) entre a janela e o template centralizados, o t-estatístico unilateral da amplitude é:

\[
T=
\begin{cases}
c\sqrt{\frac{L-2}{1-c^2}},& c>0,\\
0,&c\leq0.
\end{cases}
\]

Se \(c\rightarrow1\), \(T\rightarrow+\infty\).

O score no instante \(k\) é o máximo entre todos os templates causais que terminam em \(k\):

\[
S_{\mathrm{MF}}(k)=\max_m T_m(k).
\]

O alerta é o primeiro cruzamento do limiar.

O detector nunca recebe onset, duração, forma ou parâmetro verdadeiro.

---

## 6. Comparador secundário

O detector SBW de inclinação do M3 será executado nas mesmas curvas somente como comparação secundária.

Ele não participa do critério de viabilidade do M4.

---

## 7. Detecção precoce

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

Cruzamento anterior ao onset invalida a detecção daquela curva.

---

## 8. Desenvolvimento

- 2.000 campos por cada um dos oito estratos positivos;
- 2.000 campos por cada família negativa;
- limiar calculado apenas nos negativos;
- máximo de 0,5% de alertas em cada família negativa.

O limiar global será o máximo dos cinco limiares familiares.

---

## 9. Holdout

- 5.000 campos por cada estrato positivo;
- 5.000 campos por família negativa;
- 20 lotes independentes;
- 65.000 campos no total.

O holdout será aberto uma única vez após testes, código, templates, limiar, seeds e hashes estarem congelados.

---

## 10. Métrica primária

Recall precoce com pesos iguais entre os oito estratos:

\[
R_{\mathrm{MF}}
=
\frac{1}{8}\sum_{h=1}^{8}R_h.
\]

Intervalo por bootstrap estratificado com 10.000 réplicas.

---

## 11. Previsão anterior aos resultados

A previsão é:

\[
0.30\leq R_{\mathrm{MF}}\leq0.60.
\]

Também se prevê:

1. recall maior em linear e logística;
2. recall menor em power-law e exponencial;
3. desempenho menor em concurrent que em clean;
4. shared_oscillation continuará determinando o limiar;
5. o matched filter superará claramente o detector de inclinação SBW.

A previsão será considerada confirmada somente se o intervalo observado for compatível e os critérios de vitória forem satisfeitos.

---

## 12. Vitória

O contrato será considerado detectável pelo banco M4 somente se todos os itens ocorrerem:

1. Em cada família negativa:
\[
FPR_{\mathrm{upper}}^{95\%}\leq0.01.
\]

2. Recall global:
\[
R_{\mathrm{MF,lower}}^{95\%}\geq0.50.
\]

3. Pelo menos seis dos oito estratos:
\[
R_{h,\mathrm{lower}}^{95\%}\geq0.30.
\]

4. Pelo menos 15 dos 20 lotes possuem recall:
\[
R_{\mathrm{MF,batch}}\geq0.45.
\]

5. O limite inferior de 95% da diferença contra SBW é:
\[
R_{\mathrm{MF}}-R_{\mathrm{SBW}}\geq0.20.
\]

---

## 13. Falha forte

O contrato M4 será considerado inviável para este banco se:

- qualquer família negativa viola o limite; ou
- o limite superior de 95% do recall global é:
\[
R_{\mathrm{MF,upper}}^{95\%}\leq0.20;
\]
ou
- o limite superior de 95% da diferença contra SBW é menor ou igual a zero.

---

## 14. Inconclusivo

Qualquer resultado entre vitória e falha forte será inconclusivo.

Regra de engenharia:

> PASS permite continuar com um detector operacional. STRONG_FAIL exige rever o contrato. INCONCLUSIVE não autoriza promoção.

---

## 15. Resultados secundários

- AUROC e AP;
- recall por forma e contexto;
- detecção por nível \(p\);
- template vencedor;
- tempo até alerta;
- distribuição de scores;
- custo computacional;
- número efetivo de templates após deduplicação.

Nenhum resultado secundário altera o veredito.

---

## 16. Regras contra puxadinho

1. Nenhum template será adicionado após o desenvolvimento.
2. Nenhuma duração ou parâmetro será removido após os resultados.
3. O holdout será aberto uma única vez.
4. Nenhuma família, seed ou lote será excluído.
5. Bug pré-holdout será registrado e corrigido.
6. Bug pós-holdout invalida a execução.
7. O matched filter não receberá parâmetros verdadeiros.
8. Resultados negativos serão preservados.
9. O escopo da conclusão será limitado ao modelo sintético testado.
