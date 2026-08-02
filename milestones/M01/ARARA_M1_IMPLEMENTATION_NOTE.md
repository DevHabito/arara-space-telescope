# ARARA-M1 — Nota de implementação congelada

**Versão:** 1.0  
**Estado:** congelada antes da geração dos dados de desenvolvimento e holdout.

Esta nota resolve apenas ambiguidades operacionais do pré-registro M1. Ela não altera a pergunta, os detectores, as métricas ou os critérios de promoção.

## 1. Interpretação dos 20 lotes

O holdout contém 5.000 curvas por família **no total**, particionadas em 20 lotes independentes de 250 curvas por família. Assim:

- positivos: 4 × 5.000 = 20.000;
- negativos: 5 × 5.000 = 25.000;
- total: 45.000 curvas.

## 2. Seeds

- desenvolvimento: seed-raiz `2026072701`;
- holdout: seed-raiz `2026072702`;
- bootstrap: seed `2026072703`.

Cada lote do holdout recebe uma `SeedSequence` filha registrada.

## 3. Ruído

São simuladas 200 cadências de burn-in e 160 cadências retidas.

\[
\epsilon_k=\phi\epsilon_{k-1}+\eta_k,\quad \phi\sim U(0,0.6).
\]

A inovação é:

- normal padrão; ou
- Student-t com 5 graus de liberdade multiplicada por \(\sqrt{3/5}\), produzindo variância unitária.

A amplitude física usa o desvio-padrão marginal teórico:

\[
\sigma_\epsilon=(1-\phi^2)^{-1/2}.
\]

## 4. Positivos

Onset \(\tau\sim\operatorname{Unif}\{60,\ldots,90\}\), duração \(T\sim\operatorname{Unif}\{24,\ldots,60\}\) e amplitude \(A/\sigma_\epsilon\sim U(2,5)\).

Com \(x=\operatorname{clip}((k-\tau)/T,0,1)\):

- linear: \(s=Ax\);
- power-law: \(s=Ax^\gamma,\ \gamma\sim U(1.5,3)\);
- exponencial: \(s=A(e^{\beta x}-1)/(e^\beta-1),\ \beta\sim U(1,4)\);
- logística: \(s=A[g(x)-g(0)]/[g(1)-g(0)]\), \(g(x)=1/(1+e^{-q(x-1/2)})\), \(q\sim U(6,12)\).

## 5. Negativos

A amplitude e a duração usam as mesmas faixas dos positivos.

- quiet: \(s=0\);
- positive_impulse: pulso retangular positivo com 1 ou 2 cadências;
- symmetric_bump: \(s=A\sin(\pi x)\) durante uma duração \(T\), zero fora;
- sinusoid: \(s=A\sin(2\pi k/P+\varphi)\), \(P\sim U\{12,\ldots,48\}\), \(\varphi\sim U(0,2\pi)\);
- negative_dip_recovery: \(s=-A\sin(\pi x)\) durante uma duração \(T\), zero fora.

Bump e dip começam em uma época uniforme de 60 a 90. O impulso começa de 60 a 150.

## 6. Normalização

Mediana, MAD e AR(1) são estimados apenas nas épocas 0–39. O estimador de Yule–Walker é limitado a \([0,0.8]\). O MAD recebe piso numérico de \(10^{-8}\).

## 7. Limiar

Para uma família com \(n=2000\) e alvo de FPR 0,5%, são permitidos no máximo 10 disparos. Com alerta definido por score \(\geq\theta\), o limiar familiar é o menor número de ponto flutuante estritamente maior que o 11º maior máximo. O limiar final é o máximo entre as cinco famílias.

Esse procedimento é conservador em empates.

## 8. Escolha do CUSUM

Para cada \(\kappa\in\{0.25,0.50,0.75,1.00\}\):

1. calibra-se o limiar nos negativos;
2. calcula-se recall precoce nos positivos de desenvolvimento.

Escolhe-se a maior taxa de recall. Empates são resolvidos por:

1. menor pior FPR entre famílias;
2. menor \(\kappa\).

## 9. Intervalos

- FPR: limite superior unilateral de Clopper–Pearson a 95%;
- recall e diferença emparelhada: bootstrap não paramétrico estratificado por família positiva, 10.000 réplicas;
- limite inferior: percentil 5%;
- limite superior: percentil 95%.

Como as quatro famílias têm o mesmo tamanho, cada uma recebe peso igual.

## 10. Métricas secundárias

AUROC e Average Precision usam o máximo na mesma janela fixa 40–159 para positivos e negativos. Elas não participam do veredito.
