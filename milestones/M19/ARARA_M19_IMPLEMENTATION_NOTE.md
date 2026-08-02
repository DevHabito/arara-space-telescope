# ARARA-M19 — Nota de implementação congelada

**Versão:** 19.0  
**Estado:** congelada antes da primeira replicação.

O M19 reutiliza o protocolo multi-seed do M15, alterando somente:

- SNR final: \(13.5\sigma\);
- root seeds;
- previsão.

Cada replicação usa calibração, limiar e holdout próprios.

A função agregadora preserva apenas os campos científicos do núcleo M15 e calcula separadamente os checks da previsão M19. Nenhuma regra de passe, falha forte, FPR, bootstrap ou tamanho amostral foi alterada.
