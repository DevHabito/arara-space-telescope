# ARARA-M22 — Nota de implementação congelada

**Versão:** 22.0  
**Estado:** congelada antes da primeira replicação.

## Operação do template

Para cada curva, o SBW estima no baseline:

- escala do alvo;
- coeficiente de referência;
- escala residual;
- AR(1) residual.

O sinal bruto é deslocado por \(\delta\) e então submetido ao mesmo operador linear:

\[
x^{(s)}_k=s_k/\widehat\sigma_{\rm alvo},
\]

\[
h_0=x^{(s)}_0/\widehat\sigma_e,
\]

\[
h_k=
\frac{x^{(s)}_k-\widehat\phi x^{(s)}_{k-1}}
{\widehat\sigma_e}.
\]

Não se desloca simplesmente o template já processado, pois isso trataria incorretamente a fronteira do whitening.

## Emparelhamento

Dentro de cada curva:

- o campo observado é único;
- o residual é calculado uma vez;
- os cinco erros alteram apenas o template e o início do segmento;
- o endpoint permanece \(t_{50}\).

## Desenvolvimento

Somente negativos participam da calibração. Cada erro recebe um limiar próprio.

## Holdout

Os resultados são acumulados por:

- erro;
- estrato;
- família negativa;
- lote.

Os scores individuais são usados apenas para métricas secundárias e não decidem o veredito.

## Agregação

Cada erro recebe separadamente o mesmo protocolo hierárquico de dez replicações usado nos M15–M21.

O veredito global exige passe simultâneo em -2, 0 e +2 cadências.
