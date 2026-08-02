# ARARA-M10 — Nota de implementação congelada

**Versão:** 10.0  
**Estado:** congelada antes da geração dos dados.

## Campo positivo

O M10 importa o gerador emparelhado do M9. Para cada campo:

\[
s_k=8\sigma_0 f_k.
\]

O campo observado e a contribuição processada do sinal são calculados uma única vez. As quatro frações alteram somente o fim do segmento alinhado.

## Campo negativo

Cada negativo recebe uma única hipótese virtual. O mesmo residual e o mesmo template processado são avaliados nos quatro pseudo-tempos de fração.

## Limiares

Cada fração recebe seu próprio limiar, calibrado nos mesmos negativos de desenvolvimento.

## Bootstrap

Para cada fração:

- oito estratos;
- pesos iguais;
- 10.000 réplicas;
- percentis 5% e 95%.

## Monotonicidade

A curva passa se nenhuma diferença adjacente for inferior a \(-0.02\).

## Holdout

A abertura será registrada antes da geração. Segunda execução será recusada.
