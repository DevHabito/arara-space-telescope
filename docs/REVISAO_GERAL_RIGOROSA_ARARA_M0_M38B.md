# Revisão geral rigorosa do programa ARARA — reconstrução v0.1 até M38B

**Data da revisão:** 1 de agosto de 2026  
**Escopo:** reconstrução independente inicial, marcos M1–M38A e estado do M38B  
**Natureza da revisão:** auditoria documental e metodológica dos relatórios, pré-registros, tabelas agregadas, logs de incidentes e pacotes reproduzíveis existentes. Não foi refeita integralmente a simulação de milhões de curvas.

---

# 1. Veredito executivo

O programa ARARA produziu um **pipeline de pesquisa computacional sério e progressivamente mais rigoroso**, com pré-registros, seeds congeladas, controles de falso alerta, holdouts, preservação de falhas e replicações independentes por dados.

A conclusão científica correta, porém, é estreita:

> **Dentro do simulador sintético congelado e em SNR final 13,75, existe um detector causal promissor baseado em projeção do modo comum das referências. Ele foi demonstrado sem onset exato, sem endpoint exato, sem rótulo de forma e sem duração exata. A retirada operacional do parâmetro contínuo `u` ainda não foi concluída.**

Isso **não** equivale a validação astronômica nem a viabilidade de missão.

O estado atual é:

| Camada | Estado rigoroso |
|---|---|
| Consistência matemática da reconstrução inicial | Parcialmente validada |
| Detector sintético com oráculos completos | Confirmado |
| Onset exato necessário para detectar | Não, no simulador |
| Onset físico identificado corretamente | Não |
| Endpoint `t50` exato necessário | Não, aceitando até 4 cadências de latência |
| Forma verdadeira necessária para detectar | Não |
| Forma vencedora identificável | Não |
| Duração verdadeira necessária para detectar | Não, após M37R |
| Duração vencedora identificável | Não |
| Parâmetro contínuo `u` | Grade K=5 estruturalmente elegível |
| Banco operacional com grade de `u` | Não concluído |
| Validação em dados reais | Ausente |
| Taxa operacional por campo/hora | Ausente |
| PPV em prevalência astronômica real | Ausente |
| Fechamento óptico, energético e de missão | Ausente |

---

# 2. O que foi feito de melhor

## 2.1. A reconstrução recusou números não auditáveis

A reconstrução v0.1 deixou explícito que o código apagado não podia ser reproduzido. Em vez de simular uma falsa continuidade, refez um modelo limpo e registrou que:

- o `DP1-R_external` reconstruído não superou CUSUM ou Flux-z;
- o FLOCK antigo não possuía um FPR único identificável;
- o veredito 6U/12U não poderia ser reemitido sem distribuições de entrada;
- a energia encircled com jitter havia sido interpretada incorretamente no trabalho antigo;
- o balanço de energia foi mantido apenas como identidade dimensional.

Essa recusa em “herdar” resultados apagados é uma das partes metodologicamente mais fortes do projeto.

## 2.2. As falhas foram preservadas

A sequência M1–M29 contém muitas falhas fortes e resultados inconclusivos. Elas não foram apagadas nem rebatizadas como sucesso.

Exemplos:

- M3: subtract-before-whiten não resgatou o detector;
- M4: banco causal de 144 templates falhou;
- M5–M8: informação muito precoce permaneceu insuficiente;
- M15: 12σ em `t50` falhou em 9/10 replicações;
- M24–M28: vários estimadores e comprimentos de confirmação falharam;
- M29: projetar constante, rampa e modo comum destruiu o sinal;
- M34: endpoint rolling com latência zero falhou;
- M37: execução completa foi declarada inválida porque o controle falhou.

Isso reduz viés de publicação interno e dá credibilidade aos passes posteriores.

## 2.3. O projeto separou descoberta de confirmação em pontos importantes

Dois exemplos são particularmente bons:

