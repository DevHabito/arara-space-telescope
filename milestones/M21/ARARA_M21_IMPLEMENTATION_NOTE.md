# ARARA-M21 — Nota de implementação congelada

**Versão:** 21.0  
**Estado:** congelada antes da primeira replicação.

O M21 reutiliza o protocolo multi-seed do M15, mantendo:

- SNR final em \(13.75\sigma\);
- fração \(t_{50}\);
- todos os gates e tamanhos amostrais.

Mudam apenas as root seeds e o status científico: um PASS numérico será rotulado `PASS_CONFIRMATORY`, pois o nível foi fixado antes da abertura do M21 e não haverá nova seleção.

Nenhum critério, limiar, método de FPR ou bootstrap foi alterado.
