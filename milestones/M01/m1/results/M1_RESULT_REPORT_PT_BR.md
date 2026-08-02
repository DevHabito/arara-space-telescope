# ARARA From Zero — Relatório do teste M1

**Teste:** ARARA-M1  
**Estado:** concluído  
**Holdout:** aberto uma única vez  
**Veredito formal pré-registrado:** `INCONCLUSIVE`  
**Decisão de engenharia:** **NÃO PROMOVER**

---

## 1. Pergunta

Em séries fotométricas sintéticas não vistas, um detector causal de tendência positiva local detecta rises sustentados mais cedo que um CUSUM unilateral, mantendo o mesmo limite de falso alerta?

O teste avaliou somente séries fotométricas normalizadas. Ele não avaliou óptica, céu real, FLOCK, saúde instrumental, energia ou missão orbital.

## 2. Previsão registrada antes dos resultados

A previsão foi de ganho absoluto de recall precoce entre 0,08 e 0,18 sobre CUSUM. Para passar, o limite inferior unilateral de 95% do ganho deveria ser pelo menos 0,10 e o limite inferior do recall do M1 deveria ser pelo menos 0,30.

## 3. Limiar congelado no desenvolvimento

- ARARA-M1: `15.099813461`
- Flux-z: `12.455404282`
- CUSUM: `244.338211060`
- CUSUM kappa: `0.25`

Os limiares foram escolhidos somente no desenvolvimento, antes do holdout.

## 4. Resultado primário

- Recall precoce ARARA-M1: `0.000150` = `0.0150%`
- Recall precoce CUSUM: `0.000000` = `0.0000%`
- Diferença M1 − CUSUM: `0.000150` = `0.0150` ponto percentual
- Limite inferior de 95% do recall M1: `0.000050`
- Intervalo bootstrap unilateral central reportado para a diferença: `0.000050` a `0.000300`
- Lotes com diferença positiva: `3` de 20

Foram observadas apenas 3 detecções precoces do M1 em 20.000 eventos:

- linear: 1/5.000;
- power-law: 0/5.000;
- exponencial: 0/5.000;
- logística: 2/5.000.

A previsão de ganho de 0,08–0,18 não foi confirmada. O ganho observado foi 0,00015.

## 5. Controle de falsos alertas

O M1 satisfez o limite superior unilateral de 95% de FPR menor que 1% em cada família negativa:

| Família | Alertas | N | FPR | Limite superior 95% |
|---|---:|---:|---:|---:|
| quiet | 6 | 5000 | 0.0012 | 0.0024 |
| positive_impulse | 2 | 5000 | 0.0004 | 0.0013 |
| symmetric_bump | 9 | 5000 | 0.0018 | 0.0031 |
| sinusoid | 13 | 5000 | 0.0026 | 0.0041 |
| negative_dip_recovery | 6 | 5000 | 0.0012 | 0.0024 |

O controle de falsos alertas funcionou, mas ao custo de praticamente eliminar o recall precoce.

## 6. Critérios pré-registrados

| Critério | Resultado |
|---|---|
| FPR por família dentro do limite | PASSOU |
| Recall M1, limite inferior ≥ 0,30 | FALHOU |
| Ganho, limite inferior ≥ 0,10 | FALHOU |
| Pelo menos 3/4 famílias sem perda pontual | PASSOU |
| Pelo menos 15/20 lotes positivos | FALHOU |

O protocolo reserva “falha forte” para violação do FPR ou para evidência de diferença não positiva. Como a diferença foi minúscula, mas positiva, o rótulo formal foi “inconclusivo”. Isso não significa sucesso: a regra de engenharia do próprio pré-registro determina não promover resultados inconclusivos.

## 7. Diagnóstico pós-hoc

Esta seção não altera o veredito.

A família que determinou o limiar do M1 foi `negative_dip_recovery`. Durante a recuperação, um dip produz uma inclinação positiva local. O detector de inclinação não possui informação suficiente para saber, naquele momento, se observa:

- o começo de um rise sustentado;
- a metade ascendente de um bump;
- a recuperação de um dip;
- um trecho crescente de uma oscilação.

Essa é uma limitação de identificabilidade do observável univariado, não apenas uma escolha ruim de peso.

O CUSUM apresentou AUROC alto (`0.9618`), mas recall precoce zero. Ele cruzou o limiar em aproximadamente 17,0% dos eventos, todos tarde, com atraso mediano de 59 cadências depois de \(t_{25}\). Isso confirma por que AUROC não pode substituir a métrica de alerta precoce.

## 8. Erros encontrados antes do holdout

1. Tendência linear perfeita com variância residual numérica zero estava recebendo score zero; foi corrigida para score unilateral não limitado.
2. O limiar `float64` podia colidir com scores `float32`, permitindo 11 alertas quando o máximo era 10; foi corrigido no tipo numérico do próprio score.
3. O primeiro congelamento de limiares foi arquivado como inválido.
4. O holdout permaneceu fechado durante todas as correções.

Onze testes automatizados passaram antes da abertura do holdout.

## 9. Conclusão permitida

> Um t-estatístico causal de inclinação, aplicado sozinho a uma única curva fotométrica e sujeito a controle rigoroso de falsos alertas contra bumps, oscilações e recuperação de dips, não apresentou recall precoce operacionalmente útil no ambiente M1.

## 10. Conclusões não permitidas

Este teste não demonstra que:

- transientes reais são indetectáveis;
- o conceito geral ARARA falhou;
- um sistema multicanal não pode funcionar;
- o resultado se transfere diretamente para TESS, ZTF ou um telescópio orbital;
- CUSUM é um detector precoce adequado.

## 11. Decisão arquitetural

O próximo módulo não deve tentar salvar o M1 alterando pesos sobre o mesmo holdout. A próxima pergunta deve introduzir informação que torne o problema identificável, por exemplo:

- referência espacial/common-mode;
- housekeeping instrumental;
- coerência entre estrelas do mesmo campo;
- múltiplas bandas;
- confirmação independente.

O mesmo holdout não poderá ser usado para validar uma versão M2.
