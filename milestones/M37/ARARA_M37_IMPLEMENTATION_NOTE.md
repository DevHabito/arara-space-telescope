# ARARA-M37 — Nota de implementação

A implementação calcula o hinge apenas uma vez por curva e endpoint. Para cada forma, as 37 durações são processadas vetorialmente. O score projetado usa a identidade algébrica de projeção ortogonal: o numerador é calculado com o residual já projetado e a energia do template projetado é obtida por subtração da componente paralela à referência. Testes de equivalência numérica contra a implementação M34/M36 serão congelados antes da calibração.
