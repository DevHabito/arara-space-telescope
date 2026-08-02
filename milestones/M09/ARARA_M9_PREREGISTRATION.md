# ARARA From Zero — Pré-registro M9 Final-SNR Threshold at t100

**Versão:** M9.0  
**Estado:** congelado antes da implementação e dos dados  
**Natureza:** curva dose–resposta de amplitude final, com alinhamento-oráculo em \(t_{100}\).

---

## 1. Pergunta pequena

Mantendo ruído, artefatos, preprocessing, falso alerta e janela \(t_{100}\) congelados, qual nível fixo de amplitude final torna o contrato detectável?

---

## 2. Variável alterada

A única variável científica alterada é:

\[
A/\sigma_0 \in \{4,6,8,10,12\},
\]

onde \(\sigma_0\) é o desvio-padrão estacionário do ruído individual do alvo usado pelo gerador.

Os mesmos campos-base, onsets, durações, formas e artefatos serão reutilizados de maneira emparelhada entre os cinco níveis. Apenas a amplitude do evento localizado muda.

---

## 3. Elementos mantidos

Permanecem idênticos ao M8:

- uma estrela-alvo e oito referências;
- 180 cadências;
- ruído AR(1), normal ou Student-t;
- common-mode;
- contaminação impulsiva de uma referência;
- quatro formas positivas;
- contextos clean e concurrent;
- cinco famílias negativas;
- preprocessing SBW;
- onset verdadeiro;
- template processado exato;
- score único em \(t_{100}\);
- FPR controlado separadamente por família.

Seeds novas:

- desenvolvimento: `2026080401`;
- holdout: `2026080402`;
- bootstrap: `2026080403`.

---

## 4. Estratos positivos

Para cada nível de SNR:

- linear clean;
- linear concurrent;
- power-law clean;
- power-law concurrent;
- exponential clean;
- exponential concurrent;
- logistic clean;
- logistic concurrent.

Total:

\[
5\times 8=40
\]

estratos dose–forma–contexto.

---

## 5. Emparelhamento

Dentro de cada forma e contexto, a mesma realização de:

- ruído;
- common-mode;
- acoplamentos;
- referência contaminada;
- onset;
- duração;
- parâmetro de forma;
- artefato concurrent;

será usada nos cinco níveis de SNR.

Isso permite interpretar diferenças entre níveis como efeito da amplitude, não como troca de população.

---

## 6. Desenvolvimento

- 1.000 campos-base por forma/contexto;
- cinco níveis por campo-base;
- 2.000 curvas por família negativa;
- limiar calculado somente nos negativos;
- máximo de 0,5% de alertas por família negativa.

Os positivos não participam do limiar.

---

## 7. Holdout

- 2.500 campos por cada combinação forma–contexto–SNR;
- 5.000 curvas por família negativa;
- 20 lotes;
- 125 campos por estrato positivo em cada lote;
- 250 negativos por família em cada lote.

Total positivo:

\[
5\times8\times2500=100\,000.
\]

Total negativo:

\[
5\times5000=25\,000.
\]

---

## 8. Métrica por nível

Para cada nível \(a\):

\[
R(a)=\frac{1}{8}\sum_{h=1}^{8}R_h(a).
\]

Intervalo global por bootstrap estratificado com 10.000 réplicas.

Recall por estrato usa limite inferior unilateral de Clopper–Pearson a 95%.

---

## 9. Previsão registrada antes dos resultados

Previsões globais:

\[
R(4)\in[0.15,0.30],
\]

\[
R(6)\in[0.35,0.55],
\]

\[
R(8)\in[0.55,0.75],
\]

\[
R(10)\in[0.70,0.88],
\]

\[
R(12)\in[0.82,0.95].
\]

Previsão principal:

> O primeiro nível que satisfará todos os critérios de promoção será \(8\sigma\).

Também se prevê:

1. recall global não decrescente com SNR;
2. logística terá maior recall;
3. exponencial terá menor recall;
4. diferenças clean–concurrent diminuirão em SNR alto;
5. `shared_ramp` ou `shared_bump` determinará o limiar.

---

## 10. Vitória de um nível

Um nível \(a\) passa somente se:

1. Em cada família negativa:
\[
FPR_{\mathrm{upper}}^{95\%}\leq0.01.
\]

2. Recall global:
\[
R_{\mathrm{lower}}^{95\%}(a)\geq0.60.
\]

3. Pelo menos seis dos oito estratos:
\[
R_{h,\mathrm{lower}}^{95\%}(a)\geq0.50.
\]

4. Pelo menos 15 dos 20 lotes:
\[
R_{\mathrm{batch}}(a)\geq0.55.
\]

---

## 11. Vitória do M9

M9 passa se:

- o FPR é controlado;
- pelo menos um nível passa;
- a curva global pontual não apresenta queda maior que 0,02 entre níveis adjacentes.

O nível mínimo recomendado será o menor nível aprovado.

A previsão “primeiro nível = \(8\sigma\)” é avaliada separadamente e pode falhar mesmo se M9 passar.

---

## 12. Falha forte

M9 falha fortemente se:

- qualquer família negativa viola o FPR; ou
- nenhum nível passa e:
\[
R_{\mathrm{upper}}^{95\%}(12)\leq0.50.
\]

---

## 13. Inconclusivo

Se nenhum nível passar, mas \(12\sigma\) tiver limite superior acima de 0,50, o resultado é inconclusivo.

---

## 14. Interpretação

- **PASS:** existe um limiar de SNR no intervalo testado para detectabilidade em amplitude completa.
- **STRONG_FAIL:** nem \(12\sigma\) fecha o contrato.
- **INCONCLUSIVE:** o limiar está acima da faixa testada ou o contrato requer outra mudança.

O M9 não valida alerta precoce. Ele mede detectabilidade em \(t_{100}\).

---

## 15. Regras contra puxadinho

1. Nenhum nível será adicionado após o desenvolvimento.
2. Nenhum nível será removido.
3. Nenhuma exclusão de forma, contexto, seed ou lote.
4. Nenhuma alteração após abrir o holdout.
5. O mesmo campo-base será usado nos cinco níveis.
6. O limiar será calibrado apenas nos negativos.
7. Bug pré-holdout será registrado.
8. Bug pós-holdout invalida a execução.
9. Resultados negativos serão preservados.
