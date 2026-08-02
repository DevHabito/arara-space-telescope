# ARARA From Zero — Relatório do M15 Multi-Seed Replication of 12σ at t50

**Estado:** concluído  
**Replicações:** 10/10 concluídas  
**Veredito:** `STRONG_FAIL`  
**Decisão:** rejeitar 12σ como requisito robusto em t50

## 1. Pergunta

12σ em t50 permanece aprovado quando o procedimento completo — calibração, limiar e holdout — é repetido dez vezes com seeds independentes?

## 2. Resultado agregado

- recall agregado: `0.514710`;
- limite inferior hierárquico de 95%: `0.483404`;
- limite superior hierárquico de 95%: `0.544270`;
- replicações aprovadas: `1/10`;
- replicações com FPR controlado: `10/10`.

O limite superior agregado ficou abaixo de 0,60. Isso satisfaz o critério pré-registrado de falha forte.

## 3. Resultado por replicação

| Replicação | Limiar | Recall | Limite inferior 95% | Estratos | Lotes | FPR | Passou |
|---:|---:|---:|---:|---:|---:|---|---|
| 0 | 7.351147 | 0.529500 | 0.523800 | 4/8 | 2/20 | PASSOU | NÃO |
| 1 | 7.912483 | 0.443100 | 0.437550 | 2/8 | 0/20 | PASSOU | NÃO |
| 2 | 7.337465 | 0.533750 | 0.528200 | 4/8 | 3/20 | PASSOU | NÃO |
| 3 | 7.904032 | 0.451100 | 0.445400 | 3/8 | 0/20 | PASSOU | NÃO |
| 4 | 7.298742 | 0.535000 | 0.529200 | 4/8 | 3/20 | PASSOU | NÃO |
| 5 | 7.363563 | 0.526350 | 0.520650 | 4/8 | 0/20 | PASSOU | NÃO |
| 6 | 6.855367 | 0.606150 | 0.600650 | 6/8 | 20/20 | PASSOU | SIM |
| 7 | 7.061232 | 0.572550 | 0.566900 | 6/8 | 18/20 | PASSOU | NÃO |
| 8 | 7.221587 | 0.541250 | 0.535450 | 4/8 | 4/20 | PASSOU | NÃO |
| 9 | 8.196091 | 0.408350 | 0.402800 | 1/8 | 0/20 | PASSOU | NÃO |

## 4. Previsão

Foi previsto que 5–7 das 10 replicações passariam, com recall agregado entre 0,59 e 0,63 e veredito inconclusivo.

O observado foi:

- 1/10 passou;
- recall agregado 0,51471;
- falha forte.

A previsão foi refutada.

## 5. Falso alerta

Todas as dez replicações controlaram o FPR e nenhuma família ultrapassou o limite extremo de 1,5%. A falha não veio de falsos alertas excessivos no holdout; veio da perda de recall sob limiares calibrados independentemente.

## 6. Diagnóstico pós-hoc

A correlação descritiva entre limiar calibrado e recall foi `-0.998376`.

Esse diagnóstico não altera o veredito. Ele indica que a cauda dos negativos de desenvolvimento produz grande variação no limiar e, por consequência, no recall.

Faixa dos limiares: `6.855367` a `8.196091`.

Faixa do recall: `0.408350` a `0.606150`.

## 7. Conclusão permitida

> 12σ em t50 não é um requisito robusto sob o procedimento atual. Uma execução favorável não se reproduziu de forma consistente.

## 8. Consequência científica

Não devemos continuar refinando 11,8σ versus 12,2σ com uma única calibração. O próximo passo deve atacar a instabilidade do limiar ou elevar o SNR e repetir a robustez multi-seed.

Uma opção conservadora é testar 14σ em t50 com o mesmo protocolo de dez replicações.