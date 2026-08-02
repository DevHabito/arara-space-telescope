# ARARA From Zero — Pré-registro M28 Paired Confirmation-Length Map

**Versão:** M28.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** mapeamento prospectivo e pareado do comprimento da confirmação.

## 1. Pergunta pequena

Sob onset, endpoint, forma e duração exatos, qual dos comprimentos de confirmação congelados:

\[
L\in\{8,16,24,\mathrm{full}\}
\]

produz maior recall operacional, com limiar próprio e controle idêntico de falso alerta? Algum deles satisfaz o contrato?

## 2. Condição fixa

\[
A/\sigma_0=13.75,
\qquad
f=0.50.
\]

Continuam como oráculos:

- onset verdadeiro;
- endpoint verdadeiro \(t_{50}\);
- forma e duração exatas.

## 3. Estatística comum

Para todo comprimento, será usada a mesma estatística:

\[
Z_L=
\frac{\sum_{k\in W_L}r_kh_k}
{\sqrt{\sum_{k\in W_L}h_k^2}}.
\]

Não há intercepto, ajuste, busca ou maximização.

Para \(L\in\{8,16,24\}\):

\[
W_L=[e-L+1,e].
\]

Se parte da janela preceder o onset, o template é zero nessa região e não contribui ao numerador nem ao denominador.

Para `full`:

\[
W_{\mathrm{full}}=[\tau,e].
\]

## 4. Pareamento

Cada curva positiva ou negativa será gerada uma única vez.

Do mesmo residual e do mesmo template processado serão calculados os quatro scores. Portanto, diferenças entre comprimentos não serão confundidas com diferenças de campo, seed, ruído, onset, forma ou artefato.

## 5. Calibração

Antes dos holdouts serão gerados:

\[
50\,000
\]

negativos por cada uma das cinco famílias.

Cada curva produzirá quatro scores pareados.

Cada comprimento terá limiar próprio:

\[
\theta_8,\theta_{16},\theta_{24},\theta_{\mathrm{full}},
\]

calibrado para FPR empírico máximo de 0,5% por família.

Todos os limiares serão congelados antes dos holdouts.

Root seed:

`2026082301`.

## 6. Dez holdouts independentes

Cada holdout terá:

- 2.500 positivos por cada um dos oito estratos;
- 5.000 negativos por família;
- 20 lotes;
- os quatro comprimentos avaliados nas mesmas curvas;
- bootstrap com 10.000 réplicas por comprimento.

Root seeds:

- holdouts: `2026082302`;
- bootstraps agregados: `2026082303`.

## 7. Convenção dos limites de confiança

O gate usa limites **unilaterais de 95%**:

- limite inferior: quantil 0,05 do bootstrap;
- limite superior: quantil 0,95 do bootstrap.

Quando ambos forem mostrados juntos, serão chamados de “limites unilaterais de 95%”, equivalentes numericamente ao intervalo central de 90%, e não de intervalo bilateral de 95%.

Os limites Clopper–Pearson também são unilaterais de 95%.

## 8. Passe por holdout e comprimento

Um comprimento passa num holdout somente se:

1. cada família negativa:
\[
FPR_{\mathrm{upper,unilateral}}^{95\%}\leq0.01;
\]

2. recall global:
\[
R_{\mathrm{lower,unilateral}}^{95\%}\geq0.60;
\]

3. pelo menos 6/8 estratos têm limite inferior unilateral de 95%:
\[
R_h\geq0.50;
\]

4. pelo menos 15/20 lotes:
\[
R_{\mathrm{batch}}\geq0.55.
\]

## 9. Passe agregado por comprimento

Um comprimento passa se:

1. pelo menos 8/10 holdouts passam;
2. limite inferior agregado unilateral de 95% \(\geq0.60\);
3. pelo menos 9/10 holdouts controlam FPR;
4. nenhuma família ultrapassa limite superior de FPR de 1,5%.

## 10. Veredito global

### Candidato

`PASS_LENGTH_CANDIDATE`

se pelo menos um comprimento passa. O menor comprimento aprovado será o candidato de menor latência, mas exigirá confirmação independente no M29 antes de promoção.

### Falha forte global

`STRONG_FAIL_ALL_LENGTHS`

se todos os quatro comprimentos falham fortemente.

### Inconclusivo

Qualquer resultado intermediário será:

`INCONCLUSIVE_LENGTH_MAP`.

## 11. Falha forte por comprimento

Um comprimento falha fortemente se:

- no máximo 2/10 holdouts passam; ou
- limite superior agregado unilateral de 95% \(\leq0.60\); ou
- alguma família ultrapassa limite superior de FPR de 1,5%.

## 12. Comparações pareadas secundárias

Serão reportadas, sem alterar os gates:

- diferenças de recall por holdout;
- proporção de curvas positivas detectadas por um comprimento e não por outro;
- correlação dos scores entre comprimentos;
- crescimento do limiar;
- família determinante de cada limiar.

Não haverá teste retroativo de novos comprimentos.

## 13. Previsão anterior aos dados

Com base nos M26–M27, prevê-se:

1. nenhum comprimento passará;
2. os quatro comprimentos falharão fortemente;
3. o limiar crescerá com o comprimento efetivo;
4. o recall será maior em \(L=8\) e cairá em 16, 24 e `full`;
5. `shared_step` determinará os limiares de 16, 24 e `full`;
6. veredito:

`STRONG_FAIL_ALL_LENGTHS`.

Faixas previstas de recall agregado:

\[
R_8\in[0.24,0.34],
\]

\[
R_{16}\in[0.12,0.22],
\]

\[
R_{24}\in[0.07,0.18],
\]

\[
R_{\mathrm{full}}\in[0.05,0.25].
\]

## 14. Limite da interpretação

M28 testa uma família específica de matched filters não centrados. Não testa a estatística t correlacional do M23 e não permite concluir que todo uso de janelas longas seja inviável.

## 15. Regras contra puxadinho

1. Exatamente quatro comprimentos.
2. Exatamente 50.000 negativos por família.
3. Exatamente dez holdouts.
4. Mesmas curvas para os quatro comprimentos.
5. Limiar próprio por comprimento.
6. Nenhum holdout antes do congelamento.
7. Nenhuma seed, família, estrato, lote ou comprimento será excluído.
8. Nenhum comprimento novo será introduzido após os dados.
9. Nenhuma seleção do “melhor” será tratada como confirmação final.
10. Código, seeds, limiares e dependências serão congelados por hash.
