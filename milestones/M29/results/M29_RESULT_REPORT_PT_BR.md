# ARARA From Zero — Relatório do M29 Reference-Nuisance Projected Partial-t

**Estado:** concluído  
**Calibração:** 50.000 negativos por família  
**Holdouts:** 10/10  
**Comparação:** pareada nas mesmas curvas  
**Veredito:** `STRONG_FAIL_NUISANCE_PROJECTION`  
**Decisão:** rejeitar a projeção conjunta de constante, rampa e modo comum de referência em uma janela de oito cadências

## 1. Pergunta

Remover nuisance observável antes da correlação poderia reduzir a cauda de `shared_step` sem destruir o sinal?

O candidato projetou residual e template contra:

- constante;
- rampa linear;
- modo comum processado das estrelas de referência.

Depois calculou um t parcial unilateral com quatro graus de liberdade quando o rank foi três.

## 2. Resultado agregado

| Método | Limiar | Família determinante | Recall | Limite inferior unilateral 95% | Limite superior unilateral 95% | Passes | FPR |
|---|---:|---|---:|---:|---:|---:|---:|
| `baseline8` | 16.520498 | `shared_step` | 0.291375 | 0.289535 | 0.293205 | 0/10 | 10/10 |
| `projected_t8` | 4.497558 | `shared_ramp` | 0.006675 | 0.006290 | 0.007070 | 0/10 | 10/10 |

O candidato não melhorou o baseline. Ele praticamente eliminou a detectabilidade.

## 3. Comparação pareada

\[
R_{\rm baseline}=0.291375,
\]

\[
R_{\rm projected}=0.006675.
\]

\[
\Delta R=-0.284700.
\]

Limites unilaterais de 95% da diferença:

\[
-0.286605
\leq\Delta R\leq
-0.282795.
\]

O limite superior inteiro da diferença permaneceu negativo. Portanto, a inferioridade do candidato foi formalmente demonstrada.

Em 10/10 holdouts, o candidato teve recall menor que o baseline.

## 4. Contagens pareadas dos 200.000 positivos

- detectados por nenhum: `140789`;
- somente pelo candidato: `936`;
- somente pelo baseline: `57876`;
- por ambos: `399`.

Assim:

- baseline detectou `58275` positivos;
- candidato detectou `1335` positivos.

## 5. Resultado por forma

| Estrato | Baseline | Projetado |
|---|---:|---:|
| `exponential__clean` | 0.230560 | 0.007680 |
| `exponential__concurrent` | 0.398840 | 0.008480 |
| `linear__clean` | 0.265080 | 0.000000 |
| `linear__concurrent` | 0.419200 | 0.000000 |
| `logistic__clean` | 0.123040 | 0.010600 |
| `logistic__concurrent` | 0.287080 | 0.011360 |
| `power_law__clean` | 0.223280 | 0.007480 |
| `power_law__concurrent` | 0.383920 | 0.007800 |

Nas duas famílias lineares, o recall projetado foi exatamente zero.

## 6. Diagnóstico de identificabilidade

O nuisance teve rank três em todas as curvas. Com oito amostras, restaram quatro graus de liberdade para o teste.

Mais importante: o template projetado foi numericamente degenerado em 100% dos positivos lineares.

- `exponential__clean`: rank `3`, fração degenerada do template `0.000000`.
- `exponential__concurrent`: rank `3`, fração degenerada do template `0.000000`.
- `linear__clean`: rank `3`, fração degenerada do template `1.000000`.
- `linear__concurrent`: rank `3`, fração degenerada do template `1.000000`.
- `logistic__clean`: rank `3`, fração degenerada do template `0.000000`.
- `logistic__concurrent`: rank `3`, fração degenerada do template `0.000000`.
- `power_law__clean`: rank `3`, fração degenerada do template `0.000000`.
- `power_law__concurrent`: rank `3`, fração degenerada do template `0.000000`.

Isso não é uma falha numérica acidental. Na região local de oito cadências, um sinal linear processado pertence ao mesmo subespaço que constante e rampa. Depois da projeção, não sobra componente identificável.

Para power-law, exponencial e logística o template não foi exatamente degenerado, mas oito pontos próximos de t50 são localmente bem aproximados por componentes afins. A projeção removeu grande parte da energia discriminante.

## 7. O que aconteceu com `shared_step`

A projeção cumpriu uma parte do objetivo:

- baseline determinado por `shared_step`, limiar 16,520498;
- candidato determinado por `shared_ramp`, limiar 4,497558.

Porém, remover a dominância do degrau não foi suficiente. O método removeu o sinal verdadeiro ainda mais agressivamente.

O AUROC caiu de:

\[
0.986383
\]

para:

\[
0.528823,
\]

valor próximo do acaso.

## 8. Falso alerta

Os dois métodos controlaram o FPR em 10/10 holdouts, sem violação extrema.

O candidato apresentou taxas próximas de 0,5% em todas as famílias, coerentes com um score que perdeu separação entre positivos e negativos.

## 9. Previsão

- baseline na faixa prevista: `CONFIRMADA`;
- candidato entre 45% e 60%: `REFUTADA`;
- ganho entre 15 e 30 pontos: `REFUTADA`;
- FPR robusto nos dois: `CONFIRMADA`;
- ganho material pareado: `REFUTADO`;
- veredito previsto de ganho parcial: `REFUTADO`.

Previsão integralmente confirmada: `False`.

A direção prevista estava errada. O resultado foi uma falha forte, não um ganho parcial.

## 10. Conclusão permitida

> Na janela de oito cadências, projetar simultaneamente constante, rampa e modo comum das referências destrói a identificabilidade do sinal. O recall caiu de 29,14% para 0,67%, a diferença pareada foi estritamente negativa e o ranking tornou-se próximo do acaso.

## 11. O que foi rejeitado

Foi rejeitada a estatística específica:

`partial-t8(constante + rampa + modo comum de referência)`.

Não foi refutada toda remoção de nuisance. O teste mostrou que incluir uma rampa genérica no subespaço é incompatível com sinais localmente afins numa janela tão curta.

## 12. Próximo teste correto

Não devemos trocar várias colunas até alguma combinação passar.

O próximo controle deve alterar uma única coisa: projetar apenas o modo comum das referências, sem constante e sem rampa, mantendo o matched filter não centrado do baseline.

Esse M30 separará duas hipóteses:

- o modo comum observado pode remover `shared_step` preservando o sinal target-local;
- ou qualquer projeção do modo comum nessa janela continua destruindo separação.

A estatística candidata deverá ser:

\[
Z_{q\perp}=
\frac{(P_{q\perp}r)^\top(P_{q\perp}h)}
{\lVert P_{q\perp}h\rVert_2},
\]

sem centralização, sem rampa e sem t parcial.