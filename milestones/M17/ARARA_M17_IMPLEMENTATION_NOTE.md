# ARARA-M17 — Nota de implementação congelada

**Versão:** 17.0  
**Estado:** congelada antes da primeira replicação.

O M17 reutiliza exatamente o protocolo multi-seed do M15, alterando somente:

- SNR final: \(12\sigma\rightarrow14\sigma\);
- root seeds;
- previsão.

Cada replicação continua usando:

- calibração própria com 2.000 negativos por família;
- holdout próprio;
- limiar próprio;
- 20 lotes;
- bootstrap próprio.

O bootstrap agregado e os critérios de robustez permanecem idênticos ao M15.
