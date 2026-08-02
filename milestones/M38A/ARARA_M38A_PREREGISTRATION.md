# ARARA From Zero — Pré-registro M38A Latent-Grid Eligibility

**Versão:** M38A.0  
**Estado:** congelado antes de qualquer cálculo de elegibilidade  
**Natureza:** teste estrutural sem curvas positivas, negativas, calibração de FPR ou holdouts.

## 1. Pergunta

Qual é a menor grade uniforme e pré-definida do parâmetro latente:

\[
u\in[0,1]
\]

que aproxima suficientemente os templates contínuos para permitir um teste operacional posterior sem fornecer \(u_{\rm true}\) ao detector?

## 2. Escopo

O M38A não testa detecção.

Ele não pode produzir afirmações de recall, FPR, AUROC, latência ou viabilidade de missão.

Seu único produto científico é uma grade elegível ou a conclusão de que nenhuma das grades candidatas cumpre o contrato estrutural.

## 3. Parâmetro latente

As quatro famílias permanecem:

- linear;
- power-law;
- exponencial;
- logística.

O parâmetro latente é mapeado como nos testes anteriores:

\[
\gamma=1,5+1,5u,
\]

\[
\beta=1+3u,
\]

\[
q=6+6u.
\]

A forma linear independe de \(u\), mas permanece na auditoria.

## 4. Grades candidatas

Serão avaliadas, nesta ordem, somente as grades uniformes com:

\[
K\in\{2,3,5,9,17,33,65,129\}.
\]

Para cada \(K\):

\[
G_K=
\left\{
\frac{j}{K-1}:j=0,\ldots,K-1
\right\}.
\]

A menor grade que cumprir integralmente os dois gates será congelada.

Não será permitido inserir um valor adicional depois dos resultados.

## 5. Métrica de retenção de SNR

Para um template verdadeiro normalizado \(s(u)\) e um template aproximante \(s(g)\), define-se:

\[
\rho(u,g)=
\frac{\langle s(u),s(g)\rangle}
{\|s(u)\|\,\|s(g)\|}.
\]

No regime de ruído branco e amplitude fixa, \(\rho\) é a razão entre a média de SNR do filtro aproximado e a do filtro exato.

O banco só pode melhorar em relação ao ponto da grade mais próximo. Portanto, a auditoria local usará conservadoramente o ponto numericamente mais próximo em \(u\).

## 6. Contrato

A perda máxima admissível é fixada antes dos cálculos em:

\[
1-\rho\leq0,005.
\]

Logo, exige-se:

\[
\rho\geq0,995.
\]

Esse contrato é estrutural e não foi ajustado a um resultado de recall.

## 7. Gate A — curva completa contínua

Para cada forma, será calculada a correlação normalizada na fase contínua:

\[
x\in[0,1].
\]

A integral será aproximada por quadratura Gauss–Legendre de 512 pontos em precisão float64.

Para cada célula de Voronoi da grade em \(u\), a retenção mínima será obtida por minimização limitada contínua, com tolerância absoluta \(10^{-12}\).

Gate A:

\[
\min_{\rm forma,\,u}\rho_{\rm full}\geq0,995.
\]

A forma linear deve produzir exatamente 1 dentro da tolerância numérica.

## 8. Gate B — geometria local do detector

A grade que passa o Gate A será auditada na geometria de confirmação atual.

Serão incluídos:

- quatro formas;
- durações inteiras 24–60;
- todos os endpoints relativos possíveis:
\[
r=e-\widehat\tau\in[-39,109];
\]
- janela de oito cadências;
- amostra anterior necessária ao filtro AR(1);
- coeficiente:
\[
\phi\in[0,0,8];
\]
- transformação:
\[
w_j=f_j-\phi f_{j-1}.
\]

Escalas multiplicativas são omitidas porque cancelam na correlação.

A projeção sobre a referência não entra no M38A porque depende de curvas instrumentais. Ela será testada operacionalmente no M38B.

## 9. Malha exaustiva local

A auditoria local utilizará:

\[
u_i=\frac{i}{2048},
\quad i=0,\ldots,2048,
\]

e:

\[
\phi_j=0,025j,
\quad j=0,\ldots,32.
\]

Todos os valores de forma, duração e endpoint relativo serão enumerados.

Janelas cujo template verdadeiro tenha norma menor ou igual a \(10^{-12}\) serão marcadas como degeneradas e não entram no mínimo, pois não possuem SNR de template definido.

## 10. Margem numérica

A malha exaustiva deve satisfazer:

\[
\rho_{\rm mesh}\geq0,9955.
\]

A margem de \(5\times10^{-4}\) protege contra mínimos entre pontos da malha.

## 11. Refinamento contínuo

Para cada grade auditada, serão preservadas as 512 geometrias com menor retenção na malha.

Em cada geometria, será feita minimização contínua em \(u\) e \(\phi\), limitada à célula local da malha e à célula de Voronoi do ponto de grade correspondente.

Será usado `scipy.optimize.differential_evolution` com:

- seed 2026090401;
- tolerância \(10^{-10}\);
- `polish=True`;
- precisão float64.

Gate B:

\[
\rho_{\rm refined}\geq0,995.
\]

## 12. Procedimento de seleção

Para cada \(K\), em ordem crescente:

1. executar Gate A;
2. se Gate A falhar, não executar Gate B;
3. se Gate A passar, executar a malha local;
4. se a margem de malha falhar, avançar para o próximo \(K\);
5. se a margem passar, executar o refinamento contínuo;
6. congelar o primeiro \(K\) que satisfizer todos os gates.

## 13. Veredito

### Passe

`PASS_M38A_LATENT_GRID_ELIGIBLE_K<K>`

se uma grade cumprir todos os gates.

### Falha

`FAIL_M38A_LATENT_GRID_ELIGIBILITY`

se nenhuma grade até \(K=129\) cumprir o contrato.

## 14. Artefato congelado

Em caso de passe será criado:

`FROZEN_LATENT_GRID.json`

contendo:

- \(K\);
- todos os valores de \(u\);
- contrato de retenção;
- mínimos dos Gates A e B;
- hashes do código e pré-registro.

O M38B deverá importar esse arquivo sem modificação.

## 15. Interpretação permitida

Um passe significa somente:

> A grade congelada aproxima os templates contínuos com retenção estrutural mínima de SNR de 99,5% sob as métricas pré-registradas.

Não significa que a detecção continue passando depois do look-elsewhere adicional.

## 16. Regras contra puxadinho

1. Nenhuma curva positiva ou negativa será gerada.
2. Nenhum resultado M37R será usado para escolher \(K\).
3. Somente as oito grades pré-definidas serão testadas.
4. O contrato de 99,5% não será alterado.
5. Nenhuma forma, duração ou geometria será removida.
6. Janelas degeneradas serão contadas e reportadas.
7. O primeiro \(K\) elegível será congelado.
8. Nenhum valor de \(u\) será acrescentado depois.
9. O M38B deverá usar a grade literalmente.
10. Resultados numéricos não serão chamados de prova analítica.
