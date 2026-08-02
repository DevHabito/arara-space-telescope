# ARARA From Zero — Relatório do M5 Oracle-Aligned Information Bound

**Estado:** concluído  
**Holdout:** aberto uma única vez  
**Veredito:** `STRONG_FAIL`  
**Decisão:** **O CONTRATO ATÉ \(t_{25}\) É INSUFICIENTE NO MODELO TESTADO**

## 1. Pergunta

Se onset e contribuição processada exata do evento forem conhecidos, existe evidência suficiente entre onset e \(t_{25}\) para detectar a maioria dos eventos?

## 2. Natureza do teste

O M5 não procurou onset, duração ou forma. Cada positivo foi testado uma única vez no segmento verdadeiro, com o template exato depois do preprocessing SBW.

Cada negativo recebeu uma única hipótese virtual independente, sorteada nas mesmas distribuições.

## 3. Previsão

\[
0.40\leq R_{oracle}\leq0.75.
\]

Para passar, o limite inferior de 95% deveria ser pelo menos 0,60.

## 4. Resultado primário

- limiar: 7.669584751;
- recall oracle: 0.003350 = 0.335%;
- intervalo de 95%: 0.002875 a 0.003825;
- eventos detectados: 134/40.000;
- estratos aprovados: 0/8;
- lotes aprovados: 0/20.

O limite superior ficou em 0.383%, muito abaixo do limite de falha forte de 30%.

## 5. Resultado por estrato

| Estrato | Detecções | N | Recall | Limite inferior 95% |
|---|---:|---:|---:|---:|
| linear__clean | 2 | 5000 | 0.000400 | 0.000071 |
| linear__concurrent | 21 | 5000 | 0.004200 | 0.002816 |
| power_law__clean | 2 | 5000 | 0.000400 | 0.000071 |
| power_law__concurrent | 40 | 5000 | 0.008000 | 0.006044 |
| exponential__clean | 0 | 5000 | 0.000000 | 0.000000 |
| exponential__concurrent | 44 | 5000 | 0.008800 | 0.006744 |
| logistic__clean | 2 | 5000 | 0.000400 | 0.000071 |
| logistic__concurrent | 23 | 5000 | 0.004600 | 0.003146 |

## 6. Falsos alertas

| Família | Alertas | N | FPR | Limite superior 95% |
|---|---:|---:|---:|---:|
| quiet | 0 | 5000 | 0.000000 | 0.000599 |
| shared_ramp | 5 | 5000 | 0.001000 | 0.002101 |
| shared_step | 2 | 5000 | 0.000400 | 0.001259 |
| shared_bump | 12 | 5000 | 0.002400 | 0.003886 |
| shared_oscillation | 19 | 5000 | 0.003800 | 0.005571 |

O FPR passou em todas as famílias. `shared_oscillation` voltou a determinar o limiar.

## 7. Clean versus concurrent

- recall clean: 0.000300;
- recall concurrent: 0.006400.

O recall maior em concurrent não demonstra benefício. A perturbação compartilhada acrescenta estrutura que pode aumentar acidentalmente a correlação com o template exato. Como o mesmo efeito não aparece nos eventos limpos, ele não deve ser interpretado como evidência do sinal astrofísico.

## 8. Métricas secundárias

- AUROC: 0.729311;
- Average Precision: 0.778634.

Novamente, ranking moderado não se converte em detecção no ponto operacional rigoroso.

## 9. Conclusão permitida

> No modelo sintético atual, a informação contida entre onset e \(t_{25}\) é insuficiente para obter recall operacionalmente útil sob FPR máximo de 1% por família, mesmo quando onset e template processado exato são fornecidos.

## 10. Limites da conclusão

Isso não prova que transientes reais sejam indetectáveis. Prova que a combinação específica abaixo não fecha:

- amplitudes finais de 3–7 desvios-padrão;
- somente o primeiro quarto da amplitude;
- ruído e artefatos definidos;
- uma única curva-alvo com referências;
- falso alerta rigoroso por família.

## 11. Próxima mudança lógica

O próximo teste deve alterar somente uma variável: ampliar a janela para \(t_{50}\), mantendo todo o restante igual.

Se o oráculo em \(t_{50}\) passar, a janela de 25% era severa demais. Se também falhar, a revisão deverá avançar para \(t_{75}\), amplitude, cadência ou fonte adicional de informação.
