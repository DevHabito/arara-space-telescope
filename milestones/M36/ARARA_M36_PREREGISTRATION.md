# ARARA From Zero — Pré-registro M36 Four-Shape Rolling Bank

**Versão:** M36.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** retirada prospectiva somente do rótulo discreto de forma.

## 1. Pergunta pequena

Mantendo duração e parâmetro contínuo de forma exatos, a busca rolling causal confirmada no M35 continua operacional quando o rótulo verdadeiro da forma é substituído por um banco das quatro famílias?

## 2. Oráculo retirado

O M35 fornecia ao detector a família verdadeira:

- linear;
- power-law;
- exponencial;
- logística.

No M36, o candidato não recebe esse rótulo. Em cada endpoint, avalia as quatro famílias e usa o maior score.

## 3. Oráculos que permanecem

Permanecem conhecidos:

- duração verdadeira;
- um parâmetro latente de inclinação \(u\in[0,1]\);
- amplitude/SNR do contrato;
- conjunto das quatro famílias possíveis;
- nuisance e referências observadas.

O parâmetro latente é mapeado prospectivamente:

\[
\gamma=1.5+1.5u
\]

para power-law,

\[
\beta=1+3u
\]

para exponencial e

\[
q=6+6u
\]

para logística.

A família verdadeira usa exatamente o mesmo \(u\) empregado para gerar o sinal. As famílias alternativas recebem o mesmo percentil \(u\). Assim, somente a identidade discreta da família é desconhecida.

## 4. Métodos pareados

### Controle

`rolling_exact_shape_latency4`

usa somente a família verdadeira, com a busca rolling de 99 endpoints e contrato \(t_{50}+4\).

### Candidato

`rolling_four_shape_bank_latency4`

avalia, em cada endpoint:

\[
Z_{\rm bank}(e)=
\max_{s\in\mathcal S}Z_s(e),
\]

onde:

\[
\mathcal S=
\{\mathrm{linear,power\_law,exponential,logistic}\}.
\]

O alerta é o primeiro endpoint em que \(Z_{\rm bank}(e)\) ultrapassa o limiar próprio do banco.

Se mais de uma forma cruza no mesmo endpoint, a forma reportada é a de maior score. Empates numéricos exatos seguem a ordem congelada acima.

## 5. Busca temporal

A matemática permanece idêntica ao M35:

- endpoints 81–179;
- 99 endpoints;
- seleção até \(e-9\);
- guarda em \(e-8\);
- confirmação em \(e-7,\ldots,e\);
- hinge causal estimado somente no bloco de seleção;
- primeiro cruzamento, nunca argmax temporal.

O mesmo hinge estimado em cada endpoint é usado pelas quatro formas, pois o estimador não recebe o template.

## 6. Contrato positivo

Uma detecção é sucesso se:

\[
\tau_{\rm true}
\leq e_{\rm alert}
\leq t_{50}+4.
\]

Gatilhos antes do onset, alertas posteriores e ausência de alerta são misses.

## 7. Look-elsewhere conjunto

Para negativos, o controle usa:

\[
Z_{\max,\mathrm{exact}}
=
\max_{99\ endpoints}Z_{\rm true\ shape}.
\]

O banco usa:

\[
Z_{\max,\mathrm{bank}}
=
\max_{99\ endpoints\times4\ formas}Z.
\]

O limiar do banco será calibrado diretamente sobre esse máximo de 396 hipóteses correlacionadas por curva.

Não será feita correção analítica aproximada.

## 8. Calibração independente

Serão gerados 50.000 negativos por cada família de ruído.

Cada negativo recebe prospectivamente:

- onset virtual;
- duração virtual;
- parâmetro latente \(u\);
- uma família virtual verdadeira uniforme entre as quatro;
- o banco completo das quatro famílias.

Root seed:

`2026090101`.

## 9. Dez holdouts

Cada holdout terá:

- 2.500 positivos por cada um dos oito estratos;
- 5.000 negativos por família;
- 20 lotes;
- os dois métodos nas mesmas curvas;
- 10.000 réplicas de bootstrap.

Root seeds:

- holdouts: `2026090102`;
- bootstrap agregado: `2026090103`;
- bootstrap pareado: `2026090104`.

## 10. Convenção de confiança

Os gates usam limites unilaterais de 95%:

- inferior: quantil 0,05;
- superior: quantil 0,95.

Quando apresentados juntos, correspondem ao intervalo central de 90%.

## 11. Validade do controle

O teste é interpretável somente se `rolling_exact_shape_latency4`:

