# ARARA From Zero — Relatório do M2 Common-Mode

**Estado:** concluído  
**Holdout:** aberto uma única vez  
**Veredito formal:** `INCONCLUSIVE`  
**Decisão de engenharia:** **NÃO PROMOVER**

## 1. Pergunta

A remoção causal de perturbação compartilhada por oito estrelas de referência melhora o recall precoce de rises localizados no alvo, sob controle de falsos alertas?

## 2. Previsão anterior ao resultado

Foi previsto ganho absoluto entre 0,20 e 0,45. Para promoção, o limite inferior de 95% deveria ser pelo menos 0,15 e o recall common-mode deveria ter limite inferior de pelo menos 0,30.

## 3. Limiares congelados

- target-only: `29.501049042`
- common-mode: `20.106138229`

A família determinante para ambos foi `shared_oscillation`.

## 4. Resultado primário

- recall common-mode: `0.000050` = `0.0050%`;
- recall target-only: `0.000100` = `0.0100%`;
- diferença: `-0.000050`;
- intervalo unilateral bootstrap reportado para a diferença: `-0.000150` a `0.000050`;
- lotes com diferença positiva: `1/20`.

O common-mode detectou 2 de 40.000 eventos precocemente. O target-only detectou 4 de 40.000.

## 5. Falsos alertas do common-mode

| Família | Alertas | N | FPR | Limite superior 95% |
|---|---:|---:|---:|---:|
| quiet | 1 | 5000 | 0.0002 | 0.0009 |
| shared_ramp | 0 | 5000 | 0.0000 | 0.0006 |
| shared_step | 0 | 5000 | 0.0000 | 0.0006 |
| shared_bump | 1 | 5000 | 0.0002 | 0.0009 |
| shared_oscillation | 24 | 5000 | 0.0048 | 0.0067 |

Todas as famílias respeitaram o limite pré-registrado. O problema foi novamente a perda quase total de recall.

## 6. Critérios

| Critério | Resultado |
|---|---|
| FPR common-mode por família | PASSOU |
| Recall common-mode ≥ 0,30 no limite inferior | FALHOU |
| Ganho ≥ 0,15 no limite inferior | FALHOU |
| Não inferioridade em clean | PASSOU |
| 7/8 estratos sem perda | FALHOU |
| 15/20 lotes positivos | FALHOU |

O rótulo formal foi inconclusivo porque o intervalo da diferença inclui zero, e não houve violação de FPR. Pela regra de engenharia, inconclusivo não promove.

## 7. Resultado secundário

- AUROC target-only: `0.633867`;
- AUROC common-mode: `0.800045`;
- AP target-only: `0.697167`;
- AP common-mode: `0.828907`.

A remoção common-mode melhorou o ranking global, mas não a capacidade de cruzar o limiar antes de \(t_{25}\). Portanto, essa melhoria não é uma vitória operacional.

## 8. Diagnóstico matemático pós-hoc

O pipeline M2 primeiro branqueou cada estrela com seu próprio filtro AR(1) e só depois tentou construir a referência comum.

Para uma componente compartilhada \(c_k\), cada estrela passou por:

\[
(1-\widehat\phi_jL)a_jc_k.
\]

Como \(\widehat\phi_j\) varia entre estrelas, a mesma oscilação foi transformada de maneiras diferentes antes da mediana. Assim, não existe necessariamente um único \(q_k\) capaz de representar o componente do alvo após esses filtros distintos.

Essa ordem de operações pode deixar resíduos oscilatórios grandes mesmo quando o artefato original era compartilhado.

Isso não altera o resultado M2. Ele apenas define uma nova hipótese para outro teste:

> estimar e subtrair o common-mode antes do branqueamento individual.

## 9. Conclusão permitida

> A implementação M2 “branquear cada estrela e depois subtrair a mediana das referências” não produziu alerta precoce útil e não confirmou a previsão de ganho common-mode.

## 10. Próxima etapa permitida

O M2 não poderá ser ajustado ou retestado no mesmo holdout. Uma ordem de operações diferente exige:

- novo nome;
- novo pré-registro;
- novas seeds;
- novos dados;
- novo holdout.

A próxima hipótese será chamada M3 Subtract-Before-Whiten.
