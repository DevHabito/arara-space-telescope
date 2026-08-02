# ARARA From Zero — Relatório do M11 SNR Threshold at t75

**Estado:** concluído  
**Holdout:** aberto uma única vez  
**Veredito:** `PASS`  
**SNR mínimo aprovado:** `9.0σ`  
**Previsão de 8,5σ:** não confirmada

## 1. Resultado global

| SNR | Recall | Limite inferior 95% | Limite superior 95% | Estratos | Lotes | Passou |
|---:|---:|---:|---:|---:|---:|---|
| 8.0σ | 0.491550 | 0.485750 | 0.497300 | 2/8 | 0/20 | NÃO |
| 8.5σ | 0.559900 | 0.554150 | 0.565600 | 6/8 | 15/20 | NÃO |
| 9.0σ | 0.624200 | 0.618747 | 0.629802 | 8/8 | 20/20 | SIM |
| 9.5σ | 0.679050 | 0.673650 | 0.684402 | 8/8 | 20/20 | SIM |
| 10.0σ | 0.730100 | 0.725000 | 0.735200 | 8/8 | 20/20 | SIM |

## 2. Resultado decisivo

8,5σ satisfez os critérios de estratos e lotes, mas falhou no recall global:

`R_lower(8.5σ, t75) = 0.55415 < 0.60`

9σ foi o primeiro nível que satisfez tudo:

`R(9σ, t75) = 0.62420`

`R_lower(9σ, t75) = 0.6187475`

- 8/8 estratos aprovados;
- 20/20 lotes aprovados;
- FPR controlado em todas as famílias.

## 3. Falsos alertas

O limiar foi `8.334942818` e a família determinante foi `shared_ramp`.

## 4. Métricas secundárias

| SNR | AUROC | Average Precision |
|---:|---:|---:|
| 8.0σ | 0.984911 | 0.982055 |
| 8.5σ | 0.987587 | 0.985504 |
| 9.0σ | 0.989810 | 0.988255 |
| 9.5σ | 0.991571 | 0.990398 |
| 10.0σ | 0.993065 | 0.992148 |

## 5. Conclusão permitida

> No modelo sintético atual, com onset e template exatos, 9σ é o primeiro nível testado que torna a janela t75 compatível com o contrato de recall e falso alerta.

## 6. Limites

O resultado ainda é um limite-oráculo. Ele não demonstra que um detector autônomo encontre onset e forma em operação. Também não traduz 9σ diretamente em abertura, magnitude limite ou tempo de exposição sem um modelo fotônico instrumental.

## 7. Próxima etapa

O próximo teste lógico é fixar 9σ e verificar se t50 continua falhando ou se a janela aprovada pode ser antecipada.