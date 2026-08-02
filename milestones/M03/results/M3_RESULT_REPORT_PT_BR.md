# ARARA From Zero — Relatório do M3 Subtract-Before-Whiten

**Estado:** concluído  
**Holdout:** aberto uma única vez  
**Veredito:** `STRONG_FAIL`  
**Decisão:** **REJEITAR M3 NESTA FORMA**

## 1. Pergunta

Subtrair o common-mode antes do branqueamento AR(1) melhora o recall precoce em relação a branquear antes de subtrair?

## 2. Previsão registrada

- ganho de recall entre 0,10 e 0,30;
- limiar SBW menor;
- ganho maior em contextos concurrent;
- perda clean menor que 0,03.

## 3. Desenvolvimento

- limiar WBS: `19.503551483`;
- limiar SBW: `19.586488724`.

A previsão de limiar menor falhou antes do holdout:

\[
	heta_{SBW}>	heta_{WBS}.
\]

A família determinante continuou sendo `shared_oscillation`.

## 4. Resultado primário

- recall SBW: `0.000100`;
- recall WBS: `0.000100`;
- diferença: `0.000000`;
- intervalo bootstrap da diferença: `0.000000` a `0.000000`;
- lotes com vantagem SBW: `0/20`.

Os dois métodos detectaram 4 de 40.000 eventos precocemente. As decisões emparelhadas produziram diferença exatamente zero em todos os estratos.

## 5. Falsos alertas SBW

| Família | Alertas | N | FPR | Limite superior 95% |
|---|---:|---:|---:|---:|
| quiet | 0 | 5000 | 0.0000 | 0.0006 |
| shared_ramp | 0 | 5000 | 0.0000 | 0.0006 |
| shared_step | 1 | 5000 | 0.0002 | 0.0009 |
| shared_bump | 0 | 5000 | 0.0000 | 0.0006 |
| shared_oscillation | 23 | 5000 | 0.0046 | 0.0065 |

O controle de FPR passou.

## 6. Critérios

| Critério | Resultado |
|---|---|
| FPR SBW por família | PASSOU |
| Recall SBW ≥ 0,20 | FALHOU |
| Ganho ≥ 0,10 | FALHOU |
| Não inferioridade clean | PASSOU |
| 7/8 estratos sem perda | PASSOU |
| 15/20 lotes positivos | FALHOU |
| Limiar SBW menor | FALHOU |

A falha é forte porque o limite superior da diferença foi zero. Não há sinal de ganho positivo.

## 7. Métricas secundárias

- AUROC WBS: `0.800199`;
- AUROC SBW: `0.843183`;
- AP WBS: `0.831341`;
- AP SBW: `0.868365`.

SBW melhorou ranking global e reduziu falsos alertas de shared_oscillation de 30 para 23, mas isso não alterou o alerta precoce.

## 8. Interpretação

A troca de ordem corrige uma preocupação algébrica legítima, mas não resolve o gargalo operacional. O detector causal de inclinação continua exigindo um limiar próximo de 20 para controlar segmentos crescentes de oscilações.

A pergunta correta agora não é “qual peso devemos alterar?”, mas:

> Há informação suficiente antes de \(t_25\) para distinguir os rises definidos, sob o FPR exigido?

## 9. Conclusão permitida

> No modelo M3, subtract-before-whiten não apresentou qualquer ganho de recall precoce sobre whiten-before-subtract.

## 10. Próximo teste

O próximo teste será um limite de viabilidade com banco causal de matched filters. Ele não tentará provar que o ARARA funciona; tentará descobrir se o contrato de sinal, ruído, \(t_25\) e FPR é detectável mesmo por um método muito mais próximo do ótimo.
