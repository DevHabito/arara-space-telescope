# M27 calibration execution recovery log

A chamada que tentava gerar todas as cinco famílias atingiu o limite técnico do executor após concluir três arquivos. Os arquivos `quiet`, `shared_ramp` e `shared_step` foram reabertos e verificados: cada um continha exatamente 50.000 scores finitos e 50.000 endpoints.

As duas famílias restantes foram geradas separadamente com as seeds congeladas. Nenhum código, seed, tamanho amostral, ordem de família, regra de limiar ou gate foi alterado.
