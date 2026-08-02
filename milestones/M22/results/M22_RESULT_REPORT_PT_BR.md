# ARARA From Zero — Relatório do M22 Controlled Onset-Error Tolerance

**Estado:** concluído  
**Replicações:** 10/10  
**Veredito:** `INCONCLUSIVE`  
**Decisão:** tolerância simétrica de ±2 cadências não foi demonstrada

## 1. Pergunta

Em 13,75σ e com endpoint verdadeiro t50, o contrato sobrevive quando o onset entregue ao score erra até duas cadências em qualquer direção?

## 2. Resultado agregado

| Erro δ | Recall agregado | Limite inferior 95% | Limite superior 95% | Passes | FPR robusto | Veredito |
|---:|---:|---:|---:|---:|---|---|
| -4 | 0.706380 | 0.685553 | 0.726260 | 8/10 | NÃO | INCONCLUSIVE |
| -2 | 0.695105 | 0.675860 | 0.712632 | 9/10 | SIM | PASS |
| +0 | 0.682895 | 0.651384 | 0.712171 | 5/10 | NÃO | INCONCLUSIVE |
| +2 | 0.602790 | 0.579140 | 0.625846 | 3/10 | SIM | INCONCLUSIVE |
| +4 | 0.514815 | 0.485649 | 0.542056 | 0/10 | SIM | STRONG_FAIL |

## 3. Resultado decisivo

O contrato exigia passe simultâneo em δ=-2, 0 e +2.

- δ=-2 passou;
- δ=0 ficou inconclusivo;
- δ=+2 ficou inconclusivo.

Logo:

`INCONCLUSIVE`

Não é permitido declarar tolerância de ±2 usando apenas o lado -2 favorável.

## 4. Assimetria observada

O desempenho foi fortemente assimétrico:

- estimar o onset cedo demais preservou ou elevou o score;
- estimar o onset tarde demais reduziu principalmente o recall das formas lineares;
- +4 cadências produziu falha forte.

Taxas agregadas nos estratos lineares:

- `linear__clean`: δ=-4: 0.6775, δ=-2: 0.6392, δ=+0: 0.5788, δ=+2: 0.4117, δ=+4: 0.2677.
- `linear__concurrent`: δ=-4: 0.6707, δ=-2: 0.6248, δ=+0: 0.5658, δ=+2: 0.4189, δ=+4: 0.2877.

A hipótese pré-registrada de recall máximo em δ=0 foi refutada. δ=-4 teve o maior recall pontual agregado, embora não tenha passado o gate de robustez de FPR.

Essa assimetria significa que o score atual não funciona como uma régua neutra de erro de onset. O comprimento do segmento e a posição do template afetam a estatística.

## 5. Falso alerta

Foram registradas `9` combinações replicação–erro–família com limite superior de FPR acima de 1%.

A família `shared_bump` respondeu pela maioria das violações. Nenhuma combinação ultrapassou o limite extremo de 1,5%.

## 6. O ramo δ=0

O ramo exato é matematicamente equivalente ao score-oráculo M9. Um teste pós-hoc de equivalência obteve diferença máxima zero em 100 curvas negativas.

Mesmo assim, neste novo conjunto de seeds:

- apenas 5/10 replicações passaram;
- 7/10 controlaram o FPR em todas as famílias;
- recall agregado: 0,682895;
- limite inferior agregado: 0,651384.

A perda do gate não veio da média de recall, mas da repetibilidade e do controle de FPR entre calibrações independentes.

## 7. Consequência para 13,75σ

M20 e M21 continuam sendo resultados válidos. Porém, o ramo exato independente do M22 acrescenta evidência conflitante.

Resumo descritivo, sem gate retrospectivo:

| Evidência exata | Passes | FPR passes | Recall médio |
|---|---:|---:|---:|
| M20 | 8/10 | 10/10 | 0.659400 |
| M21 | 10/10 | 10/10 | 0.673305 |
| M22_DELTA_0 | 5/10 | 7/10 | 0.682895 |
| POOLED_DESCRIPTIVE | 23/30 | 27/30 | 0.671867 |

O total pós-hoc é 23/30 passes. Esse agrupamento não foi pré-registrado e não recebe veredito formal.

A conclusão prudente é que 13,75σ deixou de ser um requisito completamente assentado. Ele foi confirmado no M21, mas a repetibilidade posterior foi desafiada pelo M22.

## 8. Previsão

- δ=0 passaria: `REFUTADA`;
- δ=-2 passaria: `CONFIRMADA`;
- δ=+2 passaria: `REFUTADA`;
- ao menos um |δ|=4 não passaria: `CONFIRMADA`;
- δ=0 teria maior recall: `REFUTADA`.

Previsão integralmente confirmada: `False`.

## 9. Conclusão permitida

> O sistema atual tolerou um erro de onset de -2 cadências, mas não demonstrou tolerância simétrica de ±2. Um erro tardio de +2 permaneceu inconclusivo e +4 falhou fortemente. O ramo exato também não reproduziu todos os gates neste novo conjunto de calibrações.

## 10. Próximo teste correto

Não é adequado partir diretamente para uma busca livre de onset usando limiares calibrados com apenas 2.000 negativos por família.

O próximo teste deve usar uma calibração operacional estável com 50.000 negativos por família, congelar os limiares e então comparar δ=0, +1 e +2 em dez holdouts independentes. Isso separará erro tardio de onset da loteria do limiar.