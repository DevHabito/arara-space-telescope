# ARARA-M24 — Implementation audit log

Nenhum incidente registrado.

## Incidente pré-dados M24-I1

O primeiro teste unitário revelou indexação booleana incompatível ao aplicar o número de graus de liberdade, que tinha forma `(n,1)`, sobre a matriz `(n,candidatos)`.

Correção:

- o vetor `count - 2` passou a ser explicitamente difundido para a forma completa da matriz de correlações antes da indexação;
- nenhuma equação, seed, candidato, limiar ou critério mudou;
- nenhuma calibração ou holdout havia sido aberto.

Classificação: bug vetorial de implementação pré-dados, sem impacto científico.
