# ARARA From Zero — Pré-registro M1

**Estado:** congelado antes da execução  
**Versão:** M1.0  
**Objetivo:** testar uma única alegação sobre detecção causal precoce.  
**Regra de promoção:** qualquer resultado que não satisfaça todos os critérios primários não promove o detector.

---

## 1. Pergunta pequena

Em séries fotométricas sintéticas não vistas, um detector causal de tendência positiva local, chamado **ARARA-M1**, detecta rises sustentados mais cedo que um CUSUM unilateral, mantendo a mesma taxa máxima de falso alerta?

Este teste avalia somente a lógica de detecção em resíduos fotométricos normalizados.  
Ele não valida óptica, detector físico, saúde instrumental, FLOCK, energia ou missão orbital.

---

## 2. Alegação testada

**C1:** Um detector que mede diretamente tendência positiva causal em múltiplas escalas temporais apresenta maior recall precoce que um CUSUM unilateral em rises graduais, sob controle estrito e igual de falsos alertas.

---

## 3. Previsão registrada antes dos resultados

1. O ARARA-M1 deverá respeitar o limite de falso alerta em todas as famílias negativas.
2. O ganho esperado de recall precoce sobre CUSUM é de 0,08 a 0,18 em termos absolutos.
3. O ganho deverá ser maior em rises lineares e power-law.
4. O ganho poderá ser menor em rises exponenciais e logísticos.
5. O ARARA-M1 não deverá distinguir um rise astrofísico de um drift instrumental monotônico com a mesma forma observacional. Esse problema será reservado ao módulo de saúde instrumental.

A previsão operacional de aprovação é: ganho de pelo menos 0,10 com recall precoce absoluto de pelo menos 0,30.

---

## 4. Unidade temporal e sequência

- Unidade temporal: uma cadência abstrata.
- Comprimento de cada série: 160 cadências.
- Baseline causal inicial: cadências 0–39.
- Região de avaliação: cadências 40–159.
- Onset verdadeiro dos eventos: inteiro uniforme entre 60 e 90.
- Duração característica do rise: inteiro uniforme entre 24 e 60 cadências.

Nenhum resultado será convertido para segundos antes de uma cadência instrumental ser justificada.

---

## 5. Modelo de observação

A série observada é:

\[
y_k = \mu + s_k + arepsilon_k.
\]

A baseline possui \(\mu=0\). O ruído segue AR(1):

\[
arepsilon_k = \phiarepsilon_{k-1}+\eta_k,
\qquad
\phi\sim U(0,0.6).
\]

Cada curva escolhe, com probabilidade 1/2:

- inovação gaussiana de variância unitária; ou
- inovação Student-t com 5 graus de liberdade, reescalada para variância unitária.

A amplitude final do sinal, em unidades do desvio-padrão do ruído, é:

\[
A/\sigma \sim U(2,5).
\]

---

## 6. Famílias positivas

Defina:

\[
x_k=\operatorname{clip}\left(rac{k-	au}{T},0,1ight).
\]

Serão usadas quatro famílias, com a mesma frequência:

1. Linear:
\[
s_k=A x_k.
\]

2. Power-law:
\[
s_k=A x_k^\gamma,
\qquad
\gamma\sim U(1.5,3).
\]

3. Exponencial normalizada:
\[
s_k=Arac{e^{eta x_k}-1}{e^eta-1},
\qquad
eta\sim U(1,4).
\]

4. Logística normalizada no intervalo \([0,1]\), com inclinação:
\[
q\sim U(6,12).
\]

---

## 7. Famílias negativas

Cada família será avaliada separadamente:

1. ruído quieto AR(1);
2. impulso positivo de 1–2 cadências;
3. bump simétrico;
4. oscilação aproximadamente senoidal;
5. dip negativo seguido de recuperação.

Amplitudes e durações serão sorteadas em faixas comparáveis às dos eventos positivos.

Drift monotônico e step positivo persistente ficam fora do M1 porque, sem housekeeping ou informação espacial adicional, podem ser observacionalmente indistinguíveis de um evento verdadeiro. Eles serão tratados no teste do módulo interno.

---

## 8. Normalização causal

A mediana, a escala robusta e o coeficiente AR(1) serão estimados somente nas cadências 0–39.

\[
\widehat{\mu}=\operatorname{median}(y_0,\ldots,y_{39}),
\]

\[
\widehat{\sigma}
=
1.4826\operatorname{median}
|y_k-\widehat{\mu}|.
\]

O coeficiente \(\widehat{\phi}\) será estimado por Yule–Walker na baseline e limitado ao intervalo \([0,0.8]\).

A série será branqueada causalmente:

\[
z_k=
rac{
(y_k-\widehat{\mu})
-\widehat{\phi}(y_{k-1}-\widehat{\mu})
}{
\widehat{\sigma}
}.
\]

Nenhuma amostra posterior ao início da região de avaliação entra na calibração da baseline.

---

## 9. Detector ARARA-M1

