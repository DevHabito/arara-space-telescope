# ARARA — reconstrução matemática independente v0.1

## Status

Esta execução **não reproduz o código apagado**. Ela reconstrói um pipeline auditável a partir das equações e descrições sobreviventes e recusa herdar números cuja implementação não pode ser verificada.

## O que foi refeito e testado

- Modelo fotônico AB para fluxo espectral plano em `Fν`, com solução fechada e integração numérica independente.
- SNR de fotometria de abertura com fonte, céu, dark current e read noise separados.
- Energia encircled de PSF gaussiana deslocada usando distribuição qui-quadrado não central.
- PPV, votação binomial e votação beta-binomial.
- Volume bruto de dados.
- Identidade dimensional do balanço de energia por órbita.
- Gerador sintético novo, com sinal astrofísico e estado instrumental separados.
- Flux-z, CUSUM e uma reconstrução explícita do conceito DP1, chamada `DP1-R_external`.
- Limiar calibrado exclusivamente no treino.
- AUROC e average precision por implementações validadas de biblioteca.
- Lead time medido pelo primeiro cruzamento de limiar.
- Gate de saúde instrumental sem condicionar housekeeping diretamente ao rótulo.
- Seis seeds independentes, com 100 amostras por classe no treino e 200 por classe no teste, por seed.
- Nove testes automatizados; todos aprovados.

## Resultado sintético principal

O resultado não favoreceu o ARARA-DP1 reconstruído. No conjunto sintético novo:

- `CUSUM` teve AUROC mediano de aproximadamente **0,856**.
- `Flux-z` teve AUROC mediano de aproximadamente **0,788**.
- `DP1-R_external` teve AUROC mediano de aproximadamente **0,609**.

No alvo de FPR de treino de 5%, o recall precoce mediano foi aproximadamente:

- `CUSUM`: **0,070**;
- `Flux-z`: **0,0225**;
- `DP1-R_external`: **0,0075**.

O CUSUM detectou muitos eventos apenas tardiamente. O DP1-R não demonstrou vantagem neste teste. Isso não prova que todo detector ARARA seja impossível; demonstra que **esta reconstrução explícita da ideia DP1 não supera os baselines no ambiente sintético definido**.

## Gate instrumental

Como o estado instrumental foi gerado independentemente da classe astrofísica, o gate não recebeu informação escondida sobre o rótulo. Ele reduziu parte dos falsos alertas em alguns pontos de operação, mas também reduziu recall. Não apareceu nenhum “milagre” de PPV. Isso é o comportamento esperado de um veto real: ele troca falsos positivos por falsos negativos e precisa ser calibrado.

## FLOCK

Os números antigos de FLOCK não foram reproduzidos porque usavam FPR por janela como se fosse probabilidade de falso candidato coincidente entre nós. A reconstrução não faz essa substituição. Foi produzida uma grade de sensibilidade com:

- probabilidade candidata verdadeira explícita;
- probabilidade candidata falsa explícita;
- correlação de verdadeiros separada da correlação de falsos;
- prevalências de `10^-2`, `10^-3` e `10^-4`.

Sem um modelo de coincidência espacial e temporal, **não existe um único FPR FLOCK identificável**.

## Óptica e jitter

A equação de fótons publicada é correta sob duas hipóteses restritas: `Fν` constante na banda e throughput constante. A solução fechada coincidiu com a integração numérica com erro relativo da ordem de `10^-16`.

A energia encircled diminuiu monotonicamente com o deslocamento da PSF, como deve ocorrer. Isso corrige a tabela antiga em que o deslocamento aumentava a energia capturada.

## Potência

O cálculo dimensional por órbita foi refeito e testado. Porém, não foi emitido novo veredito 6U/12U. As distribuições de potência, área solar, heater, transmissão, eficiência, bateria e duty cycle foram apagadas ou não ficaram documentadas em nível suficiente. Recriar números concretos agora seria inventar entradas.

## Fronteira atual

Esta etapa testa consistência matemática e sintética. Ela não é validação em céu real nem fechamento de missão. A próxima etapa necessária é um benchmark com curvas reais e injeções controladas. Até isso existir, a conclusão rigorosa é:

> O conceito de decisão embarcada e sanidade instrumental continua testável. O detector DP1 reconstruído não demonstrou superioridade. FLOCK e viabilidade 6U/12U permanecem não identificáveis sem dados e parâmetros adicionais.
