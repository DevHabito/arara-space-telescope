# ARARA From Zero — Relatório do M9 Final-SNR Threshold at t100

**Estado:** concluído  
**Holdout:** aberto uma única vez  
**Veredito:** `PASS`  
**Nível mínimo aprovado:** `8.0σ`  
**Previsão principal:** confirmada

## 1. Pergunta

Mantendo o contrato em amplitude completa, qual SNR final fixo torna a detecção alinhada-oráculo operacionalmente suficiente?

## 2. Previsão registrada

O primeiro nível aprovado seria \(8\sigma\).

Faixas previstas:

- \(4\sigma\): 15–30%;
- \(6\sigma\): 35–55%;
- \(8\sigma\): 55–75%;
- \(10\sigma\): 70–88%;
- \(12\sigma\): 82–95%.

## 3. Resultado global

| SNR final | Recall | Limite inferior 95% | Limite superior 95% | Estratos aprovados | Lotes aprovados | Passou |
|---:|---:|---:|---:|---:|---:|---|
| 4σ | 0.112500 | 0.108950 | 0.116100 | 0/8 | 0/20 | NÃO |
| 6σ | 0.457900 | 0.452400 | 0.463500 | 2/8 | 0/20 | NÃO |
| 8σ | 0.746000 | 0.741100 | 0.750900 | 8/8 | 20/20 | SIM |
| 10σ | 0.890850 | 0.887300 | 0.894400 | 8/8 | 20/20 | SIM |
| 12σ | 0.950150 | 0.947650 | 0.952600 | 8/8 | 20/20 | SIM |

A curva foi monotônica. As diferenças adjacentes foram:

\[
[0.3454, 0.2881, 0.14484999999999992, 0.05930000000000002].
\]

## 4. Falsos alertas

| Família | FPR | Limite superior 95% |
|---|---:|---:|
| quiet | 0.000000 | 0.000599 |
| shared_ramp | 0.003200 | 0.004856 |
| shared_step | 0.000400 | 0.001259 |
| shared_bump | 0.002000 | 0.003390 |
| shared_oscillation | 0.000000 | 0.000599 |

O FPR passou em todas as famílias. `shared_ramp` determinou o limiar de desenvolvimento:

\[
	heta=9.492495537.
\]

## 5. Métricas secundárias

| SNR | AUROC | Average Precision |
|---:|---:|---:|
| 4σ | 0.956314 | 0.942433 |
| 6σ | 0.985666 | 0.983448 |
| 8σ | 0.994832 | 0.994324 |
| 10σ | 0.997941 | 0.997778 |
| 12σ | 0.999067 | 0.999019 |

## 6. Conclusão permitida

> No modelo sintético atual, com alinhamento-oráculo e observação até a amplitude completa, \(8\sigma\) é o primeiro nível testado que satisfaz simultaneamente recall global, cobertura por estrato, estabilidade por lote e controle de falso alerta.

## 7. Limites

Isso não demonstra que um detector autônomo alcance o mesmo resultado. O M9 conhece onset e template exatos e avalia em \(t_{100}\). O resultado estabelece um requisito de informação, não uma missão validada.

## 8. Próxima pergunta

Com SNR final fixo em \(8\sigma\), qual é a primeira fração do evento que satisfaz o contrato: 25%, 50%, 75% ou 100%?
