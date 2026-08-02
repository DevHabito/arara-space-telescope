# ARARA From Zero — Relatório do M20 Adaptive Refinement at 13,75σ, t50

**Estado:** concluído  
**Replicações:** 10/10  
**Veredito científico:** `PASS_REFINEMENT_CANDIDATE`  
**Veredito numérico:** `PASS`  
**Decisão:** 13,75σ torna-se candidato, mas ainda não substitui 14σ

## 1. Resultado agregado

- recall agregado: `0.659400`;
- intervalo hierárquico de 95%: `0.636240` a `0.682195`;
- replicações aprovadas: `8/10`;
- replicações com FPR aprovado: `10/10`;
- violação extrema de FPR: `False`.

Todos os gates numéricos foram satisfeitos. Como 13,75σ foi escolhido adaptativamente após M19 e M17, o resultado é candidato e exige confirmação independente.

## 2. Resultado por replicação

| Replicação | Limiar | Recall | Limite inferior 95% | Estratos | Lotes | FPR | Passou |
|---:|---:|---:|---:|---:|---:|---|---|
| 0 | 7.853364 | 0.597500 | 0.591850 | 6/8 | 20/20 | PASSOU | NÃO |
| 1 | 7.733836 | 0.622650 | 0.617150 | 7/8 | 20/20 | PASSOU | SIM |
| 2 | 6.966505 | 0.716050 | 0.710950 | 8/8 | 20/20 | PASSOU | SIM |
| 3 | 7.413219 | 0.658950 | 0.653400 | 8/8 | 20/20 | PASSOU | SIM |
| 4 | 7.927001 | 0.590600 | 0.584900 | 6/8 | 19/20 | PASSOU | NÃO |
| 5 | 7.068670 | 0.703750 | 0.698450 | 8/8 | 20/20 | PASSOU | SIM |
| 6 | 7.082855 | 0.702150 | 0.696900 | 8/8 | 20/20 | PASSOU | SIM |
| 7 | 7.622900 | 0.634400 | 0.628800 | 7/8 | 20/20 | PASSOU | SIM |
| 8 | 7.177704 | 0.694400 | 0.689097 | 8/8 | 20/20 | PASSOU | SIM |
| 9 | 7.327849 | 0.673550 | 0.668200 | 8/8 | 20/20 | PASSOU | SIM |

## 3. Previsão

- 8–10 replicações passariam: confirmada;
- recall agregado entre 0,645 e 0,675: confirmada;
- resultado candidato: confirmado.

Previsão integralmente confirmada: `True`.

## 4. Comparação

| SNR | Passes | Recall agregado | Estado |
|---:|---:|---:|---|
| 13σ | 6/10 | 0.620275 | Inconclusivo |
| 13,5σ | 7/10 | 0.656570 | Inconclusivo |
| 13,75σ | 8/10 | 0.659400 | Candidato |
| 14σ | 10/10 | 0.663930 | Confirmado |

## 5. Conclusão permitida

> 13,75σ satisfez prospectivamente o contrato numérico em t50, mas ainda não é requisito confirmado porque o nível foi selecionado por refinamento adaptativo.

## 6. Próxima etapa obrigatória

Executar M21 no mesmo nível de 13,75σ, com seeds inteiramente novas e sem nova escolha de SNR. Somente um PASS confirmatório permitirá substituir 14σ.