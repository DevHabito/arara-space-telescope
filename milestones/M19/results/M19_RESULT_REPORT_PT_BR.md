# ARARA From Zero — Relatório do M19 Multi-Seed Replication of 13,5σ at t50

**Estado:** concluído  
**Replicações:** 10/10  
**Veredito:** `INCONCLUSIVE`  
**Decisão:** 13,5σ não pode ser promovido como requisito robusto em t50

## 1. Pergunta

13,5σ em t50 fecha o contrato quando calibração, limiar e holdout são repetidos integralmente dez vezes?

## 2. Resultado agregado

- recall agregado: `0.656570`;
- intervalo hierárquico de 95%: `0.636225` a `0.675620`;
- replicações aprovadas: `7/10`;
- replicações com FPR aprovado: `9/10`;
- violação extrema de FPR: `False`.

O limite inferior agregado ficou acima de 0,60 e a robustez global de FPR foi satisfeita. Porém, somente 7 das 10 replicações passaram. O protocolo exigia pelo menos 8.

## 3. Resultado por replicação

| Replicação | Limiar | Recall | Limite inferior 95% | Estratos | Lotes | FPR | Passou |
|---:|---:|---:|---:|---:|---:|---|---|
| 0 | 7.061191 | 0.692450 | 0.687150 | 8/8 | 20/20 | PASSOU | SIM |
| 1 | 7.751268 | 0.599050 | 0.593500 | 6/8 | 20/20 | PASSOU | NÃO |
| 2 | 7.154863 | 0.676050 | 0.670650 | 8/8 | 20/20 | PASSOU | SIM |
| 3 | 7.208881 | 0.671150 | 0.665700 | 8/8 | 20/20 | PASSOU | SIM |
| 4 | 6.885261 | 0.708400 | 0.703250 | 8/8 | 20/20 | PASSOU | SIM |
| 5 | 7.586125 | 0.622100 | 0.616600 | 7/8 | 20/20 | PASSOU | SIM |
| 6 | 7.825765 | 0.588100 | 0.582500 | 6/8 | 20/20 | PASSOU | NÃO |
| 7 | 7.378980 | 0.651950 | 0.646450 | 8/8 | 20/20 | PASSOU | SIM |
| 8 | 7.049837 | 0.688700 | 0.683500 | 8/8 | 20/20 | FALHOU | NÃO |
| 9 | 7.238035 | 0.667750 | 0.662350 | 8/8 | 20/20 | PASSOU | SIM |

## 4. A replicação 8

A replicação 8 apresentou recall alto, mas não passou porque uma família negativa teve limite superior de FPR:

`FPR_upper = 0.010176 > 0.010000`.

Ela não pode ser contada como aprovada. A diferença é pequena, mas o critério estava congelado antes dos dados.

## 5. Previsão

Previsão pré-registrada:

- 8–10 replicações passariam;
- recall agregado entre 0,630 e 0,655;
- veredito PASS.

Resultado:

- contagem de passes: `7/10` — refutada;
- recall agregado: `0.656570` — excedeu o teto previsto em `0.001570`;
- veredito INCONCLUSIVE — previsão de PASS refutada.

Nenhum limite foi arredondado nem alterado.

## 6. Comparação robusta

| Condição | Passes | Recall agregado | Intervalo agregado | Veredito |
|---|---:|---:|---:|---|
| 12σ, t50 — M15 | 1/10 | 0.514710 | 0.483404–0.544270 | STRONG_FAIL |
| 13σ, t50 — M18 | 6/10 | 0.620275 | 0.601655–0.638730 | INCONCLUSIVE |
| 13,5σ, t50 — M19 | 7/10 | 0.656570 | 0.636225–0.675620 | INCONCLUSIVE |
| 14σ, t50 — M17 | 10/10 | 0.663930 | 0.648170–0.680135 | PASS |

A tendência de melhora é coerente, mas 13,5σ ainda não alcançou a repetibilidade pré-registrada.

## 7. Falso alerta

Nove das dez replicações controlaram o FPR em todas as famílias, satisfazendo a robustez agregada de FPR. Uma replicação ficou ligeiramente acima de 1%, sem ultrapassar o limite extremo de 1,5%.

## 8. Diagnóstico pós-hoc

Correlação descritiva entre limiar e recall: `-0.998244`.

Faixa dos limiares: `6.885261` a `7.825765`.

Faixa do recall: `0.588100` a `0.708400`.

Esse diagnóstico não altera o veredito.

## 9. Conclusão permitida

> No modelo sintético atual e sob alinhamento-oráculo, 13,5σ em t50 apresenta desempenho agregado suficiente, mas não passa de forma repetível em pelo menos 8 das 10 replicações. A condição permanece inconclusiva e não pode substituir 14σ.

## 10. Estado do requisito

- 12σ: rejeitado robustamente;
- 13σ: inconclusivo;
- 13,5σ: inconclusivo, com 7/10 passes;
- 14σ: confirmado robustamente.

O requisito confirmado permanece 14σ. O intervalo não confirmado mais estreito é:

`13,5σ < requisito confirmado <= 14σ`

Isso não afirma que 13,5σ seja matematicamente impossível; afirma apenas que não satisfez o protocolo de robustez.