# ARARA From Zero — Relatório do M13 SNR Threshold at t50

**Estado:** concluído  
**Holdout:** aberto uma única vez  
**Veredito:** `PASS`  
**SNR mínimo aprovado na grade:** `12.0σ`  
**Previsão de 14σ:** não confirmada

## 1. Resultado global

| SNR | Recall | Limite inferior 95% | Limite superior 95% | Estratos | Lotes | Passou |
|---:|---:|---:|---:|---:|---:|---|
| 10.0σ | 0.444800 | 0.439150 | 0.450550 | 3/8 | 0/20 | NÃO |
| 12.0σ | 0.634250 | 0.628850 | 0.639700 | 8/8 | 20/20 | SIM |
| 14.0σ | 0.770000 | 0.765200 | 0.774800 | 8/8 | 20/20 | SIM |
| 16.0σ | 0.856600 | 0.852600 | 0.860500 | 8/8 | 20/20 | SIM |
| 18.0σ | 0.912850 | 0.909550 | 0.916150 | 8/8 | 20/20 | SIM |

## 2. Resultado decisivo

10σ falhou:

`R_lower(10σ, t50) = 0.43915`

12σ foi o primeiro nível aprovado na grade:

`R(12σ, t50) = 0.63425`

`R_lower(12σ, t50) = 0.62885`

- 8/8 estratos aprovados;
- 20/20 lotes aprovados;
- FPR controlado.

O limiar foi `6.639109612` e a família determinante foi `shared_bump`.

## 3. Métricas secundárias

| SNR | AUROC | Average Precision |
|---:|---:|---:|
| 10.0σ | 0.972755 | 0.967311 |
| 12.0σ | 0.983901 | 0.981842 |
| 14.0σ | 0.990312 | 0.989496 |
| 16.0σ | 0.994091 | 0.993730 |
| 18.0σ | 0.996370 | 0.996177 |

## 4. Conclusão permitida

> No modelo sintético atual e sob alinhamento-oráculo, o requisito em t50 está entre 10σ e 12σ. Na grade grossa testada, 12σ foi o primeiro nível aprovado.

## 5. Próxima pergunta

Refinar o intervalo com 10,5σ, 11σ, 11,5σ e 12σ.