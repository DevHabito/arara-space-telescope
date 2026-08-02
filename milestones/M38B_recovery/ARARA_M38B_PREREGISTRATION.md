# ARARA From Zero — Pré-registro M38B Frozen Latent-Grid Operational Bank

**Versão:** M38B.0  
**Estado:** congelado antes da implementação, calibração e holdouts

## Pergunta

Mantendo as quatro famílias sintéticas, o banco rolling continua operacional quando o valor verdadeiro de `u` é substituído pela grade congelada pelo M38A?

## Grade importada literalmente

`[0.0, 0.25, 0.5, 0.75, 1.0]`

Nenhum ponto poderá ser removido, acrescentado ou deslocado.

## Métodos pareados

- `rolling_full_duration_exact_latent_latency4`: 99 endpoints × 4 formas × 37 durações = 14.652 hipóteses, usando `u_true`.
- `rolling_full_duration_latent_grid5_latency4`: 99 × 4 × 37 × 5 = 73.260 hipóteses.

O controle é matematicamente idêntico ao candidato do M37R e tem poder de veto.

## Matemática preservada

SNR 13,75; endpoints 81–179; hinge causal; guarda e confirmação de oito cadências; AR(1); projeção pelo modo de referência; primeiro cruzamento; duração 24–60; quatro formas; sucesso entre onset e `t50+4`.

## Desempate

No mesmo endpoint e score numericamente idêntico, vence a tupla menor `(índice_u, duração, índice_forma)`. O alerta temporal é sempre o primeiro cruzamento.

## Calibração

Quatro blocos independentes de 50.000 negativos por família, concatenados antes do limiar. Total: 200.000 por família e 1.000.000 de negativos. FPR-alvo empírico: 0,5%, no máximo 1.000 alertas por família.

Seeds: calibração `2026090501`; holdouts `2026090502`; bootstrap agregado `2026090503`; bootstrap pareado `2026090504`.

## Holdouts

Dez holdouts. Cada um: 2.500 positivos por oito estratos, 5.000 negativos por cinco famílias, 20 lotes, 10.000 bootstraps.

## Gates

Controle válido: ≥8/10 passes, limite inferior agregado ≥0,60, FPR robusto em ≥9/10 e sem FPR extremo >1,5%.

Candidato por holdout: FPR superior unilateral ≤0,01 em todas as famílias; recall inferior unilateral ≥0,60; ≥6/8 estratos com limite inferior ≥0,50; ≥15/20 lotes com recall ≥0,55. Agregado: ≥8/10 passes, limite inferior ≥0,60 e FPR robusto.

## Identificação de u

Entre detecções primárias, medir se o vencedor coincide com o ponto da grade mais próximo de `u_true` (empates ao ponto inferior), além do erro absoluto e acurácias dentro de 0,125 e 0,25. Identificação passa se o limite inferior agregado da célula mais próxima ≥0,70 e ≥8/10 holdouts passam.

## Vereditos

- `INVALID_M38B_EXACT_LATENT_CONTROL`
- `PASS_M38B_LATENT_GRID_AND_IDENTIFICATION`
- `PASS_M38B_DETECTION_LATENT_UNRELIABLE`
- `STRONG_FAIL_M38B_LATENT_GRID_BANK`
- `INCONCLUSIVE_M38B_LATENT_GRID_BANK`

## Previsão

Controle: limiar 7,00–7,22; recall 0,745–0,765; 7–10 passes. Candidato: limiar 7,15–7,55; recall 0,725–0,755; diferença −0,030 a 0; 4–9 passes. FPR robusto, identificação abaixo de 70%, veredito mais provável inconclusivo.

## Regras contra puxadinho

Grade importada literalmente; 73.260 hipóteses; quatro blocos completos; nenhum bloco/seed/família/forma/duração/u/endpoint/estrato/lote removido; dez holdouts; nenhum holdout antes do segundo congelamento; nenhum gate alterado depois dos dados; M37R e M38A permanecem inalterados.
