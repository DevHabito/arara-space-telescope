from pathlib import Path
import json,sys,time
import numpy as np
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root))
import arara_m37 as m
family=sys.argv[1]
results=root/'results'; parts=results/'calibration_parts'
manifest=json.loads((results/'PRE_CALIBRATION_FREEZE_SHA256.json').read_text())
for relative,expected in manifest.items():
    observed=m.sha256_file(root/relative)
    if observed!=expected: raise RuntimeError(f'freeze mismatch {relative}')
opened=results/'CALIBRATION_OPENED.json'
if not opened.exists():
    try:
        opened.write_text(json.dumps({'status':'OPENED_ONCE','calibration_seed':m.Config().calibration_seed,'negatives_per_family':m.Config().calibration_negatives_per_family,'control_hypotheses':396,'full_hypotheses':14652,'freeze_manifest_sha256':m.sha256_file(results/'PRE_CALIBRATION_FREEZE_SHA256.json')},indent=2))
    except FileExistsError: pass
path=parts/f'{family}.npz'
if path.exists():
    print(f'{family}: already complete');sys.exit(0)
cfg=m.Config();plan=json.loads((root/'FROZEN_SEEDS.json').read_text())
t=time.perf_counter();out=m.generate_calibration_family(family,cfg,plan);np.savez_compressed(path,**out)
print(f'{family}: n={len(out["score_rolling_four_shape_full_duration_bank_latency4"])} elapsed={time.perf_counter()-t:.2f}s size={path.stat().st_size/1024**2:.3f}MB')
