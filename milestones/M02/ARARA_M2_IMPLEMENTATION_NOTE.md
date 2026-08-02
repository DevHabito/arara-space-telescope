# ARARA-M2 — Nota de implementação congelada

**Versão:** 2.0  
**Estado:** congelada antes da geração de desenvolvimento e holdout.

Esta nota resolve ambiguidades operacionais sem alterar hipótese, previsão, métricas ou critérios.

## 1. Seeds

- desenvolvimento: `2026072801`;
- holdout: `2026072802`;
- bootstrap: `2026072803`.

Cada estrato e lote recebe uma `SeedSequence` filha registrada.

## 2. Desvio-padrão de referência

Quando uma amplitude é expressa em unidades de \(\sigma_j\), usa-se o desvio-padrão estacionário do ruído individual:

\[
\sigma_j
=
\frac{\sigma_{\eta,j}}{\sqrt{1-\phi_j^2}}.
\]

O common-mode de fundo não entra nessa definição.

## 3. Perturbações compartilhadas

Seja \(u=(k-\tau_c)/T_c\).

- shared_ramp:
  \[
  h(k)=\operatorname{clip}(u,0,1).
  \]
- shared_step:
  \[
  h(k)=\mathbb{1}(k\geq\tau_c).
  \]
- shared_bump:
  \[
  h(k)=\sin(\pi u)
  \]
  para \(0\leq u\leq1\), zero fora.
- shared_oscillation:
  \[
  h(k)=\mathbb{1}(k\geq\tau_c)
  \sin(2\pi(k-\tau_c)/P).
  \]

Para ramp e bump, \(T_c\) é uniforme entre 24 e 60. Para step não há duração. Para oscilação, \(P\) é inteiro uniforme entre 16 e 48.

A injeção em cada estrela é:

\[
a_j d_j A_c h(k),
\]

com \(d_j\sim U(0.9,1.1)\).

## 4. Contexto concurrent

Para cada evento concurrent:

- sorteia-se uniformemente uma das quatro famílias compartilhadas;
- o onset compartilhado é:
  \[
  \tau_c=\operatorname{clip}(\tau+\delta,60,120),
  \quad
  \delta\sim\operatorname{Unif}\{-10,\ldots,10\};
  \]
- amplitude e duração seguem as mesmas distribuições dos negativos.

## 5. Contaminação de referência

Com probabilidade 0,30 por campo:

- uma das oito referências é escolhida uniformemente;
- recebe um impulso positivo de uma ou duas cadências;
- o início é uniforme entre 60 e 178;
- a amplitude é uniforme entre 3 e 7 vezes o desvio-padrão estacionário daquela referência.

O alvo nunca recebe esse impulso de referência.

## 6. Normalização e beta

A baseline inclui índices 0–49. O cálculo de beta usa índices 1–49, porque a primeira amostra branqueada não possui predecessor observado.

A regressão possui intercepto por centralização. Se a variância de \(q\) for menor que \(10^{-12}\), beta é definido como zero. Depois:

\[
\widehat\beta\leftarrow
\operatorname{clip}(\widehat\beta,0,3).
\]

## 7. Estatística de inclinação

É a mesma definição matemática do M1. Em uma janela com variância residual numericamente zero:

- inclinação positiva recebe \(+\infty\);
- inclinação nula ou negativa recebe zero.

## 8. Limiar

Para 2.000 negativos e alvo de 0,5%, são permitidos no máximo 10 alertas por família.

Com alerta definido por \(S\geq\theta\), o limiar de cada família é o menor número representável, no dtype do score, estritamente maior que o 11º maior máximo. O limiar global é o máximo dos limiares familiares.

## 9. Bootstrap

O bootstrap é:

- emparelhado entre target-only e common-mode;
- estratificado;
- 10.000 réplicas;
- pesos iguais entre estratos.

Para recall global são usados oito estratos. Para não inferioridade clean são usados os quatro estratos clean.

Limites inferiores e superiores são os percentis 5% e 95%, coerentes com limites unilaterais pré-registrados de 95%.

## 10. Métrica por lote

Cada lote contém 250 curvas por cada um dos oito estratos positivos. O recall do lote é a média simples das 2.000 curvas positivas, equivalente à média com peso igual porque todos os estratos têm o mesmo tamanho.

## 11. AUROC e AP

Usam o máximo do score na mesma janela 50–179 para positivos e negativos. São secundários e não alteram o veredito.

## 12. Holdout

O arquivo `HOLDOUT_OPENED.json` será criado imediatamente antes da geração. Uma segunda execução é recusada automaticamente.
