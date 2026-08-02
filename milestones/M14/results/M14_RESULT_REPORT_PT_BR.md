# ARARA From Zero — Relatório do M14 Refined SNR Threshold at t50

**Estado:** concluído  
**Holdout:** aberto uma única vez  
**Veredito:** `INCONCLUSIVE`  
**Previsão de primeiro passe em 12σ:** não confirmada

## 1. Resultado global

| SNR | Recall | Limite inferior 95% | Limite superior 95% | Estratos | Lotes | Passou |
|---:|---:|---:|---:|---:|---:|---|
| 10.5σ | 0.459450 | 0.453800 | 0.465150 | 3/8 | 0/20 | NÃO |
| 11.0σ | 0.507900 | 0.502150 | 0.513700 | 4/8 | 0/20 | NÃO |
| 11.5σ | 0.554600 | 0.548900 | 0.560150 | 5/8 | 12/20 | NÃO |
| 12.0σ | 0.598200 | 0.592650 | 0.603850 | 6/8 | 20/20 | NÃO |

## 2. Resultado decisivo em 12σ

`R(12σ, t50) = 0.59820`

`R_lower(12σ, t50) = 0.59265`

O contrato exigia limite inferior de pelo menos 0,60. Portanto, 12σ falhou formalmente.

Mesmo assim:

- 6/8 estratos atingiram o critério individual;
- 20/20 lotes atingiram o critério de lote;
- FPR permaneceu controlado.

## 3. Divergência com M13

No M13, 12σ passou com:

`R_lower = 0.62885`

No M14, com seeds novas e nova calibração:

`R_lower = 0.59265`

Não é correto escolher apenas M13. A divergência mostra sensibilidade à realização e ao limiar calibrado.

## 4. Métricas secundárias

| SNR | AUROC | Average Precision |
|---:|---:|---:|
| 10.5σ | 0.975367 | 0.971152 |
| 11.0σ | 0.978478 | 0.975084 |
| 11.5σ | 0.981148 | 0.978414 |
| 12.0σ | 0.983442 | 0.981231 |

## 5. Conclusão permitida

> O requisito em t50 não pode ser fixado em 12σ com base em uma única execução favorável. O resultado é instável entre duas replicações prospectivas independentes.

## 6. Próxima etapa

Executar uma replicação prospectiva multi-seed do procedimento completo em 12σ e t50.