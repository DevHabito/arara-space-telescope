# ARARA From Zero — Relatório do M18 Multi-Seed Replication of 13σ at t50

**Estado:** concluído  
**Replicações:** 10/10  
**Veredito:** `INCONCLUSIVE`  
**Decisão:** 13σ não pode ser promovido como requisito robusto em t50

## 1. Pergunta

13σ em t50 fecha o contrato quando calibração, limiar e holdout são repetidos integralmente dez vezes?

## 2. Resultado agregado

- recall agregado: `0.620275`;
- intervalo hierárquico de 95%: `0.601655` a `0.638730`;
- replicações aprovadas: `6/10`;
- replicações com FPR aprovado: `10/10`;
- violação extrema de FPR: `False`.

O limite inferior agregado ficou acima de 0,60, mas somente 6 das 10 replicações passaram. O protocolo exigia pelo menos 8.

## 3. Resultado por replicação

| Replicação | Limiar | Recall | Limite inferior 95% | Estratos | Lotes | FPR | Passou |
|---:|---:|---:|---:|---:|---:|---|---|
| 0 | 7.440330 | 0.597550 | 0.592047 | 6/8 | 20/20 | PASSOU | NÃO |
| 1 | 6.991841 | 0.665600 | 0.660250 | 8/8 | 20/20 | PASSOU | SIM |
| 2 | 7.107828 | 0.648450 | 0.642900 | 8/8 | 20/20 | PASSOU | SIM |
| 3 | 6.978690 | 0.659800 | 0.654350 | 8/8 | 20/20 | PASSOU | SIM |
| 4 | 7.024481 | 0.659800 | 0.654250 | 8/8 | 20/20 | PASSOU | SIM |
| 5 | 7.672711 | 0.572500 | 0.566800 | 6/8 | 19/20 | PASSOU | NÃO |
| 6 | 7.598202 | 0.579350 | 0.573750 | 6/8 | 19/20 | PASSOU | NÃO |
| 7 | 7.356224 | 0.615500 | 0.609900 | 6/8 | 20/20 | PASSOU | SIM |
| 8 | 7.602490 | 0.574900 | 0.569250 | 6/8 | 18/20 | PASSOU | NÃO |
| 9 | 7.211545 | 0.629300 | 0.623800 | 6/8 | 20/20 | PASSOU | SIM |

## 4. Previsão

Previsão pré-registrada:

- 3–7 replicações passariam;
- recall agregado entre 0,56 e 0,62;
- veredito INCONCLUSIVE.

Resultado:

- contagem de passes: `6/10` — confirmada;
- recall agregado: `0.620275` — excedeu a faixa prevista por 0,000275;
- veredito INCONCLUSIVE — confirmado.

A previsão não foi integralmente confirmada. Não arredondamos 0,620275 para 0,620000.

## 5. Comparação robusta

| Condição | Passes | Recall agregado | Intervalo agregado | Veredito |
|---|---:|---:|---:|---|
| 12σ, t50 — M15 | 1/10 | 0.514710 | 0.483404–0.544270 | STRONG_FAIL |
| 13σ, t50 — M18 | 6/10 | 0.620275 | 0.601655–0.638730 | INCONCLUSIVE |
| 14σ, t50 — M17 | 10/10 | 0.663930 | 0.648170–0.680135 | PASS |

O crescimento é coerente, mas o critério de repetibilidade impede promover 13σ.

## 6. Falso alerta

Todas as dez replicações controlaram o FPR. A falha de promoção veio da variabilidade do recall entre calibrações independentes.

## 7. Diagnóstico pós-hoc

Correlação descritiva entre limiar e recall: `-0.996329`.

Faixa dos limiares: `6.978690` a `7.672711`.

Faixa do recall: `0.572500` a `0.665600`.

Esse diagnóstico não altera o veredito.

## 8. Conclusão permitida

> No modelo sintético atual e sob alinhamento-oráculo, 13σ em t50 é uma condição limítrofe: o desempenho agregado supera 60%, mas a condição não passa de forma suficientemente repetível entre calibrações e holdouts independentes.

## 9. Consequência

13σ não deve substituir 14σ como requisito confirmado. O estado rigoroso é:

- 12σ: rejeitado robustamente;
- 13σ: inconclusivo e não promovido;
- 14σ: confirmado robustamente.

## 10. Próxima pergunta

Testar 13,5σ com o mesmo protocolo multi-seed pode verificar se a margem intermediária alcança pelo menos 8/10 replicações.