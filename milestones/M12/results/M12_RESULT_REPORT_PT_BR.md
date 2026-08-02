# ARARA From Zero — Relatório do M12 Earliest Fraction at 9σ

**Estado:** concluído  
**Holdout:** aberto uma única vez  
**Veredito:** `PASS`  
**Primeira fração aprovada:** `0.75`  
**Previsão t75:** confirmada

## 1. Resultado global

| Fração | Recall | Limite inferior 95% | Limite superior 95% | FPR | Estratos | Lotes | Passou |
|---:|---:|---:|---:|---|---:|---:|---|
| 0.25 | 0.021950 | 0.020250 | 0.023650 | PASSOU | 0/8 | 0/20 | NÃO |
| 0.50 | 0.174750 | 0.170347 | 0.179150 | PASSOU | 0/8 | 0/20 | NÃO |
| 0.75 | 0.634850 | 0.629350 | 0.640350 | PASSOU | 8/8 | 20/20 | SIM |
| 1.00 | 0.856450 | 0.852450 | 0.860350 | PASSOU | 8/8 | 20/20 | SIM |

## 2. Resultado decisivo

Em t50:

`R(t50) = 0.17475`

`R_lower(t50) = 0.1703475`

A janela continua muito abaixo do contrato.

Em t75:

`R(t75) = 0.63485`

`R_lower(t75) = 0.62935`

- 8/8 estratos aprovados;
- 20/20 lotes aprovados;
- FPR controlado;
- critério global aprovado.

## 3. Replicação

O resultado t75 replica de forma independente o M11, no qual 9σ também foi o primeiro nível aprovado nessa janela.

## 4. Métricas secundárias

| Fração | AUROC | Average Precision |
|---:|---:|---:|
| 0.25 | 0.861028 | 0.806539 |
| 0.50 | 0.963155 | 0.952830 |
| 0.75 | 0.989511 | 0.988503 |
| 1.00 | 0.997004 | 0.996642 |

## 5. Conclusão permitida

> No modelo sintético atual e sob alinhamento-oráculo, 9σ permite satisfazer o contrato a partir de t75. A janela t50 permanece insuficiente.

## 6. Limite

O resultado não valida um detector autônomo. Onset e template exatos continuam sendo fornecidos.

## 7. Próxima pergunta

Fixar t50 e medir qual SNR final é necessário para fechar o contrato.