- M20 escolheu 13,75σ adaptativamente; M21 repetiu o mesmo nível com novas seeds e confirmou.
- M30 descobriu a projeção exclusiva do modo comum; M31 repetiu a mesma matemática com nova calibração e novos holdouts.

A independência é de **dados sintéticos, seeds e calibração**, não de implementação ou equipe. Mesmo assim, é muito melhor que tratar a descoberta como confirmação.

## 2.4. O look-elsewhere foi incorporado progressivamente

Nos estágios rolling e de bancos, o limiar foi calibrado sobre o máximo por curva incluindo:

- endpoints;
- formas;
- durações;
- futuramente, valores de `u`.

Isso é correto. Não houve uso de um limiar de hipótese única para um banco com milhares de buscas.

## 2.5. O M37 foi invalidado corretamente

O M37 tinha números descritivos promissores, mas o controle passou somente 1/10 holdouts. O protocolo deu ao controle poder de veto e o resultado foi mantido como:

`INVALID_M37_EXACT_DURATION_CONTROL`.

A auditoria mostrou equivalência numérica com o M36 nas mesmas curvas. Em seguida, o M37R aumentou prospectivamente a calibração para quatro blocos independentes e obteve controle válido.

Essa é uma decisão metodológica boa.

---

# 3. Linha do tempo científica

## Fase A — reconstrução e detectores precoces

### Reconstrução v0.1

- CUSUM: AUROC mediano ≈ 0,856.
- Flux-z: AUROC mediano ≈ 0,788.
- DP1-R: AUROC mediano ≈ 0,609.
- Nenhuma superioridade do detector ARARA reconstruído.
- FLOCK e viabilidade 6U/12U ficaram não identificáveis.

### M1–M4

- M1 slope causal: recall precoce de 0,015%.
- M2 common-mode após whitening: recall de 0,005%.
- M3 subtract-before-whiten: sem ganho.
- M4 banco model-aware: recall de 0,07%.

Conclusão: o contrato precoce original não era detectável por essas estatísticas.

### M5–M8 — limite-oráculo por fração

Com onset e template exatos:

- `t25`: recall 0,335%.
- `t50`: 3,56%.
- `t75`: 12,93%.
- `t100`: 35,91%.

Conclusão: o problema não era apenas a busca; havia pouca informação no começo do evento sob o ruído sintético escolhido.

## Fase B — dose-resposta de SNR com oráculos

### M9–M12

- Em `t100`, 8σ foi o primeiro nível aprovado.
- Em 8σ, somente `t100` passou.
- Em `t75`, 9σ foi o primeiro nível aprovado.
- Em 9σ, `t50` continuou insuficiente.

### M13–M21

- M13 encontrou 12σ como primeiro passe numa grade grossa.
- M14 mostrou que 12σ não se reproduzia.
- M15: 12σ passou somente 1/10.
- M16: ampliar a calibração não resgatou 12σ.
- M17: 14σ passou 10/10.
- M18: 13σ foi inconclusivo.
- M19: 13,5σ foi inconclusivo, 7/10.
- M20: 13,75σ passou 8/10 como candidato adaptativo.
- M21: 13,75σ foi confirmado em 10/10.

Conclusão válida naquela arquitetura: 13,75σ era o menor nível robustamente confirmado entre os níveis testados em `t50`, com onset e template exatos.

**Cuidado:** depois do M30 a estatística mudou radicalmente. Portanto, 13,75σ não deve ser tratado como requisito mínimo do detector atual.

## Fase C — onset e estatística de confirmação

### M22–M28

- M22 mostrou forte assimetria a erros de onset: atraso de +2 já era ruim e +4 falhava.
- M23, com calibração grande, confirmou tolerância somente até +1.
- M24: hinge retrospectivo causal colapsou para ≈2% de recall.
- M25: split-sample elevou recall para ≈27%, mas continuou falhando.
- M26: até com onset exato, confirmação de 8 pontos ficou em ≈28%.
- M27: 16 pontos não resgataram.
- M28, pareado: 8, 16, 24 e janela completa falharam; comprimentos maiores pioraram.