1. passa em pelo menos 8/10 holdouts;
2. possui limite inferior agregado de recall \(\geq0.60\);
3. controla FPR em pelo menos 9/10 holdouts;
4. não apresenta violação extrema.

Falha produz:

`INVALID_M36_EXACT_SHAPE_CONTROL`.

## 12. Gate operacional do banco

Por holdout, o banco passa se:

1. cada família tem:
\[
FPR_{\rm upper}^{95\%,unilateral}\leq0.01;
\]

2. recall:
\[
R_{\rm lower}^{95\%,unilateral}\geq0.60;
\]

3. pelo menos 6/8 estratos têm limite inferior \(\geq0.50\);

4. pelo menos 15/20 lotes têm recall \(\geq0.55\).

Agregado, passa se:

1. pelo menos 8/10 holdouts passam;
2. limite inferior agregado \(\geq0.60\);
3. pelo menos 9/10 holdouts controlam FPR;
4. nenhuma violação extrema acima de 1,5%.

## 13. Gate separado de identificação da forma

Entre as detecções primárias corretas do banco, define-se:

\[
A_{\rm shape}
=
P(\widehat s=s_{\rm true}\mid
\tau\leq e_{\rm alert}\leq t_{50}+4).
\]

A identificação passa se:

1. limite inferior unilateral agregado de 95% \(\geq0.70\);
2. pelo menos 8/10 holdouts têm limite inferior unilateral \(\geq0.70\).

Esse gate não altera o gate de detecção. Ele separa “detectar sem conhecer a forma” de “classificar a forma com confiança”.

## 14. Comparação pareada

Será reportada:

\[
\Delta R=
R_{\rm bank}-R_{\rm exact}.
\]

Não existe gate adicional de não inferioridade. O contrato operacional absoluto é primário.

## 15. Veredito

### Detecção e identificação passam

`PASS_FOUR_SHAPE_BANK_AND_IDENTIFICATION`

se:

- controle válido;
- banco passa detecção;
- identificação passa.

### Detecção passa, identificação não

`PASS_DETECTION_SHAPE_UNRELIABLE`

se:

- controle válido;
- banco passa detecção;
- identificação não passa.

### Falha forte

`STRONG_FAIL_FOUR_SHAPE_BANK`

se o controle é válido e qualquer ocorre:

- no máximo 2/10 holdouts passam detecção;
- limite superior agregado do recall do banco \(\leq0.60\);
- violação extrema de FPR.

### Inconclusivo

`INCONCLUSIVE_FOUR_SHAPE_BANK`

nos demais casos.

## 16. Diagnósticos congelados

Sem alterar gates:

- limiares e famílias determinantes;
- recall por estrato;
- recall por forma verdadeira;
- matriz de confusão da forma selecionada;
- acurácia da forma entre todos os alertas;
- acurácia entre detecções primárias;
- endpoint e latência do primeiro cruzamento;
- detecções pareadas;
- AUROC/AP dos máximos;
- distribuição da forma escolhida em negativos;
- retenção de energia.

## 17. Previsão

Como o M35 ficou próximo da fronteira nos contextos concurrent, prevê-se aumento de limiar e perda moderada:

\[
R_{\rm exact}\in[0.73,0.79],
\]

\[
R_{\rm bank}\in[0.66,0.75],
\]

\[
\Delta R\in[-0.10,0.00].
\]

Prevê-se:

- limiar do banco entre 7,2 e 8,6;
- FPR robusto;
- 3–8 holdouts aprovados;
- acurácia de forma entre 0,45 e 0,75;
- veredito `INCONCLUSIVE_FOUR_SHAPE_BANK`.

A previsão cruza deliberadamente a fronteira operacional.

## 18. Limites

Mesmo um passe completo não retira:

- duração exata;
- parâmetro latente exato;
- amplitude/SNR fixa;
- validação em dados reais;
- definição física da cadência.

## 19. Regras contra puxadinho

1. Exatamente duas estratégias de detecção.
2. Exatamente quatro formas no banco.
3. Exatamente 99 endpoints.
4. Exatamente 396 hipóteses no máximo negativo do banco.
5. Primeiro cruzamento define o alerta.
6. Limiar próprio por método.
7. Exatamente 50.000 negativos por família.
8. Exatamente dez holdouts.
9. Nenhum holdout antes do congelamento.
10. Nenhuma forma, família, seed, estrato, endpoint ou lote será removido.
11. Nenhum gate será alterado após os dados.
12. O passe M35 e a falha M34 permanecem inalterados.
