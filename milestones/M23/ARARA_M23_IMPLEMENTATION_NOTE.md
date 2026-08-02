# ARARA-M23 — Nota de implementação congelada

**Versão:** 23.0  
**Estado:** congelada antes da geração da calibração.

## 1. Dependências

O núcleo M22 e as dependências M15, M9, M5 e M2 foram extraídos do pacote reproduzível completo do M22.

Nenhum arquivo de dependência será modificado.

## 2. Endpoint

O campo legado `PositivePanel.t100` armazena:

\[
\operatorname{time\_at\_fraction}(s, f).
\]

Como M23 fixa \(f=0.50\), esse campo contém numericamente \(t_{50}\). A auditoria está registrada em `PRE_IMPLEMENTATION_ENDPOINT_AUDIT.md`.

## 3. Calibração

São usadas cinco streams independentes, uma por família negativa.

Cada stream gera 50 blocos consecutivos de 1.000 curvas, totalizando 50.000. O estado do RNG é contínuo entre blocos.

Os scores completos de cada família e erro serão persistidos em arquivos NPZ antes do cálculo dos limiares.

## 4. Congelamento

Depois da calibração:

- os três limiares;
- os hashes dos scores;
- os hashes do código;
- as seeds;

serão congelados antes de criar o marcador `HOLDOUTS_OPENED.json`.

## 5. Holdouts

Cada holdout usa uma seed própria e os mesmos limiares globais congelados.

Não há calibração por holdout. Assim, a variabilidade observada vem dos dados de holdout, condicionada à calibração grande escolhida.

## 6. Escopo

M23 estima tolerância tardia condicionada a uma calibração específica de 50.000 negativos por família. Não estima incerteza entre calibrações grandes independentes.