Conclusão: o downstream matched-filter não centrado era o gargalo, não apenas o estimador de onset.

### M29–M31 — descoberta principal

- M29 projetou constante + rampa + modo comum e praticamente apagou o sinal.
- M30 projetou somente o modo comum das referências:
  - baseline: recall 30,98%;
  - candidato: 79,82%;
  - diferença ≈48,84 pontos;
  - 10/10 holdouts.
- M31 confirmou:
  - recall 79,65%;
  - 10/10;
  - FPR robusto.

Este é o resultado mais importante do programa.

> A projeção exclusiva do modo comum observado nas referências é a peça central do detector sintético atual.

## Fase D — retirada dos oráculos

### M32–M33 — onset

- M32 com hinge causal:
  - recall 76,55%;
  - 10/10;
  - onset correto em envelope `[-2,+1]` em apenas 25,23%.
- M33 comparou hinge próprio com hinge permutado:
  - próprio: 77,49%;
  - permutado: 69,88%;
  - ganho pareado: 7,61 pontos;
  - 10/10.

Conclusão:

- o onset exato não é necessário para **detecção**;
- o hinge contém informação específica da curva;
- ele não é um timestamp físico confiável;
- o nome correto é “âncora causal de alinhamento”.

### M34–M35 — endpoint

- M34, sucesso exigido até `t50`: 63,07%, falha forte.
- Diagnóstico até `t50+4`: 75,76%.
- M35, novo teste independente com latência +4:
  - 75,50%;
  - 9/10;
  - FPR 10/10.

Conclusão: o endpoint exato pode ser retirado se forem aceitas até quatro cadências de latência algorítmica.

### M36 — forma

- Banco de quatro formas:
  - recall 75,71%;
  - 10/10.
- Acurácia da forma vencedora:
  - 28,96%;
  - 0/10 no gate de identificação.

Conclusão: a forma verdadeira não é necessária para detectar, mas a forma vencedora não é uma classificação confiável.

### M37 e M37R — duração

M37:

- controle passou 1/10;
- resultado invalidado;
- candidato descritivo ≈73,46%.

M37R, com 200 mil negativos por família:

- controle:
  - 75,53%;
  - 10/10.
- banco completo de 37 durações:
  - 74,69%;
  - 8/10;
  - perda pareada ≈0,846 ponto.
- identificação:
  - duração exata 2,56%;
  - dentro de ±2: 11,69%;
  - 0/10.

Conclusão: a duração verdadeira não é necessária para detectar dentro do simulador; a duração vencedora é praticamente inútil como estimativa física.

### M38A — parâmetro contínuo `u`

Teste determinístico, sem outcomes:

- K=2 falhou na curva completa.
- K=3 passou na curva completa, mas falhou na geometria local.
- K=5 passou:
  - grade `[0, 0.25, 0.5, 0.75, 1]`;
  - retenção mínima refinada ≈99,7769%.

Conclusão: K=5 é estruturalmente elegível, não operacionalmente confirmada.

### M38B

Estado atual:

- pré-registro e implementação existem;
- grade K=5 foi incorporada;
- candidato teria 73.260 hipóteses por curva;
- a execução operacional não terminou;
- não há limiar, recall, FPR, holdout ou veredito válido.

---

# 4. O que pode ser afirmado hoje

## Afirmação forte, mas somente sintética

> Sob o gerador atual, em SNR final 13,75 e usando oito referências, o detector com projeção do modo comum, âncora causal, busca rolling e bancos de forma/duração alcança aproximadamente 74%–76% de recall com falso alerta controlado pelo contrato interno.

## Afirmações intermediárias

- O modo comum das referências contém informação decisiva para remover os artefatos compartilhados simulados.
- O hinge contém informação curva-específica para alinhamento.
- Marginalizar sobre forma e duração custa pouco recall.
- Os parâmetros vencedores não são bons estimadores dos parâmetros verdadeiros.

