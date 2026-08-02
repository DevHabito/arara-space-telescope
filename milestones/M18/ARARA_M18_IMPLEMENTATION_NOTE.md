# ARARA-M18 — Nota de implementação congelada

**Versão:** 18.0  
**Estado:** congelada antes da primeira replicação.

O M18 reutiliza o protocolo multi-seed do M15, alterando somente:

- SNR final: \(13\sigma\);
- root seeds;
- previsão.

Cada replicação continua usando calibração, limiar e holdout próprios.

A função agregadora do M18 preserva apenas os campos científicos do núcleo M15 e calcula separadamente os checks da previsão M18. Isso evita herdar rótulos de previsão de protocolos anteriores.

Nenhuma regra de passe, falha forte, FPR, bootstrap ou tamanho amostral foi alterada.
