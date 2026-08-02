# ARARA-M15 — Nota de implementação congelada

**Versão:** 15.0  
**Estado:** congelada antes da primeira replicação.

## 1. Plano de seeds

Uma `SeedSequence(2026081001)` gera dez sequências filhas, uma por replicação.

Cada sequência de replicação gera três filhas:

1. desenvolvimento;
2. holdout;
3. bootstrap da replicação.

O inteiro operacional de cada filha é o primeiro `uint32` de `generate_state(1)`. Entropia, `spawn_key` e inteiro serão registrados em `FROZEN_REPLICATION_SEEDS.json`.

## 2. Núcleo reutilizado

Cada replicação usa o núcleo M9 com:

- `snr_levels=(12.0,)`;
- `target_fraction=0.50`;
- tamanhos e critérios congelados no M15;
- limiar próprio.

## 3. Persistência

Para cada replicação serão salvos:

- métricas de desenvolvimento;
- limiar;
- resumo positivo e negativo;
- métricas por lote;
- métricas secundárias;
- veredito da replicação.

Os dados podem ser regenerados integralmente por código e seeds.

## 4. Bootstrap hierárquico

Em cada réplica bootstrap:

1. sorteiam-se dez índices de replicação com reposição;
2. para cada replicação sorteada e cada um dos oito estratos, sorteia-se:
   \[
   X^*\sim\operatorname{Binomial}(n,\widehat p);
   \]
3. calcula-se a média com pesos iguais entre as dez replicações sorteadas e os oito estratos.

Serão usadas 10.000 réplicas com seed `2026081002`.

## 5. Execução

O marcador `REPLICATIONS_OPENED.json` será criado antes da primeira replicação. A execução poderá ser dividida em blocos técnicos, sem trocar qualquer seed, código ou critério.