## Afirmações proibidas

Não há suporte para afirmar que:

- o ARARA detecta transientes astronômicos reais;
- 13,75σ é o requisito físico final;
- quatro cadências são uma latência aceitável;
- o FPR atual é aceitável por campo/hora;
- o detector tem PPV útil para eventos raros;
- a forma ou duração escolhida descrevem o evento real;
- um telescópio 6U ou 12U fecha em potência, óptica ou telemetria;
- FLOCK melhora a confiabilidade;
- a missão está pronta para engenharia.

---

# 5. Limitações críticas

## 5.1. Modelo fechado e matched ao detector

Os positivos pertencem exatamente a quatro famílias conhecidas. As durações reais pertencem exatamente ao intervalo pesquisado. O parâmetro `u` pertence exatamente ao modelo usado pelo banco.

Isso é um teste **closed-world**. O detector nunca foi obrigado a lidar com uma morfologia positiva fora do vocabulário.

A consequência é importante:

> O banco demonstrou capacidade de marginalizar dentro do próprio modelo, não robustez a transientes desconhecidos.

## 5.2. Nuisance quase rank-one

Os artefatos compartilhados são injetados nas estrelas por um processo comum com multiplicadores próximos.

A projeção do modo comum é precisamente o operador esperado para remover um nuisance dessa forma. O ganho enorme do M30 é matematicamente plausível, mas pode ser específico da simetria do simulador.

É necessário testar:

- efeitos cromáticos;
- PSF e centroid drift;
- transparência não linear;
- diferentes acoplamentos temporais;
- múltiplos modos comuns;
- referências variáveis;
- artefatos target-only;
- gaps;
- saturação;
- cosmic rays;
- heteroscedasticidade fotônica;
- crowded fields.

## 5.3. FPR por curva não é taxa operacional

O alvo de calibração é aproximadamente 0,5% por curva-alvo, com gate de até 1% no holdout.

Para 10.000 curvas-alvo independentes, 0,5% corresponde, em expectativa, a cerca de 50 alertas falsos. Isso ainda não inclui repetição ao longo do tempo.

Sem:

- número de alvos por campo;
- duração da curva;
- cadência física;
- sobreposição entre janelas;
- dependência entre alvos;
- prevalência de eventos;

não é possível obter falso alerta por campo/hora ou PPV.

Este é um bloqueio de missão, não um detalhe de apresentação.

## 5.4. SNR sem ponte instrumental

O SNR é amplitude em unidades do desvio-padrão estacionário do simulador.

Ainda falta mapear:

\[
\text{magnitude, abertura, throughput, céu, exposição, read noise, dark, jitter}
\longrightarrow
\text{SNR do detector}.
\]

Além disso, 13,75σ foi escolhido antes da descoberta do detector projetado. O detector atual pode ter uma curva dose-resposta muito diferente.

## 5.5. Model uncertainty domina a incerteza estatística

Os holdouts contêm dezenas de milhares de curvas e produzem intervalos estreitos. Isso dá boa precisão **condicional ao simulador**.

Mas a maior incerteza não é binomial. É:

- escolha das famílias;
- distribuição dos parâmetros;
- modelo de ruído;
- distribuição de artefatos;
- acoplamento das referências;
- prevalência;
- conversão física.

Intervalos estreitos não reduzem essa incerteza.

## 5.6. Independência limitada

M21, M31 e outros testes usam dados novos, mas compartilham:

- o mesmo simulador;
- a mesma árvore de dependências;
- a mesma implementação;
- as mesmas escolhas de famílias.

Um bug sistemático ou uma hipótese errada pode sobreviver a todas as seeds.

É necessária ao menos uma reimplementação independente dos marcos M31/M37R.

## 5.7. Multiplicidade do programa inteiro

Cada marco controlou sua própria hipótese, mas dezenas de hipóteses foram testadas sequencialmente.

Isso é aceitável como programa exploratório com confirmações locais, porém não existe um controle global de erro para “M1–M38”.

