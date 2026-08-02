# ARARA From Zero — Relatório do M4 Matched-Filter Viability

**Estado:** concluído  
**Holdout:** aberto uma única vez e retomado deterministicamente por lotes após limite técnico do ambiente  
**Veredito:** `STRONG_FAIL`  
**Decisão:** **REVER O CONTRATO ANTES DE CRIAR OUTRO DETECTOR OPERACIONAL**

## 1. Pergunta

Um banco causal de matched filters, informado sobre as famílias possíveis de rise mas sem conhecer onset, duração ou parâmetros verdadeiros, consegue detectar pelo menos metade dos eventos antes de \(t_{25}\), controlando falsos alertas?

## 2. Banco congelado

- candidatos antes da deduplicação: 160;
- templates retidos: 144;
- comprimentos distintos: 34;
- limiar matched filter: 28.133857727;
- limiar SBW-slope: 18.453260422.

## 3. Previsão registrada

\[
0.30\leq R_{MF}\leq0.60.
\]

Para vitória, o limite inferior de 95% deveria ser pelo menos 0,50.

## 4. Resultado primário

- recall matched filter: 0.000700 = 0.0700%;
- limite de 95%: 0.000500 a 0.000925;
- recall SBW-slope: 0.000100;
- diferença MF−SBW: 0.000600;
- intervalo da diferença: 0.000400 a 0.000825.

O matched filter detectou 28 de 40.000 eventos precocemente. A previsão mínima de 30% não foi aproximada.

## 5. Resultado por estrato

| Estrato | Detecções | N | Recall | Limite inferior 95% |
|---|---:|---:|---:|---:|
| linear__clean | 2 | 5000 | 0.000400 | 0.000071 |
| linear__concurrent | 5 | 5000 | 0.001000 | 0.000394 |
| power_law__clean | 2 | 5000 | 0.000400 | 0.000071 |
| power_law__concurrent | 5 | 5000 | 0.001000 | 0.000394 |
| exponential__clean | 4 | 5000 | 0.000800 | 0.000273 |
| exponential__concurrent | 3 | 5000 | 0.000600 | 0.000164 |
| logistic__clean | 1 | 5000 | 0.000200 | 0.000010 |
| logistic__concurrent | 6 | 5000 | 0.001200 | 0.000523 |

Nenhum dos oito estratos alcançou limite inferior de 30%.

## 6. Falsos alertas

| Família | Alertas | N | FPR | Limite superior 95% |
|---|---:|---:|---:|---:|
| quiet | 4 | 5000 | 0.000800 | 0.001830 |
| shared_ramp | 9 | 5000 | 0.001800 | 0.003139 |
| shared_step | 7 | 5000 | 0.001400 | 0.002628 |
| shared_bump | 10 | 5000 | 0.002000 | 0.003390 |
| shared_oscillation | 39 | 5000 | 0.007800 | 0.010176 |

`shared_oscillation` apresentou limite superior de 0.010176, ligeiramente acima do máximo 0,01. Assim, o critério de FPR também falhou.

## 7. Critérios

| Critério | Resultado |
|---|---|
| FPR por família | FALHOU |
| Recall global, limite inferior ≥ 0,50 | FALHOU |
| Seis estratos com limite inferior ≥ 0,30 | FALHOU |
| Quinze lotes com recall ≥ 0,45 | FALHOU |
| Ganho contra SBW ≥ 0,20 | FALHOU |

O limite superior do recall foi 0.000925, muito abaixo do limiar de falha forte de 0,20.

## 8. Métricas secundárias

- AUROC matched filter: 0.787357;
- AUROC SBW-slope: 0.843587;
- AP matched filter: 0.806232;
- AP SBW-slope: 0.868305.

O banco model-aware não superou o SBW no ranking global e não produziu recall precoce útil.

## 9. Interpretação rigorosa

O resultado não é uma prova de impossibilidade matemática absoluta. O banco é finito, o preprocessing é específico e o modelo é sintético.

Entretanto, ele refuta uma hipótese concreta:

> Conhecer aproximadamente as quatro formas de rise e procurá-las causalmente numa grade de duração e estágio não é suficiente para tornar o contrato atual operacional.

A busca por muitos templates aumenta o efeito de múltiplas comparações. Trechos crescentes de oscilações continuam semelhantes aos prefixos de rise e elevam o limiar.

## 10. Próxima pergunta lógica

O próximo teste deve retirar a dificuldade de busca:

> Se onset e forma exata forem fornecidos por um oráculo, há evidência suficiente no segmento até \(t_{25}\)?

Se o oráculo também falhar, o sinal antes de \(t_{25}\) é insuficiente sob o ruído definido. Se o oráculo passar, o gargalo é busca autônoma/múltiplas comparações, não ausência de informação.
