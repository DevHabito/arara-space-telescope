# ARARA From Zero — Relatório do M8 Oracle at t100

**Estado:** concluído  
**Holdout:** aberto uma única vez  
**Veredito:** `INCONCLUSIVE`  
**Decisão:** **NÃO PROMOVER O CONTRATO ATUAL**

## 1. Pergunta

Com onset e template processado exatos, observar até a primeira chegada à amplitude final torna o evento detectável sob o mesmo controle de falso alerta?

## 2. Previsão registrada

\[
0.25\leq R_{t100}\leq0.55.
\]

O resultado pontual ficou dentro da faixa prevista, mas não satisfez todos os critérios de vitória.

## 3. Resultado primário

- recall global: 0.359125 = 35.913%;
- intervalo de 95%: 0.355275 a 0.362901;
- limiar: 8.757669449;
- estratos aprovados: 3/8;
- lotes aprovados: 16/20.

O critério global exigia limite inferior de pelo menos 40%. O observado foi 35.528%.

## 4. Resultado por estrato

| Estrato | Recall | Limite inferior 95% |
|---|---:|---:|
| linear__clean | 0.307800 | 0.297048 |
| linear__concurrent | 0.307200 | 0.296454 |
| power_law__clean | 0.325600 | 0.314677 |
| power_law__concurrent | 0.309200 | 0.298434 |
| exponential__clean | 0.274000 | 0.263624 |
| exponential__concurrent | 0.268600 | 0.258291 |
| logistic__clean | 0.564600 | 0.552941 |
| logistic__concurrent | 0.516000 | 0.504270 |

## 5. Falsos alertas

| Família | FPR | Limite superior 95% |
|---|---:|---:|
| quiet | 0.000000 | 0.000599 |
| shared_ramp | 0.005600 | 0.007670 |
| shared_step | 0.001200 | 0.002367 |
| shared_bump | 0.002800 | 0.004374 |
| shared_oscillation | 0.000600 | 0.001550 |

O FPR passou em todas as famílias. `shared_bump` determinou o limiar de desenvolvimento.

## 6. Clean versus concurrent

- clean: 0.368000;
- concurrent: 0.350250.

Diferentemente dos testes anteriores, o desempenho foi semelhante entre os contextos, com leve vantagem para clean.

## 7. Métricas secundárias

- AUROC: 0.969313;
- Average Precision: 0.979962.

## 8. Progressão das janelas

\[
R_{t25}=0.00335,
\]

\[
R_{t50}=0.035575,
\]

\[
R_{t75}=0.12925,
\]

\[
R_{t100}=0.359125.
\]

A informação cresce fortemente com a evolução do evento. Contudo, o desempenho operacionalmente útil só começa a surgir próximo da amplitude completa, o que contraria a meta de alerta realmente precoce.

## 9. Conclusão permitida

> No modelo atual, amplitude completa e alinhamento-oráculo fornecem informação moderada, mas ainda insuficiente para promover o contrato: recall de aproximadamente 36%, com forte heterogeneidade entre formas.

## 10. Decisão científica

A sequência de frações termina aqui. O próximo teste não deve ampliar novamente a janela. Deve alterar uma variável física ou instrumental, preferencialmente a amplitude final/SNR, mantendo o restante congelado.
