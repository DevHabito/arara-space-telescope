# ARARA From Zero — Relatório do M38A Latent-Grid Eligibility

**Estado:** concluído  
**Natureza:** teste estrutural sem outcomes  
**Positivos gerados:** 0  
**Negativos gerados:** 0  
**Holdouts abertos:** 0  
**Veredito:** `PASS_M38A_LATENT_GRID_ELIGIBLE_K5`  

## 1. Pergunta

Qual é a menor grade uniforme do parâmetro contínuo u que preserva pelo menos 99,5% do SNR de filtro casado sob as métricas estruturais congeladas?

A resposta foi:

\[
G_5=\{0,\;0{,}25,\;0{,}50,\;0{,}75,\;1\}.
\]

## 2. Seleção das grades

| K | Retenção mínima na curva completa | Gate completo | Auditoria local | Selecionada |
|---:|---:|---|---|---|
| 2 | 0.986205601 | FALHOU | `NOT_RUN_FULL_CURVE_FAIL` | NÃO |
| 3 | 0.996319759 | PASSOU | `FAIL_LOCAL_MESH` | NÃO |
| 5 | 0.998997047 | PASSOU | `PASS_LOCAL_REFINED` | SIM |
| 9 | 0.999737743 | PASSOU | `NOT_RUN_FIRST_ELIGIBLE_ALREADY_FOUND` | NÃO |
| 17 | 0.999932915 | PASSOU | `NOT_RUN_FIRST_ELIGIBLE_ALREADY_FOUND` | NÃO |
| 33 | 0.999983033 | PASSOU | `NOT_RUN_FIRST_ELIGIBLE_ALREADY_FOUND` | NÃO |
| 65 | 0.999995733 | PASSOU | `NOT_RUN_FIRST_ELIGIBLE_ALREADY_FOUND` | NÃO |
| 129 | 0.999998930 | PASSOU | `NOT_RUN_FIRST_ELIGIBLE_ALREADY_FOUND` | NÃO |

A grade K=2 falhou antes da geometria local.

A grade K=3 passou na curva completa, mas falhou na janela real de confirmação. Isso demonstra que uma métrica global da curva, sozinha, seria insuficiente.

K=5 foi a primeira grade que cumpriu todos os gates; grades maiores não foram auditadas localmente, conforme o pré-registro.

## 3. Gate A — curva completa

Para K=5, a retenção mínima contínua foi `0.998997047`.

Logo, a perda máxima de SNR na curva completa foi:

\[
1-\rho_{\rm full}=0.001002953
\approx0{,}1003\%.
\]

O pior caso foi a família power-law no primeiro intervalo da grade, em u=0,125 aproximado por u=0.

## 4. Gate B — geometria local

A auditoria enumerou:

- quatro formas;
- 37 durações;
- 149 endpoints relativos;
- 2.049 valores de u;
- 33 valores de phi;
- janela de oito cadências e amostra AR anterior.

Total estrutural:

\[
1,491,090,084
\text{ combinações}.
\]

- avaliações com SNR definido: `1,090,797,444`;
- avaliações degeneradas: `400,292,640`;
- avaliações trivialmente idênticas: `723,028,581`.

A contagem trivialmente idêntica é um subconjunto das avaliações válidas.

### Falha de K=3

Retenção local mínima: `0.992306497`.

Condição crítica:

- forma: `power_law`;
- duração: `30`;
- endpoint relativo: `3`;
- phi: `0.8`;
- u verdadeiro: `0.25`;
- u aproximante: `0.0`.

Como 0,992306497 é menor que 0,995, K=3 foi rejeitada.

### Passe de K=5

Retenção mínima da malha: `0.997768888`.

Retenção mínima depois do refinamento contínuo das 512 piores células: `0.997768888`.

A perda estrutural local máxima foi:

\[
1-\rho_{\rm local}=0.002231112
\approx0{,}2231\%.
\]

Isso permanece abaixo do limite pré-registrado de 0,5%.

O pior caso refinado ocorreu em uma power-law muito cedo na subida, com phi=0,8 e u=0,125 aproximado por u=0.

Todos os 512 refinamentos contínuos terminaram com sucesso.

## 5. Grade congelada

A grade que o M38B deverá importar literalmente é:

```text
[0.0, 0.25, 0.5, 0.75, 1.0]
```

Ela foi gravada com os hashes do pré-registro e da implementação em `FROZEN_LATENT_GRID.json`.

## 6. Consequência computacional

O banco operacional posterior terá:

\[
99\text{ endpoints}
\times4\text{ formas}
\times37\text{ durações}
\times5\text{ valores de }u
=73.260
\]

hipóteses por curva.

O M38B deverá calibrar o máximo conjunto das 73.260 hipóteses. Não será válido calibrar u, duração, forma ou endpoint separadamente.

## 7. O que o M38A demonstra

> A grade uniforme de cinco pontos aproxima os templates contínuos com retenção estrutural mínima de SNR superior a 99,5% na curva completa e na geometria local pré-projetada do detector.

## 8. O que não demonstra

O M38A não demonstra:

- que o detector continuará passando depois do novo look-elsewhere;
- que a projeção instrumental sobre referências preservará o mesmo limite;
- que o valor vencedor de u será identificável;
- que as quatro famílias descrevem eventos astronômicos reais;
- viabilidade instrumental ou de missão.

A projeção sobre referências depende das curvas observadas e foi deliberadamente deixada para o teste operacional.

## 9. Próximo passo correto

O M38B deverá comparar, nas mesmas curvas:

1. controle com u verdadeiro, quatro formas e 37 durações;
2. candidato com a grade congelada de cinco valores.

A calibração deverá voltar a usar o protocolo agrupado que resolveu a validade no M37R:

\[
4\text{ blocos independentes}\times50.000
=200.000
\]

negativos por família.

O controle continuará com poder de veto. A identificação de u deverá ser um gate separado da detecção.