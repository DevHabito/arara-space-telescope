# ARARA From Zero — Relatório do M23 Stable Calibration and Late-Onset Tolerance

**Estado:** concluído  
**Calibração:** 50.000 negativos por família, congelada antes dos holdouts  
**Holdouts:** 10/10 concluídos  
**Veredito:** `PASS_LATE_ONSET_PLUS1`  
**Decisão:** tolerância tardia de uma cadência demonstrada; duas cadências rejeitadas

## 1. Pergunta

Com uma calibração grande e única, 13,75σ em t50 tolera onset fornecido uma ou duas cadências tarde?

## 2. Limiar congelado

| Erro δ | Limiar | Família determinante |
|---:|---:|---|
| +0 | 7.335540 | `shared_bump` |
| +1 | 7.255368 | `shared_oscillation` |
| +2 | 7.285589 | `shared_oscillation` |

Nenhum limiar foi recalibrado depois da abertura dos holdouts.

## 3. Resultado agregado

| Erro δ | Recall agregado | Limite inferior 95% | Limite superior 95% | Holdouts aprovados | FPR robusto | Veredito |
|---:|---:|---:|---:|---:|---|---|
| +0 | 0.670780 | 0.668325 | 0.673135 | 10/10 | SIM | PASS |
| +1 | 0.641555 | 0.639115 | 0.644010 | 10/10 | SIM | PASS |
| +2 | 0.594090 | 0.591915 | 0.596310 | 0/10 | SIM | STRONG_FAIL |

## 4. Resultado decisivo

### Onset exato

- 10/10 holdouts passaram;
- FPR passou em 10/10;
- recall agregado: 0,670780;
- limite inferior: 0,668325.

### Onset uma cadência tarde

- 10/10 holdouts passaram;
- FPR passou em 10/10;
- recall agregado: 0,641555;
- limite inferior: 0,639115.

### Onset duas cadências tarde

- 0/10 holdouts passaram;
- FPR passou em 10/10;
- recall agregado: 0,594090;
- limite superior: 0,596310.

Como o limite superior inteiro permaneceu abaixo de 0,60, +2 sofreu falha forte.

## 5. Veredito global

δ=0 e δ=+1 passaram, enquanto δ=+2 falhou fortemente.

`PASS_LATE_ONSET_PLUS1`

Assim, o sistema atual demonstrou tolerância condicionada a um atraso de uma cadência, mas não de duas.

## 6. Queda de desempenho

A perda de recall foi monotônica:

- 0 → +1: queda absoluta de 0,029225;
- +1 → +2: queda absoluta de 0,047465;
- 0 → +2: queda absoluta de 0,076690.

O segundo passo causa dano maior que o primeiro.

Taxas agregadas nas formas lineares:

- `linear__clean`: δ=+0: 0.5633, δ=+1: 0.4922, δ=+2: 0.4050.
- `linear__concurrent`: δ=+0: 0.5529, δ=+1: 0.4912, δ=+2: 0.4121.

## 7. Efeito da calibração estável

No M22, o ramo exato sofreu instabilidade de FPR e passou em apenas 5/10 replicações. No M23, com os limiares grandes e congelados, o ramo exato passou em 10/10 holdouts e controlou o FPR em todos.

Isso sustenta que a loteria de limiar do M22 afetava fortemente o ramo δ=0.

Para δ=+2, porém, a estabilização não produziu resgate:

- M22: inconclusivo, 3/10 passes;
- M23: falha forte, 0/10 passes;
- FPR robusto em M23: 10/10.

Portanto, a insuficiência de +2 não pode ser atribuída à instabilidade do limiar.

## 8. Previsão

- δ=0 passaria: `CONFIRMADA`;
- δ=+1 passaria: `CONFIRMADA`;
- δ=+2 seria inconclusivo: `REFUTADA`;
- FPR robusto nos três: `CONFIRMADA`;
- recall estritamente decrescente: `CONFIRMADA`;
- veredito global previsto: `CONFIRMADO`.

Previsão integralmente confirmada: `False`.

A previsão não foi integralmente confirmada porque +2 não ficou inconclusivo: falhou fortemente.

## 9. Conclusão permitida

> Condicionado a uma calibração única de 50.000 negativos por família, 13,75σ em t50 tolera robustamente um onset fornecido uma cadência tarde. Um atraso de duas cadências é insuficiente e falhou fortemente.

## 10. Limites

- o endpoint t50 continua exato;
- forma e duração continuam exatas;
- o resultado é condicionado a uma calibração grande específica;
- M23 não testa busca autônoma de onset;
- M23 não mede variabilidade entre várias calibrações independentes de 50.000 negativos.

## 11. Próxima etapa correta

O próximo teste deve introduzir um estimador causal de onset cujo erro seja avaliado antes do score. O contrato operacional inicial deve exigir que pelo menos 90% dos onsets estimados não atrasem mais que uma cadência, pois +2 já foi rejeitado.