# ARARA-M20 — Nota de implementação congelada

**Versão:** 20.0  
**Estado:** congelada antes da primeira replicação.

O M20 reutiliza o protocolo multi-seed do M15, alterando somente:

- SNR final: \(13.75\sigma\);
- root seeds;
- previsão;
- interpretação adaptativa de um eventual PASS.

O núcleo numérico continua usando os mesmos gates. Se o resultado numérico for `PASS`, a saída científica do M20 será `PASS_REFINEMENT_CANDIDATE`, pois o nível foi escolhido adaptativamente após M19 e M17.

Nenhum critério, tamanho amostral, método de limiar, FPR ou bootstrap foi alterado.
