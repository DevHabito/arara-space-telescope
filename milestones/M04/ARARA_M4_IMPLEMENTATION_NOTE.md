# ARARA-M4 — Nota de implementação congelada

**Versão:** 4.0  
**Estado:** congelada antes da geração de desenvolvimento e holdout.

## 1. Dependências congeladas

O M4 importa:

- gerador, métricas e estatística de inclinação de `../m2/arara_m2.py`;
- preprocessing SBW de `../m3/arara_m3.py`.

Os hashes SHA-256 desses arquivos serão incluídos no congelamento pré-holdout.

## 2. Construção dos templates

Para cada forma, parâmetro, duração e nível \(p\), resolve-se \(x_p\) analiticamente quando possível e por `brentq` para a logística.

O template bruto é avaliado em:

\[
x_i=\frac{i}{L-1}x_p.
\]

Depois:

1. subtrai-se sua média;
2. divide-se pela norma Euclidiana;
3. remove-se qualquer duplicata com o mesmo comprimento e valores iguais após arredondamento a 12 casas decimais.

Templates de norma menor que \(10^{-12}\) são proibidos.

## 3. Estatística

A fórmula de correlação é matematicamente equivalente ao t-estatístico da regressão simples com intercepto:

\[
T=c\sqrt{\frac{L-2}{1-c^2}}.
\]

Implementação:

- \(c\leq0\): score zero;
- \(0<c<1\): fórmula acima;
- \(c\geq1-10^{-15}\): score infinito;
- janela de variância menor que \(10^{-12}\): score zero.

O score usa somente janelas que terminam no instante corrente.

## 4. Template vencedor

Cada template recebe ID inteiro estável, definido pela ordem do pré-registro. Em duplicatas, permanece o primeiro ID.

Serão armazenados:

- score máximo por curva;
- primeiro cruzamento;
- ID do template no primeiro cruzamento;
- metadados completos do banco.

## 5. Limiares

Matched filter e SBW recebem limiares próprios.

Para 2.000 negativos e alvo de 0,5%:

- máximo permitido: 10 alertas por família;
- limiar familiar: próximo número representável acima do 11º maior máximo;
- limiar global: máximo dos cinco limiares familiares.

## 6. Intervalos

- FPR: Clopper–Pearson unilateral superior de 95%;
- recall por estrato: Clopper–Pearson unilateral inferior de 95%;
- recall global e diferença MF−SBW: bootstrap emparelhado e estratificado, 10.000 réplicas;
- limites bootstrap: percentis 5% e 95%.

## 7. Comparador SBW

O comparador é o detector de inclinação do M3 aplicado ao mesmo resíduo SBW. Não há reutilização do limiar M3; um novo limiar é calibrado nos negativos M4.

## 8. Holdout

O arquivo `HOLDOUT_OPENED.json` será criado imediatamente antes da geração. Uma segunda execução será recusada.
