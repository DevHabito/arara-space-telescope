# ARARA From Zero — Relatório do M6 Oracle at t50

**Estado:** concluído  
**Holdout:** aberto uma única vez  
**Veredito:** `STRONG_FAIL`  
**Decisão:** **\(t_{50}\) AINDA É INSUFICIENTE NO MODELO TESTADO**

## 1. Pergunta

Mantendo tudo igual ao M5, permitir observação até 50% da amplitude final torna o evento detectável quando onset e template exatos são conhecidos?

## 2. Previsão

\[
0.25\leq R_{t50}\leq0.60.
\]

Para passar, o limite inferior deveria ser pelo menos 0,50.

## 3. Resultado primário

- limiar: 7.325491428;
- recall: 0.035575 = 3.558%;
- intervalo de 95%: 0.034050 a 0.037125;
- estratos aprovados: 0/8;
- lotes aprovados: 0/20.

O recall aumentou em relação ao M5, mas o limite superior permaneceu abaixo de 4%.

## 4. Resultado por estrato

| Estrato | Detecções | N | Recall | Limite inferior 95% |
|---|---:|---:|---:|---:|
| linear__clean | 45 | 5000 | 0.009000 | 0.006919 |
| linear__concurrent | 201 | 5000 | 0.040200 | 0.035731 |
| power_law__clean | 117 | 5000 | 0.023400 | 0.019991 |
| power_law__concurrent | 342 | 5000 | 0.068400 | 0.062616 |
| exponential__clean | 93 | 5000 | 0.018600 | 0.015568 |
| exponential__concurrent | 322 | 5000 | 0.064400 | 0.058780 |
| logistic__clean | 65 | 5000 | 0.013000 | 0.010478 |
| logistic__concurrent | 238 | 5000 | 0.047600 | 0.042744 |

## 5. Falsos alertas

| Família | Alertas | N | FPR | Limite superior 95% |
|---|---:|---:|---:|---:|
| quiet | 0 | 5000 | 0.000000 | 0.000599 |
| shared_ramp | 10 | 5000 | 0.002000 | 0.003390 |
| shared_step | 8 | 5000 | 0.001600 | 0.002885 |
| shared_bump | 26 | 5000 | 0.005200 | 0.007208 |
| shared_oscillation | 12 | 5000 | 0.002400 | 0.003886 |

O FPR passou em todas as famílias. Diferentemente da previsão, `shared_bump`, e não `shared_oscillation`, determinou o limiar de desenvolvimento.

## 6. Clean versus concurrent

- recall clean: 0.016000;
- recall concurrent: 0.055150.

A superioridade de concurrent continua suspeita: perturbações adicionais podem elevar correlação e não devem ser interpretadas como melhor detecção do evento verdadeiro.

## 7. Métricas secundárias

- AUROC: 0.872029;
- Average Precision: 0.900717.

O ranking global tornou-se forte, mas o ponto operacional de falso alerta ainda produz recall baixo.

## 8. Comparação M5 → M6

\[
R_{t25}=0.00335,
\qquad
R_{t50}=0.035575.
\]

A janela maior produziu ganho de aproximadamente 10,6 vezes, porém o valor absoluto continua incompatível com um alerta científico útil.

## 9. Conclusão permitida

> No modelo sintético atual, observar até metade da amplitude não fornece evidência suficiente para recall alto sob o contrato de falso alerta, mesmo com alinhamento e template exatos.

## 10. Próxima pergunta

A próxima alteração isolada deve ser \(t_{75}\). Se \(t_{75}\) também falhar fortemente, será mais racional revisar amplitude, ruído, cadência ou informação multibanda do que continuar ampliando detectores.