Por isso, a força dos resultados deve ser ordenada:

1. descoberta + réplica independente;
2. passe prospectivo único;
3. diagnóstico pós-hoc;
4. resultado descritivo de teste inválido.

## 5.8. Terminologia de confiança

Nos marcos antigos, pares de quantis 0,05 e 0,95 foram ocasionalmente chamados de intervalo de 95%.

Correto:

- cada extremo é um limite unilateral de 95%;
- juntos formam um intervalo central de 90%.

Os relatórios posteriores corrigiram isso. Um erratum mestre deve harmonizar os documentos antigos.

---

# 6. Auditoria de reproducibilidade

## Pontos fortes

- pré-registros por marco;
- seeds registradas;
- arquivos de especificação;
- hashes;
- logs de incidentes;
- testes automatizados;
- relatórios de recomputação do veredito em M37R e M38A;
- pacotes ZIP completos;
- ausência de substituição silenciosa de holdouts.

Nos pacotes armazenados:

- M37R registra 7 testes aprovados e recomputação do veredito `MATCH`;
- M38A registra 7 testes aprovados e recomputação `MATCH`;
- os warnings do runtime de planilha nos logs são externos ao código científico.

## Incidentes corretamente registrados

- M31: interrupção após holdouts 0–6; 7–9 concluídos com seeds congeladas.
- M37: execução em blocos e auditoria posterior.
- M38B: reset do runtime e perda do estado parcial.

Esses incidentes não devem ser escondidos. A documentação existente é um ponto positivo.

## Problemas específicos do M38B recovery

A recuperação é transparente, mas ainda não está pronta para ser tratada como execução científica final.

### Inconsistência de identidade

O pré-registro M38B contém seeds `2026090501–04`, enquanto o recovery usa `2026090601–04`.

Isso deveria receber um novo identificador formal, por exemplo:

`M38B-R`.

Um arquivo de auditoria não substitui completamente um novo pré-registro com as seeds efetivas.

### Freeze incompleto

O manifesto de recuperação verifica seis arquivos centrais, mas não cobre toda a árvore de dependências, o script de execução e uma suíte de testes-fonte.

O ZIP contém as dependências e importa corretamente, porém a proteção por hash da recuperação deveria incluir tudo o que pode alterar o resultado.

### Estado dos resultados

Não há:

- `FROZEN_THRESHOLDS.json`;
- calibração agrupada;
- arquivos de holdout;
- `VERDICT.json`;
- relatório final.

Portanto, M38B permanece não executado até o fim.

### Alegação de progresso parcial

Houve na conversa uma alegação anterior de 945 mil curvas calculadas, seguida pela informação de que nenhum resultado parcial utilizável sobreviveu.

Como o conjunto atual de artefatos não contém esses chunks, o número não é auditável e deve ser excluído do registro científico.

O único estado defensável é:

`M38B-R — calibração não concluída`.

---

# 7. Avaliação por dimensão

| Dimensão | Avaliação |
|---|---|
| Honestidade sobre falhas | Forte |
| Pré-registro local | Forte |
| Controle de look-elsewhere | Forte nos marcos tardios |
| Controle de FPR dentro do simulador | Forte |
| Replicação por novas seeds | Boa |
| Reimplementação independente | Ausente |
| Robustez a model misspecification | Fraca |
| Validação fora da distribuição | Ausente |
| Validação em dados reais | Ausente |
| Ponte fotônica/instrumental | Incompleta |
| Taxa operacional/PPV | Ausente |
| Viabilidade de missão | Não demonstrada |
| Maturidade como bancada de pesquisa | Alta |
| Maturidade como detector astronômico | Baixa |
| Maturidade como missão | Muito baixa |

---

# 8. O principal resultado real do trabalho

O maior valor obtido não é “provar uma missão”.

É este:

> Foi construída uma bancada sintética auditável que eliminou várias ideias ruins, isolou o principal mecanismo útil — projeção do modo comum das referências — e mostrou como retirar progressivamente informações-oráculo sem esconder a perda de identificabilidade dos parâmetros.

