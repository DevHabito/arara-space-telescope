# ARARA-M26 — Nota de implementação congelada

**Versão:** 26.0  
**Estado:** congelada antes da calibração.

## Controle único

O M26 reutiliza exatamente:

- a função de partição temporal do M25;
- a guarda de uma cadência;
- o matched filter de oito pontos;
- o operador SBW;
- os tamanhos amostrais e gates.

A única alteração causal é:

- M25: template deslocado para o onset estimado;
- M26: template permanece no onset exato/virtual fornecido.

## Positivos

O residual SBW e o template processado são calculados com o sinal exato. O score usa apenas a janela confirmatória congelada.

## Negativos

Cada negativo recebe uma hipótese virtual exata. Não há busca sobre onset, portanto a distribuição nula mede somente o matched filter curto e os artefatos do modelo.

## Escopo

M26 não remove nenhuma informação-oráculo. É um controle destinado a decompor a falha do M25.
