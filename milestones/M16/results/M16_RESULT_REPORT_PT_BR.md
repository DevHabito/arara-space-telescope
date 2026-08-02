# ARARA From Zero — Relatório do M16 Calibration-Size Stability

**Estado:** concluído  
**Mundos:** 3/3  
**Calibrações:** 900/900  
**Veredito:** `STRONG_FAIL_CALIBRATION_NOT_PRIMARY`  
**Decisão:** o tamanho pequeno da calibração não é a causa principal da falha de 12σ em t50

## 1. Pergunta

A instabilidade de 12σ em t50 é causada principalmente pelo uso de apenas 2.000 negativos por família para calibrar o limiar?

## 2. Desenho

- três mundos independentes;
- 50.000 negativos por família em cada superpool;
- o mesmo holdout entre tamanhos dentro de cada mundo;
- 100 calibrações por tamanho e mundo;
- tamanhos 2.000, 10.000 e 50.000 por família;
- 900 calibrações no total.

## 3. Resultado agregado

| Negativos por família | Calibrações | Largura/estabilidade | Passes | Taxa de passe | FPR aprovado | Recall mediano | Q90 do limite inferior |
|---:|---:|---|---:|---:|---:|---:|---:|
| 2.000 | 300 | mediana W90=1.075258 | 11 | 3.667% | 94.000% | 0.544375 | 0.594318 |
| 10.000 | 300 | mediana W90=0.520539 | 0 | 0.000% | 97.667% | 0.545550 | 0.573150 |
| 50.000 | 300 | mediana W90=0.245539 | 0 | 0.000% | 100.000% | 0.546700 | 0.557610 |

## 4. Estabilização do limiar

Razões de largura W50k/W2k por mundo:

`0.253896, 0.228353, 0.203618`

Mediana da razão: `0.228353`.

Isso representa redução mediana de aproximadamente `77.16%` na largura central de 90% do limiar.

A calibração maior estabilizou fortemente o quantil negativo.

## 5. O resgate não ocorreu

Em 50.000 negativos por família:

- passes: `0/300`;
- taxa de passe: `0.000%`;
- limite superior binomial de 95% da taxa de passe: `0.994%`;
- recall mediano: `0.546700`;
- percentil 90 do limite inferior de recall: `0.557610`;
- FPR aprovado em 100% das calibrações.

Portanto, um limiar mais estável não levou o recall ao contrato de 60%.

## 6. Por que 2.000 produziu alguns passes?

Com 2.000 negativos ocorreram `11/300` passes.

Isso não favorece a calibração pequena. A amostra pequena ocasionalmente subestima a cauda negativa e produz limiares anormalmente baixos. Alguns desses limiares passam por acaso no holdout, enquanto outros violam o FPR.

A evidência disso é:

- FPR aprovado em 2.000: `94.000%`;
- FPR aprovado em 50.000: `100.000%`;
- taxa de passe em 50.000: zero.

O passe raro de uma calibração pequena é uma loteria de limiar, não robustez.

## 7. Previsão

- redução W50k/W2k ≤ 0,40: `CONFIRMADA`;
- taxas de passe ≤ 20%: `CONFIRMADA`;
- recall mediano de 50k entre 0,50 e 0,56: `CONFIRMADA`;
- veredito previsto: `CONFIRMADO`.

Previsão integralmente confirmada: `True`.

## 8. Conclusão permitida

> A calibração com apenas 2.000 negativos aumenta fortemente a variabilidade do limiar, mas não é a causa principal da insuficiência de 12σ em t50. Com 50.000 negativos por família, o limiar estabiliza e nenhuma das 300 calibrações fecha o contrato.

## 9. Consequência

12σ em t50 permanece rejeitado. O próximo teste correto é uma replicação multi-seed completa em 14σ e t50, sem refinar casas decimais em torno de um nível já refutado.