# ARARA From Zero — Relatório do M17 Multi-Seed Replication of 14σ at t50

**Estado:** concluído  
**Replicações:** 10/10  
**Veredito:** `PASS`  
**Decisão:** 14σ é requisito robusto provisório em t50 no modelo-oráculo

## 1. Pergunta

14σ em t50 fecha o contrato quando calibração, limiar e holdout são repetidos integralmente dez vezes?

## 2. Resultado agregado

- recall agregado: `0.663930`;
- intervalo hierárquico unilateral de 95%: `0.648170` a `0.680135`;
- replicações aprovadas: `10/10`;
- replicações com FPR aprovado: `10/10`;
- violação extrema de FPR: `False`.

O limite inferior agregado permaneceu acima de 0,60.

## 3. Resultado por replicação

| Replicação | Limiar | Recall | Limite inferior 95% | Estratos | Lotes | FPR | Passou |
|---:|---:|---:|---:|---:|---:|---|---|
| 0 | 7.798361 | 0.626800 | 0.621250 | 6/8 | 20/20 | PASSOU | SIM |
| 1 | 7.748918 | 0.637700 | 0.632150 | 7/8 | 20/20 | PASSOU | SIM |
| 2 | 7.525536 | 0.664550 | 0.659150 | 8/8 | 20/20 | PASSOU | SIM |
| 3 | 7.907470 | 0.617250 | 0.611750 | 7/8 | 20/20 | PASSOU | SIM |
| 4 | 7.299476 | 0.688650 | 0.683300 | 8/8 | 20/20 | PASSOU | SIM |
| 5 | 7.394844 | 0.682450 | 0.677100 | 8/8 | 20/20 | PASSOU | SIM |
| 6 | 7.107209 | 0.717650 | 0.712450 | 8/8 | 20/20 | PASSOU | SIM |
| 7 | 7.406895 | 0.681650 | 0.676350 | 8/8 | 20/20 | PASSOU | SIM |
| 8 | 7.340681 | 0.681850 | 0.676600 | 8/8 | 20/20 | PASSOU | SIM |
| 9 | 7.699231 | 0.640750 | 0.635350 | 8/8 | 20/20 | PASSOU | SIM |

## 4. Previsão

Previsão pré-registrada:

- 8–10 replicações passariam;
- recall agregado entre 0,68 e 0,78;
- veredito PASS.

Resultado:

- contagem de passes: `10/10` — confirmada;
- recall agregado: `0.663930` — abaixo da faixa prevista;
- veredito PASS — confirmado.

A previsão não foi integralmente confirmada porque o recall agregado foi menor que o antecipado.

## 5. Comparação com 12σ

| Condição | Passes | Recall agregado | Intervalo agregado | Veredito |
|---|---:|---:|---:|---|
| 12σ, t50 (M15) | 1/10 | 0.514710 | 0.483404–0.544270 | STRONG_FAIL |
| 14σ, t50 (M17) | 10/10 | 0.663930 | 0.648170–0.680135 | PASS |

A diferença não pode ser atribuída apenas ao tamanho da calibração: o M16 mostrou que elevar a calibração para 50.000 negativos estabiliza o limiar, mas não resgata 12σ.

## 6. Falso alerta

Todas as dez replicações controlaram o FPR. Nenhuma apresentou limite superior acima de 1,5%.

## 7. Diagnóstico pós-hoc

Correlação descritiva entre limiar e recall: `-0.996263`.

Faixa dos limiares: `7.107209` a `7.907470`.

Faixa do recall: `0.617250` a `0.717650`.

O diagnóstico não altera o veredito.

## 8. Conclusão permitida

> No modelo sintético atual e sob alinhamento-oráculo, 14σ em t50 satisfaz robustamente o contrato em dez replicações prospectivas independentes.

## 9. Limites

14σ não foi demonstrado como mínimo matemático. O que foi estabelecido é:

- 12σ foi rejeitado robustamente;
- 14σ foi confirmado robustamente;
- o limiar robusto está no intervalo testado `(12σ, 14σ]`.

Também permanece sendo um limite-oráculo: onset e template exatos são fornecidos.

## 10. Próxima pergunta

Uma replicação multi-seed em 13σ pode refinar o intervalo sem abandonar o protocolo.