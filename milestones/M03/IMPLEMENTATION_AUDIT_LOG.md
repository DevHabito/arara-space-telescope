# ARARA-M3 — Implementation audit log

Nenhum incidente registrado antes dos testes iniciais.

## Incident 001 — Teste comparava variâncias em escalas diferentes

- Encontrado por: suíte inicial, antes do desenvolvimento.
- Erro: o teste comparava a variância do resíduo SBW renormalizado com a variância do fluxo bruto.
- Motivo da invalidade: o operador SBW redefine a escala pela MAD do resíduo; portanto, a comparação direta de variâncias não testa remoção de common-mode.
- Correção: usar o caso ideal sem ruído independente, em que séries proporcionais devem produzir resíduo numericamente nulo.
- Impacto no algoritmo: nenhum.
- Impacto nos dados: nenhum; desenvolvimento e holdout permaneciam inexistentes.
