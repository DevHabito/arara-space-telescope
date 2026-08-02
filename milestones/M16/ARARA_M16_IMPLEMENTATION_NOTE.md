# ARARA-M16 — Nota de implementação congelada

**Versão:** 16.0  
**Estado:** congelada antes da geração do primeiro superpool.

## 1. Plano de seeds

Três árvores independentes são usadas:

- `SeedSequence(2026081101)`: geração dos três mundos;
- `SeedSequence(2026081102)`: reamostragem das calibrações;
- `SeedSequence(2026081103)`: bootstrap de recall.

Cada mundo recebe:

- cinco streams de calibração, uma por família negativa;
- um stream raiz de holdout;
- três streams de reamostragem, um por tamanho;
- três streams de bootstrap, um por tamanho.

Entropia, `spawn_key` e inteiro operacional serão congelados em `FROZEN_WORLD_SEEDS.json`.

## 2. Superpool

Cada família negativa será gerada em blocos congelados de 1.000 curvas até completar 50.000 scores.

Somente os scores alinhados em \(t_{50}\) serão persistidos. Nenhum score será descartado.

## 3. Holdout

O holdout de cada mundo será gerado uma única vez com o núcleo M9:

- SNR final 12σ;
- fração 0,50;
- 20 lotes;
- limiar infinito durante a geração, para armazenar scores sem pré-classificação.

Os mesmos scores de holdout serão usados para todos os tamanhos e reamostragens daquele mundo.

## 4. Reamostragem

Para cada mundo, tamanho e repetição:

- amostragem com reposição separada por família;
- dtype dos scores: `float32`;
- ordem estatística obtida por `numpy.partition`;
- limiar idêntico ao contrato `conservative_threshold` do M2.

## 5. Intervalos

- FPR por família: Clopper–Pearson unilateral superior de 95%;
- recall por estrato: Clopper–Pearson unilateral inferior de 95%;
- recall global por calibração: bootstrap binomial estratificado com 10.000 réplicas;
- proporção agregada de calibrações aprovadas: Clopper–Pearson unilateral de 95%.

## 6. Execução

O arquivo `EXPERIMENT_OPENED.json` será criado antes do primeiro superpool.

A execução poderá ser dividida em chamadas técnicas. Código, seeds, tamanhos e critérios não poderão mudar.
