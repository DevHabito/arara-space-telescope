# ARARA-M33 — Nota de implementação

O M33 importa o estimador e o downstream do M32. A única operação nova é uma permutação aleatória sem pontos fixos, aplicada dentro de cada grupo e lote com RNG dedicado. Os mesmos onsets hinge são usados antes e depois da permutação.
