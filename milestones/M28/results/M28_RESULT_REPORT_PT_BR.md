# ARARA From Zero — Relatório do M28 Paired Confirmation-Length Map

**Estado:** concluído  
**Calibração:** 50.000 negativos por família  
**Holdouts:** 10/10  
**Comprimentos:** 8, 16, 24 e intervalo completo, avaliados nas mesmas curvas  
**Veredito:** `STRONG_FAIL_ALL_LENGTHS`  
**Decisão:** rejeitar toda a família atual de matched filters não centrados para confirmação em t50

## 1. Pergunta

O fracasso dos M26–M27 dependia do comprimento ou refletia um problema estrutural da estatística? Para responder sem confundir seeds, cada curva recebeu simultaneamente quatro scores com limiares próprios.

## 2. Convenção estatística

Os gates usam limites unilaterais de 95%:

- limite inferior: quantil 5%;
- limite superior: quantil 95%.

Quando mostrados juntos, os dois números equivalem ao intervalo central de 90%; não são rotulados como intervalo bilateral de 95%.

## 3. Resultado agregado

| Comprimento | Limiar | Recall | Limite inferior unilateral 95% | Limite superior unilateral 95% | Passes | FPR | Veredito |
|---|---:|---:|---:|---:|---:|---:|---|
| `8` | 16.317589 | 0.304230 | 0.302100 | 0.306330 | 0/10 | 10/10 | STRONG_FAIL |
| `16` | 21.132420 | 0.179290 | 0.177360 | 0.181155 | 0/10 | 10/10 | STRONG_FAIL |
| `24` | 23.170723 | 0.134650 | 0.133040 | 0.136205 | 0/10 | 10/10 | STRONG_FAIL |
| `full` | 24.072241 | 0.116215 | 0.114735 | 0.117690 | 0/10 | 10/10 | STRONG_FAIL |

Todos os quatro comprimentos falharam fortemente:

`STRONG_FAIL_ALL_LENGTHS`

Nenhum holdout passou em qualquer comprimento.

## 4. Curva pareada do comprimento

O resultado foi estritamente monotônico nas dez replicações:

\[
R_8 > R_{16} > R_{24} > R_{\mathrm{full}}.
\]

Valores agregados:

\[R_8=0{,}304230,\]

\[R_{16}=0{,}179290,\]

\[R_{24}=0{,}134650,\]

\[R_{\mathrm{full}}=0{,}116215.\]

Em todos os 10/10 holdouts, oito cadências superaram 16, 24 e full. Portanto, a queda não é explicável por seeds diferentes.

Diferenças médias pareadas:

- `8 - 16`: `0.124940`; o comprimento da esquerda venceu em `10/10` holdouts.
- `8 - 24`: `0.169580`; o comprimento da esquerda venceu em `10/10` holdouts.
- `8 - full`: `0.188015`; o comprimento da esquerda venceu em `10/10` holdouts.
- `16 - 24`: `0.044640`; o comprimento da esquerda venceu em `10/10` holdouts.
- `16 - full`: `0.063075`; o comprimento da esquerda venceu em `10/10` holdouts.
- `24 - full`: `0.018435`; o comprimento da esquerda venceu em `10/10` holdouts.

## 5. Crescimento do limiar

| Comprimento | Limiar | Mudança relativa | Família determinante |
|---|---:|---:|---|
| `8` | 16.317589 | — | `shared_step` |
| `16` | 21.132420 | 29.51% | `shared_step` |
| `24` | 23.170723 | 9.65% | `shared_step` |
| `full` | 24.072241 | 3.89% | `shared_step` |

A mesma família determinou todos os limiares:

`shared_step`.

Aumentar a janela fornece mais suporte tanto ao sinal verdadeiro quanto ao degrau compartilhado. Nesta estatística não centrada, a cauda nula cresce mais rapidamente do que a capacidade operacional de detecção.

## 6. Falso alerta

Todos os comprimentos controlaram o FPR em 10/10 holdouts. Nenhuma família ultrapassou 1%, e não houve violação extrema.

Portanto, a falha não é consequência de gates instáveis. O controle de FPR funciona, mas exige limiares incompatíveis com recall de 60%.

## 7. Ranking versus operação

| Comprimento | AUROC médio | AP média | Recall operacional |
|---|---:|---:|---:|
| `8` | 0.986799 | 0.979894 | 0.304230 |
| `16` | 0.980874 | 0.969365 | 0.179290 |
| `24` | 0.978092 | 0.963841 | 0.134650 |
| `full` | 0.977151 | 0.961786 | 0.116215 |

O ranking permanece alto, mas isso não salva o detector no regime de falso alerta exigido. AUROC alto não equivale a um ponto operacional utilizável na cauda extrema.

## 8. Relação com o M23

O resultado não refuta o M23. O M23 usava uma estatística correlacional t, com centralização e normalização por variância. O M28 usa matched filter não centrado:

\[
Z=\frac{r^\top h}{\lVert h\rVert_2}.
\]

Logo, o que foi rejeitado é esta família específica de matched filters, não toda possibilidade de utilizar o intervalo completo.

## 9. Previsão

- nenhum comprimento passaria: `CONFIRMADA`;
- todos falhariam fortemente: `CONFIRMADA`;
- limiares cresceriam estritamente: `CONFIRMADA`;
- recall cairia estritamente: `CONFIRMADA`;
- shared_step dominaria 16, 24 e full: `CONFIRMADA`;
- todas as faixas de recall: `CONFIRMADAS`.

Previsão integralmente confirmada: `True`.

Isso confirma o diagnóstico de falha; não constitui validação prática do ARARA.

## 10. Conclusão permitida

> No modelo sintético atual, com onset, endpoint, forma e duração exatos, nenhum dos matched filters não centrados de 8, 16, 24 ou intervalo completo satisfaz o contrato em t50. O comprimento maior piora de forma pareada porque a família shared_step eleva o limiar mais rapidamente do que o sinal ganha detectabilidade operacional.

## 11. Consequência metodológica

Não há justificativa para testar 32, 48 ou outro comprimento dentro da mesma estatística. O mapa pareado já mostrou a direção.

O próximo teste deve mudar apenas a estatística, não o comprimento. A hipótese mais direta é projetar explicitamente componentes de nuisance — constante, degrau e rampa — antes de correlacionar com o template.

Esse detector deverá ser comparado prospectivamente ao baseline L=8 nas mesmas curvas. Um eventual ganho exigirá limiar próprio e confirmação independente posterior.