Isso é uma contribuição real de método e engenharia de pesquisa.

A arquitetura sintética atual é:

1. normalização e whitening;
2. construção do modo comum das referências;
3. projeção do residual e do template ortogonalmente ao modo comum;
4. âncora causal de alinhamento;
5. confirmação em oito cadências;
6. busca rolling de primeiro cruzamento;
7. marginalização sobre forma e duração;
8. grade latente estrutural K=5, ainda não confirmada operacionalmente.

---

# 9. Próximas etapas rigorosas

## Etapa 1 — corrigir o M38B antes de executar

Criar `M38B-R` com:

- novo pré-registro contendo as seeds reais `2026090601–04`;
- hash de todas as dependências;
- hash do script;
- testes-fonte incluídos;
- ambiente/versões congelados;
- checkpoint por bloco e por chunk;
- verificação automática dos hashes antes da primeira curva;
- manifesto das calibrações antes dos holdouts.

Não alterar grade, gates ou matemática.

## Etapa 2 — concluir o M38B-R

Se o controle falhar, o candidato fica sem veredito.

Se o candidato passar:

- o último oráculo paramétrico do banco sintético será retirado para detecção;
- `u`, forma e duração vencedores continuarão sem significado físico até prova separada.

Se falhar:

- não ajustar a grade pós-hoc;
- usar apenas diagnósticos congelados para formular um novo teste.

## Etapa 3 — dose-resposta do detector autônomo final

Depois de congelar a arquitetura completa, repetir SNR em uma grade nova.

O objetivo é determinar a curva de recall do **detector final**, não do detector-oráculo antigo.

## Etapa 4 — bateria out-of-distribution

Congelar um simulador adversarial separado, idealmente implementado sem importar o gerador atual:

- formas não incluídas;
- múltiplos picos;
- rises com platô;
- sinais negativos;
- mudanças de cor;
- gaps;
- glitches target-only;
- referências contaminadas;
- ruído Poisson heteroscedástico;
- drifts não rank-one;
- crowded fields;
- cadência irregular;
- eventos sobrepostos.

## Etapa 5 — dados reais com injeções cegas

Aplicar o detector congelado a séries reais, com injeções cegas e divisão por campos/épocas.

O ideal é que a equipe que injeta os sinais não seja a mesma que ajusta o detector.

## Etapa 6 — métrica operacional

Substituir o FPR abstrato por:

- falso alerta por alvo-hora;
- falso alerta por campo-hora;
- carga diária de candidatos;
- PPV por prevalência;
- latência em segundos/minutos;
- custo computacional e energético por campo.

## Etapa 7 — ponte de missão

Só depois conectar:

- fluxo fotônico;
- abertura;
- throughput;
- magnitude;
- exposição;
- céu;
- jitter;
- pointing;
- CPU;
- memória;
- downlink;
- bateria;
- duty cycle.

FLOCK deve ser reintroduzido apenas com um modelo explícito de coincidência espacial, temporal e entre nós.

---

# 10. Conclusão final

A revisão não encontrou base para dizer que o ARARA já seja um telescópio ou detector astronômico validado.

Também não encontrou base para descartar o trabalho como inútil.

A conclusão equilibrada é:

> **O projeto evoluiu de uma reconstrução que refutou o detector inicial para uma arquitetura sintética causal, auditável e internamente robusta. O resultado central — projeção do modo comum das referências — foi confirmado. A detecção deixou de depender de onset, endpoint, forma e duração exatos dentro do simulador. Porém, a validade externa continua essencialmente aberta, e o M38B ainda não concluiu a retirada operacional do último parâmetro latente.**

O próximo salto de conhecimento não virá de dezenas de novos marcos no mesmo simulador.

Virá de:

1. terminar corretamente o M38B-R;
2. testar misspecification;
3. usar dados reais;
4. converter FPR e SNR em unidades operacionais e físicas.
