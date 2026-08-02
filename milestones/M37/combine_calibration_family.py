from pathlib import Path
import sys,numpy as np
root=Path(__file__).resolve().parent
family=sys.argv[1]; parts=root/'results'/'calibration_parts'
paths=sorted(parts.glob(f'{family}_chunk_*.npz'))
if not paths: raise RuntimeError('no chunks')
keys=None; collected={}
for path in paths:
    with np.load(path) as data:
        if keys is None:
            keys=list(data.files);collected={k:[] for k in keys}
        if list(data.files)!=keys: raise RuntimeError('key mismatch')
        for k in keys: collected[k].append(data[k])
out={k:np.concatenate(v) for k,v in collected.items()}
if len(next(iter(out.values())))!=50000: raise RuntimeError(f'wrong total {len(next(iter(out.values())))}')
final=parts/f'{family}.npz';np.savez_compressed(final,**out)
print(f'{family}: combined {len(paths)} chunks n=50000 size={final.stat().st_size/1024**2:.3f}MB')
