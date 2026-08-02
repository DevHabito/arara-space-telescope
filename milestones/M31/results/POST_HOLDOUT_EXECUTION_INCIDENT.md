# M31 — Registro de interrupção de execução

Durante a execução sequencial dos dez holdouts, o ambiente interrompeu a chamada após 60 segundos quando os holdouts 0–6 já haviam sido persistidos.

Procedimento adotado:

1. os arquivos persistidos dos holdouts 0–6 foram verificados no sistema de arquivos;
2. nenhuma seed, curva, família, estrato ou lote foi substituído;
3. os holdouts 7–9 foram executados posteriormente com as seeds originalmente congeladas;
4. nenhum critério, limiar, código matemático ou gate foi alterado;
5. a agregação ocorreu somente depois da presença dos sete arquivos exigidos para cada um dos dez holdouts.

A interrupção foi operacional e não altera o resultado científico.
