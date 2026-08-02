# ARARA From Zero — Relatório do M26 Exact-Onset Control for Split Confirmation

**Estado:** concluído  
**Calibração:** 50.000 negativos por família  
**Holdouts:** 10/10 concluídos  
**Veredito:** `STRONG_FAIL_EXACT_ONSET_SPLIT_CONFIRMATION`  
**Decisão:** o matched filter confirmatório de oito cadências é insuficiente mesmo com onset exato

## 1. Pergunta

O M25 falhou porque o onset foi mal estimado ou porque a confirmação curta de oito cadências era insuficiente?

O M26 manteve exatamente a guarda e o matched filter do M25, mas devolveu o onset exato.

## 2. Calibração

Limiar congelado: `16.623075`.

Família determinante: `shared_step`.

O limiar permaneceu praticamente igual ao M25 e dentro da faixa pré-registrada de 14–18. A família `shared_step` continuou controlando a cauda nula.

## 3. Resultado agregado

- recall agregado: `0.284350`;
- intervalo hierárquico de 95%: `0.282030` a `0.286605`;
- holdouts aprovados: `0/10`;
- holdouts com FPR aprovado: `10/10`;
- violação extrema de FPR: `False`.

O limite superior agregado permaneceu em apenas 28,66%, abaixo do requisito de 60%. Isso produz falha forte independentemente dos demais gates.

## 4. Resultado por holdout

| Holdout | Recall | Limite inferior 95% | AUROC | AP | FPR | Passou |
|---:|---:|---:|---:|---:|---|---|
| 0 | 0.277200 | 0.272150 | 0.986414 | 0.979061 | SIM | NÃO |
| 1 | 0.286100 | 0.280900 | 0.986667 | 0.980164 | SIM | NÃO |
| 2 | 0.285500 | 0.280300 | 0.985955 | 0.977915 | SIM | NÃO |
| 3 | 0.288400 | 0.283250 | 0.986237 | 0.978915 | SIM | NÃO |
| 4 | 0.283450 | 0.278400 | 0.986300 | 0.978980 | SIM | NÃO |
| 5 | 0.285600 | 0.280450 | 0.986522 | 0.979341 | SIM | NÃO |
| 6 | 0.288050 | 0.282950 | 0.987001 | 0.980361 | SIM | NÃO |
| 7 | 0.283650 | 0.278550 | 0.986691 | 0.979854 | SIM | NÃO |
| 8 | 0.283100 | 0.278050 | 0.986158 | 0.978519 | SIM | NÃO |
| 9 | 0.282450 | 0.277247 | 0.986056 | 0.979037 | SIM | NÃO |

## 5. Resultado por forma

| Estrato | Recall |
|---|---:|
| `exponential__clean` | 0.227040 |
| `exponential__concurrent` | 0.386960 |
| `linear__clean` | 0.260320 |
| `linear__concurrent` | 0.413640 |
| `logistic__clean` | 0.121240 |
| `logistic__concurrent` | 0.279600 |
| `power_law__clean` | 0.211560 |
| `power_law__concurrent` | 0.374440 |

Nenhum estrato alcançou o gate individual de 50% com margem. As formas concorrentes tiveram recall maior, mas isso reflete a estrutura do artefato simultâneo no modelo e não uma vantagem física do sinal.

## 6. Falso alerta

Todos os dez holdouts controlaram o FPR e nenhuma combinação ultrapassou 1%.

| Família | Alertas totais | Curvas | Taxa | Maior limite superior 95% |
|---|---:|---:|---:|---:|
| `quiet` | 0 | 50000 | 0.000000 | 0.000599 |
| `shared_bump` | 62 | 50000 | 0.001240 | 0.003139 |
| `shared_oscillation` | 13 | 50000 | 0.000260 | 0.001259 |
| `shared_ramp` | 62 | 50000 | 0.001240 | 0.003390 |
| `shared_step` | 263 | 50000 | 0.005260 | 0.009270 |

A falha não veio de falso alerta descontrolado. O limiar conservador funcionou, mas o score de oito pontos não acumulou informação suficiente para superar a cauda de degraus compartilhados.

## 7. Comparação causal M25 → M26

- M25, onset estimado: recall `0.270425`;
- M26, onset exato: recall `0.284350`;
- ganho absoluto: `0.013925` (1.39 pontos percentuais);
- razão: `1.0515x`;
- limiar M25: `16.778311`;
- limiar M26: `16.623075`.

O onset exato recuperou apenas cerca de 1,39 ponto percentual. Como M25 e M26 usam seeds e calibrações independentes, essa diferença é descritiva, não um efeito pareado. Ainda assim, o M26 isolado demonstra formalmente que o score curto falha mesmo sem erro de onset.

## 8. Decomposição do gargalo

O resultado elimina a interpretação de que a dobradiça era, sozinha, responsável pelo recall de 27% do M25.

> O principal gargalo do ramo M25–M26 é a confirmação de oito cadências sob uma cauda nula dominada por `shared_step`.

A dobradiça continua inadequada para localizar o onset, como mostrou o M25, mas corrigir o onset não resgata esta estatística de confirmação.

## 9. Previsão

- limiar entre 14 e 18: `CONFIRMADA`;
- recall entre 0,55 e 0,68: `REFUTADA`;
- 3–7 passes: `REFUTADA`;
- veredito inconclusivo: `REFUTADA`;
- previsão integralmente confirmada: `False`.

A previsão subestimou a severidade. O controle produziu falha forte, não resultado limítrofe.

## 10. Conclusão permitida

> Com onset exato, endpoint exato e template exato, o matched filter restrito às oito últimas cadências até t50 alcançou somente 28,44% de recall e falhou em todos os holdouts. Portanto, a confirmação curta do M25 é insuficiente dentro do modelo atual.

## 11. Consequência metodológica

Não é científico testar outro estimador de onset sobre a mesma confirmação de oito pontos. O downstream já foi rejeitado sob informação-oráculo.

## 12. Próximo teste correto

O M27 deve manter onset exato e aumentar apenas a confirmação de oito para 16 cadências, com uma guarda e a mesma calibração de 50.000 negativos por família.

- se 16 cadências passarem, o caminho operacional volta a existir com uma janela confirmatória maior;
- se falharem fortemente, a próxima comparação será 24 cadências ou uma estatística explicitamente resistente a degraus;
- somente depois de validar o downstream deve-se voltar à estimativa autônoma de onset.