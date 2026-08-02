# ARARA-M34 — Nota de implementação

O hinge e o downstream são importados da cadeia M25/M30–M33. A implementação nova calcula o hinge em uma grade de endpoints por somas cumulativas e avalia somente as nove amostras brutas necessárias para produzir as oito amostras whitened do template em cada endpoint. Essa forma é algebricamente equivalente a deslocar e processar a curva inteira, mas evita materializar 99 templates completos por curva.
