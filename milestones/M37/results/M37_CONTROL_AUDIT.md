# M37 — Auditoria suplementar de controle

## Estado

Esta auditoria foi executada depois dos resultados e é diagnóstica. Ela não altera limiares, gates, seeds ou veredito.

## Testes congelados

`[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m                                                                 [100%][0m
[33m=============================== warnings summary ===============================[0m
../../../opt/pyvenv/lib/python3.13/site-packages/_pytest/cacheprovider.py:475
  /opt/pyvenv/lib/python3.13/site-packages/_pytest/cacheprovider.py:475: PytestCacheWarning: cache could not write path /mnt/data/ARARA_M37/.pytest_cache/v/cache/nodeids: [Errno 13] Permission denied: '/mnt/data/ARARA_M37/.pytest_cache/v/cache/nodeids'
    config.cache.set("cache/nodeids", sorted(self.cached_nodeids))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
[33m[32m8 passed[0m, [33m[1m1 warning[0m[33m in 0.94s[0m[0m`

## Integridade dos arquivos

- entradas verificadas: 53
- divergências SHA-256: 0

## Equivalência M36–M37

O controle do M37 foi comparado diretamente, nas mesmas curvas, com o banco de quatro formas do M36 usando a duração verdadeira.

- grupos positivos auditados: 8
- famílias negativas auditadas: 5
- maior diferença absoluta de score: 2.300e-13
- divergências na forma vencedora: 0

Conclusão: não foi encontrada evidência de que a invalidação do controle tenha sido causada pela vetorização do M37.

## Sensibilidade da cauda de calibração

Os limiares dos blocos de 5.000 são apresentados apenas como diagnóstico de sensibilidade da cauda; não são intervalos de confiança e não substituem a calibração congelada de 50.000.

- limiar M36, 50.000 `shared_step`: 7.105932
- limiar M37, 50.000 `shared_step`: 7.280584

A diferença entre calibrações independentes é compatível com um gate estratificado muito próximo da fronteira, mas esta observação é pós-hoc e não autoriza substituir o limiar do M37.
