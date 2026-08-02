# ARARA From Zero — Relatório do M10 Earliest Fraction at 8σ

**Estado:** concluído  
**Holdout:** aberto uma única vez  
**Veredito:** `PASS_MAPPING_ONLY`  
**Primeira fração aprovada:** `1.0`  
**Previsão t75:** não confirmada

## 1. Resultado global

| Fração | Recall | Limite inferior 95% | Limite superior 95% | FPR passou | Estratos | Lotes | Passou |
|---:|---:|---:|---:|---|---:|---:|---|
| 0.25 | 0.025950 | 0.024150 | 0.027800 | NÃO | 0/8 | 0/20 | NÃO |
| 0.50 | 0.124950 | 0.121150 | 0.128750 | SIM | 0/8 | 0/20 | NÃO |
| 0.75 | 0.591750 | 0.586150 | 0.597350 | SIM | 8/8 | 20/20 | NÃO |
| 1.00 | 0.829950 | 0.825650 | 0.834250 | SIM | 8/8 | 20/20 | SIM |

## 2. Resultado decisivo em t75

Recall pontual:

`R(t75) = 0.59175`

Limite inferior unilateral de 95%:

`R_lower(t75) = 0.58615`

O contrato exigia:

`R_lower >= 0.60`

Portanto, t75 falhou, mesmo tendo:

- 8/8 estratos acima do critério individual;
- 20/20 lotes acima do critério por lote;
- FPR controlado.

Não é permitido arredondar 58,615% para 60%.

## 3. Fração de 25%

Em t25, além do recall baixo, ao menos uma família negativa violou o limite de FPR no holdout.

## 4. Replicação em t100

`R(t100) = 0.82995`

com limite inferior:

`R_lower(t100) = 0.82565`

Isso replica independentemente que 8σ é suficiente em amplitude completa.

## 5. Métricas secundárias

| Fração | AUROC | Average Precision |
|---:|---:|---:|
| 0.25 | 0.838033 | 0.773153 |
| 0.50 | 0.952104 | 0.937243 |
| 0.75 | 0.985268 | 0.982661 |
| 1.00 | 0.995255 | 0.994534 |

## 6. Conclusão permitida

> Com SNR final de 8σ, apenas a amplitude completa passou o contrato. A janela de 75% ficou próxima, mas formalmente abaixo do limiar global.

## 7. Próximo teste

Fixar t75 e testar a grade estreita de SNR:

`8, 8.5, 9, 9.5, 10`.