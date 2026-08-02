from pathlib import Path
import json,sys,time
import numpy as np
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root))
import arara_m37 as m
family=sys.argv[1]
chunk_index=int(sys.argv[2])
chunk_size=int(sys.argv[3]) if len(sys.argv)>3 else 5000
cfg=m.Config()
if chunk_size % cfg.calibration_batch_size:
    raise ValueError('chunk_size must be divisible by frozen batch size')
results=root/'results'; parts=results/'calibration_parts'; parts.mkdir(exist_ok=True)
chunk_path=parts/f'{family}_chunk_{chunk_index:02d}.npz'
state_path=parts/f'{family}_state_{chunk_index:02d}.json'
if chunk_path.exists() and state_path.exists():
    print(f'{family} chunk {chunk_index}: already complete');sys.exit(0)
manifest=json.loads((results/'PRE_CALIBRATION_FREEZE_SHA256.json').read_text())
for relative,expected in manifest.items():
    if m.sha256_file(root/relative)!=expected:
        raise RuntimeError(f'freeze mismatch {relative}')
plan=json.loads((root/'FROZEN_SEEDS.json').read_text())
rng=np.random.default_rng()
if chunk_index==0:
    rng=np.random.default_rng(plan['calibration'][family]['integer_seed'])
else:
    prior=parts/f'{family}_state_{chunk_index-1:02d}.json'
    if not prior.exists(): raise RuntimeError(f'missing prior state {prior}')
    rng.bit_generator.state=json.loads(prior.read_text())
core=m.calibration_core(cfg)
pieces={key:[] for key in (
    'score_rolling_four_shape_exact_duration_latency4',
    'score_rolling_four_shape_full_duration_bank_latency4',
    'control_argmax_endpoint','full_argmax_endpoint','full_argmax_shape_index','full_argmax_duration',
    'true_shape_index','true_duration','control_energy_at_max','full_energy_at_max')}
remaining=chunk_size
t=time.perf_counter()
while remaining>0:
    n=min(cfg.calibration_batch_size,remaining)
    output=m.evaluate_negative_family(family,n,rng,cfg,core)
    control_grid=output['control_score_grid'];full_grid=output['full_score_grid']
    control_argmax=np.argmax(control_grid,axis=1);full_argmax=np.argmax(full_grid,axis=1);row=np.arange(n)
    pieces['score_rolling_four_shape_exact_duration_latency4'].append(control_grid[row,control_argmax].astype(np.float32))
    pieces['score_rolling_four_shape_full_duration_bank_latency4'].append(full_grid[row,full_argmax].astype(np.float32))
    pieces['control_argmax_endpoint'].append(cfg.endpoint_grid[control_argmax].astype(np.int16))
    pieces['full_argmax_endpoint'].append(cfg.endpoint_grid[full_argmax].astype(np.int16))
    pieces['full_argmax_shape_index'].append(output['full_shape_index_grid'][row,full_argmax].astype(np.int8))
    pieces['full_argmax_duration'].append(output['full_duration_grid'][row,full_argmax].astype(np.int16))
    pieces['true_shape_index'].append(output['true_shape_index'].astype(np.int8))
    pieces['true_duration'].append(output['true_duration'].astype(np.int16))
    pieces['control_energy_at_max'].append(output['control_energy_grid'][row,control_argmax].astype(np.float32))
    pieces['full_energy_at_max'].append(output['full_energy_grid'][row,full_argmax].astype(np.float32))
    remaining-=n
out={k:np.concatenate(v) for k,v in pieces.items()}
np.savez_compressed(chunk_path,**out)
state_path.write_text(json.dumps(rng.bit_generator.state),encoding='utf-8')
print(f'{family} chunk {chunk_index}: n={chunk_size} elapsed={time.perf_counter()-t:.2f}s')