Para cada instante \(k\) e cada janela:

\[
w\in\{8,16,32\},
\]

é ajustada uma regressão linear causal:

\[
z_i=a+b\,t_i+e_i.
\]

Calcula-se o t-estatístico unilateral da inclinação:

\[
T_w(k)=
\max\left(
0,
rac{\widehat b}{SE(\widehat b)}
ight).
\]

O score é:

\[
S_{\mathrm{M1}}(k)=
\max_{w\in\{8,16,32\}}T_w(k).
\]

O primeiro cruzamento do limiar é:

\[
t_{\mathrm{alert}}
=
\min\{k:S_{\mathrm{M1}}(k)\geq	heta\}.
\]

Não será usado o instante do máximo do score.

---

## 10. Baselines

### Flux-z

\[
S_z(k)=\max(0,z_k).
\]

### CUSUM unilateral

\[
C_k=
\max(0,C_{k-1}+z_k-\kappa).
\]

O parâmetro \(\kappa\) será escolhido somente no conjunto de desenvolvimento, a partir da grade fixa:

\[
\{0.25,0.50,0.75,1.00\}.
\]

A escolha maximizará recall precoce sob a restrição de falso alerta do desenvolvimento.

---

## 11. Definição de detecção precoce

Para cada evento, defina:

\[
t_{25}=
\min\{k:s_k\geq0.25A\}.
\]

Uma detecção correta e precoce exige:

\[
	au\leq t_{\mathrm{alert}}\leq t_{25}.
\]

Qualquer cruzamento antes de \(	au\) é um falso disparo e a curva não conta como detecção correta.

---

## 12. Dados de desenvolvimento e teste

### Desenvolvimento

- 2.000 curvas por família positiva;
- 2.000 curvas por família negativa.

Os limiares serão escolhidos para que o FPR empírico seja no máximo 0,5% em cada família negativa.

### Holdout final

- 5.000 curvas por família positiva;
- 5.000 curvas por família negativa;
- 20 lotes independentes de seeds.

O holdout será gerado apenas após código, parâmetros, métricas e critérios terem sido congelados.

Nenhum hiperparâmetro será alterado depois de abrir o holdout.

---

## 13. Métrica primária

Recall precoce:

\[
R_{\mathrm{early}}
=
rac{
N(	au\leq t_{\mathrm{alert}}\leq t_{25})
}{
N_{\mathrm{eventos}}
}.
\]

Diferença emparelhada contra CUSUM:

\[
\Delta R
=
R_{\mathrm{early,M1}}
-
R_{\mathrm{early,CUSUM}}.
\]

O intervalo de confiança será obtido por bootstrap estratificado por família positiva, com 10.000 réplicas.

---

## 14. Controle de falso alerta

Para cada família negativa:

\[
FPR_j=
P(\exists k\in[40,159]:
S(k)\geq	heta
\mid j).
\]

Será calculado o limite superior unilateral de 95% de Clopper–Pearson.

Não será usada média arbitrária entre famílias negativas.

---

## 15. Vitória

O M1 passa somente se todos os itens forem satisfeitos:

1. Para cada família negativa, o limite superior unilateral de 95% do FPR é menor ou igual a 1%.
2. O limite inferior de 95% do recall precoce do M1 é maior ou igual a 0,30.
3. O limite inferior de 95% de \(\Delta R\) é maior ou igual a 0,10.
4. Pelo menos 3 das 4 famílias positivas apresentam diferença pontual não negativa.
5. Pelo menos 15 dos 20 lotes de seed apresentam \(\Delta R>0\).

---

## 16. Falha e resultado inconclusivo

### Falha forte

O detector é rejeitado nesta forma se:

- qualquer família negativa ultrapassar o limite de FPR; ou
- o limite superior de 95% de \(\Delta R\) for menor ou igual a zero.

### Inconclusivo

O resultado é inconclusivo quando não satisfaz a vitória, mas também não satisfaz a falha forte.

Para fins de engenharia, tanto falha forte quanto inconclusivo significam:

> não promover o M1 para o próximo módulo.

Uma versão M2 exigirá novo pré-registro. Os critérios do M1 não serão alterados retroativamente.

---

## 17. Resultados secundários

Serão relatados, mas não decidirão aprovação:

- AUROC;
- Average Precision;
- mediana do primeiro cruzamento;
- ganho de tempo em cadências;
- resultados por família de sinal;
- distribuição por seed;
- curvas de calibração;
- custo computacional por amostra.

---

## 18. Regras contra puxadinho

1. Nenhum ajuste usando o holdout.
2. Nenhuma remoção de família depois de ver o resultado.
3. Nenhuma mudança de métrica primária.
4. Nenhum descarte seletivo de seeds.
5. Toda exceção numérica vira falha explícita.
6. Resultados negativos serão preservados.
7. Código, ambiente, seeds, hashes e tabelas serão arquivados.
8. Uma alegação só será promovida dentro do escopo efetivamente testado.
