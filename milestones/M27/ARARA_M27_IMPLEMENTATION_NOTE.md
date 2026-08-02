# ARARA-M27 — Nota de implementação congelada

**Versão:** 27.0  
**Estado:** congelada antes da calibração.

## Alteração única

O M27 reutiliza integralmente o núcleo do M26 e altera somente `confirmation_length` de 8 para 16.

A função de partição herdada produz:

- seleção geométrica até `endpoint - 17`;
- uma guarda em `endpoint - 16`;
- confirmação em `endpoint - 15 ... endpoint`.

A região anterior é estrutural e não participa do score.

## Positivos e negativos

Positivos usam onset, forma, duração e endpoint exatos. Negativos recebem hipóteses virtuais exatas. Não há busca de onset.

## Inferência

Os quantis 0,05 e 0,95 são usados como limites unilaterais de 95%, em continuidade com os gates pré-registrados. Quando apresentados em conjunto, não serão chamados de intervalo bilateral de 95%.
