from __future__ import annotations
from pathlib import Path
import json, hashlib, os, sys, time, zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np, pandas as pd

ROOT=Path('/mnt/data/ARARA_M38B')
RESULTS=ROOT/'results'; RESULTS.mkdir(exist_ok=True)
for d in ['calibration_blocks','calibration_parts','holdouts']:(RESULTS/d).mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT))
import arara_m38b as m

# Recovery note: original freeze manifest was incomplete after runtime reset; scientific prereg/spec/code survived.
(ROOT/'RECOVERY_AUDIT.md').write_text('''# M38B recovery audit\n\nThe prior runtime was reset after preregistration. The scientific preregistration, specification, implementation, and M38A frozen grid survived, but the original seed file and orchestration/test files did not. Therefore this execution is treated as a fresh confirmatory recovery run, with the same mathematics and gates, newly frozen seeds, and no reuse of calibration or holdout outcomes.\n\nRecovery seeds: calibration 2026090601, holdouts 2026090602, aggregate bootstrap 2026090603, paired bootstrap 2026090604.\n''',encoding='utf-8')

class Cfg(m.Config):
    calibration_seed:int=2026090601
    holdout_root_seed:int=2026090602
    aggregate_bootstrap_root_seed:int=2026090603
    paired_difference_bootstrap_seed:int=2026090604

cfg=Cfg(calibration_seed=2026090601,holdout_root_seed=2026090602,aggregate_bootstrap_root_seed=2026090603,paired_difference_bootstrap_seed=2026090604)
# build_seed_plan uses instance values
plan=m.build_seed_plan(cfg)
(ROOT/'FROZEN_SEEDS_RECOVERY.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
freeze_files=['ARARA_M38B_PREREGISTRATION.md','ARARA_M38B_SPEC.json','arara_m38b.py','FROZEN_LATENT_GRID_M38A.json','RECOVERY_AUDIT.md','FROZEN_SEEDS_RECOVERY.json']
manifest={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in freeze_files}
(RESULTS/'PRE_CALIBRATION_RECOVERY_FREEZE_SHA256.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')

FAMS=list(m.NEGATIVE_FAMILIES)
METHODS=list(cfg.methods)

def calibration_family(family:str):
    import sys, json, numpy as np
    from pathlib import Path
    root=Path('/mnt/data/ARARA_M38B'); sys.path.insert(0,str(root)); import arara_m38b as mm
    cc=mm.Config(calibration_seed=2026090601,holdout_root_seed=2026090602,aggregate_bootstrap_root_seed=2026090603,paired_difference_bootstrap_seed=2026090604)
    plan=json.loads((root/'FROZEN_SEEDS_RECOVERY.json').read_text())
    block_paths=[]
    for block in range(cc.calibration_block_count):
        seed=plan['calibration_blocks'][str(block)][family]['integer_seed']
        rng=np.random.default_rng(seed)
        arr=mm.calibration_output_from_rng(family,cc.calibration_negatives_per_block,rng,cc)
        p=root/'results/calibration_blocks'/f'{family}_block_{block:02d}.npz'; np.savez_compressed(p,**arr); block_paths.append(p)
    pooled=mm.combine_calibration_blocks(block_paths,cc.calibration_negatives_per_block,cc.calibration_negatives_per_family)
    out=root/'results/calibration_parts'/f'{family}.npz'; np.savez_compressed(out,**pooled)
    return family,str(out)

if not (RESULTS/'FROZEN_THRESHOLDS.json').exists():
    t=time.time(); paths={}
    with ProcessPoolExecutor(max_workers=5) as ex:
        futs={ex.submit(calibration_family,f):f for f in FAMS}
        for fut in as_completed(futs):
            fam,p=fut.result(); paths[fam]=Path(p); print('calibration complete',fam,flush=True)
    details,table,diag=m.freeze_thresholds(cfg,paths)
    (RESULTS/'FROZEN_THRESHOLDS.json').write_text(json.dumps(details,indent=2),encoding='utf-8')
    table.to_csv(RESULTS/'calibration_metrics.csv',index=False); diag.to_csv(RESULTS/'calibration_diagnostics.csv',index=False)
    drivers=[]
    for method in METHODS:
        s=table[table.method==method]; row=s.loc[s.family_specific_threshold.idxmax()]
        drivers.append({'method':method,'threshold':row.threshold,'driver_family':row.family})
    pd.DataFrame(drivers).to_csv(RESULTS/'threshold_drivers.csv',index=False)
    print('calibration elapsed',time.time()-t,flush=True)

# freeze before holdouts
prehold=['ARARA_M38B_PREREGISTRATION.md','ARARA_M38B_SPEC.json','arara_m38b.py','FROZEN_LATENT_GRID_M38A.json','RECOVERY_AUDIT.md','FROZEN_SEEDS_RECOVERY.json','results/FROZEN_THRESHOLDS.json','results/calibration_metrics.csv','results/calibration_diagnostics.csv','results/threshold_drivers.csv']
prehold_manifest={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in prehold}
(RESULTS/'PRE_HOLDOUT_RECOVERY_FREEZE_SHA256.json').write_text(json.dumps(prehold_manifest,indent=2),encoding='utf-8')

SUFFIXES=[('method_summary','method_summary'),('stratum_summary','strata'),('negative_summary','negative'),('batch_summary','batches'),('pair_counts','pair_counts'),('paired_summary','paired'),('identification_summary','identification'),('timing_detail','timing'),('negative_selection_summary','negative_selection'),('projection_diagnostics','projection')]

def run_holdout(index:int):
    import sys,json
    from pathlib import Path
    root=Path('/mnt/data/ARARA_M38B'); sys.path.insert(0,str(root)); import arara_m38b as mm
    cc=mm.Config(calibration_seed=2026090601,holdout_root_seed=2026090602,aggregate_bootstrap_root_seed=2026090603,paired_difference_bootstrap_seed=2026090604)
    plan=json.loads((root/'FROZEN_SEEDS_RECOVERY.json').read_text()); thresholds=json.loads((root/'results/FROZEN_THRESHOLDS.json').read_text())['thresholds']
    out=mm.evaluate_holdout(cc,plan['holdouts'][index],thresholds)
    for key,suffix in SUFFIXES: out[key].to_csv(root/'results/holdouts'/f'holdout_{index:02d}_{suffix}.csv',index=False)
    return index

if not (RESULTS/'VERDICT.json').exists():
    t=time.time()
    with ProcessPoolExecutor(max_workers=5) as ex:
        futs=[ex.submit(run_holdout,i) for i in range(10)]
        for fut in as_completed(futs): print('holdout complete',fut.result(),flush=True)
    def combine(s): return pd.concat([pd.read_csv(RESULTS/'holdouts'/f'holdout_{i:02d}_{s}.csv') for i in range(10)],ignore_index=True)
    ms=combine('method_summary'); ss=combine('strata'); ns=combine('negative'); bs=combine('batches'); pc=combine('pair_counts'); ps=combine('paired'); ids=combine('identification'); td=combine('timing'); negsel=combine('negative_selection'); proj=combine('projection')
    for df,name in [(ms,'holdout_method_summary.csv'),(ss,'stratum_summary_all_holdouts.csv'),(ns,'negative_summary_all_holdouts.csv'),(bs,'batch_summary_all_holdouts.csv'),(pc,'pair_counts_all_holdouts.csv'),(ps,'paired_summary_all_holdouts.csv'),(ids,'identification_summary_all_holdouts.csv'),(td,'timing_detail_all_positives.csv'),(negsel,'negative_selection_summary_all_holdouts.csv'),(proj,'projection_diagnostics_all_holdouts.csv')]: df.to_csv(RESULTS/name,index=False)
    thresholds=json.loads((RESULTS/'FROZEN_THRESHOLDS.json').read_text())['thresholds']; dr=pd.read_csv(RESULTS/'threshold_drivers.csv'); drivers=dict(zip(dr.method,dr.driver_family))
    agg=m.aggregate_results(cfg,ms,ss,ids,pc,thresholds,drivers); boot=agg.pop('method_bootstrap_df'); delta=agg.pop('delta_bootstrap')
    (RESULTS/'VERDICT.json').write_text(json.dumps(agg,indent=2),encoding='utf-8'); boot.to_csv(RESULTS/'method_bootstrap.csv',index=False); pd.DataFrame({'replicate':np.arange(len(delta)),'grid_minus_control':delta}).to_csv(RESULTS/'paired_delta_bootstrap.csv',index=False)
    print('holdouts elapsed',time.time()-t,flush=True)

# concise reports
v=json.loads((RESULTS/'VERDICT.json').read_text()); ms=pd.read_csv(RESULTS/'holdout_method_summary.csv'); ss=pd.read_csv(RESULTS/'stratum_summary_all_holdouts.csv'); ns=pd.read_csv(RESULTS/'negative_summary_all_holdouts.csv'); ids=pd.read_csv(RESULTS/'identification_summary_all_holdouts.csv')
method_rows=[]
for method,d in v['method_details'].items(): method_rows.append({'method':method,'threshold':d['threshold'],'driver':d['threshold_driver'],'recall':d['aggregate_recall_point'],'lower95':d['aggregate_recall_lower_one_sided_95'],'upper95':d['aggregate_recall_upper_one_sided_95'],'passes':d['holdout_pass_count'],'fpr_passes':d['fpr_pass_holdout_count'],'operational_pass':d['operational_pass']})
pd.DataFrame(method_rows).to_csv(RESULTS/'method_aggregate.csv',index=False)
sa=ss.groupby(['method','stratum']).agg(hits=('hits','sum'),n=('n','sum')).reset_index(); sa['recall']=sa.hits/sa.n; sa.to_csv(RESULTS/'method_stratum_aggregate.csv',index=False)
fa=ns.groupby(['method','family']).agg(alerts=('alerts','sum'),n=('n','sum'),max_upper=('fpr_upper_one_sided_95','max')).reset_index(); fa['rate']=fa.alerts/fa.n; fa.to_csv(RESULTS/'method_fpr_aggregate.csv',index=False)
pd.DataFrame([v['latent_identification']]).to_csv(RESULTS/'latent_identification_aggregate.csv',index=False)
report=f'''# ARARA M38B Recovery — Resultado\n\n**Veredito:** `{v['verdict']}`\n\nEste é um recovery run prospectivamente re-congelado após perda parcial do estado do runtime original. Nenhum outcome anterior de calibração ou holdout foi reutilizado.\n\n## Métodos\n\n'''
for method,d in v['method_details'].items(): report+=f"- `{method}`: threshold={d['threshold']:.6f}, recall={d['aggregate_recall_point']:.6f}, lower95={d['aggregate_recall_lower_one_sided_95']:.6f}, passes={d['holdout_pass_count']}/10, FPR={d['fpr_pass_holdout_count']}/10.\n"
report+=f"\n## Diferença pareada\n\n{v['paired_difference']}\n\n## Identificação latente\n\n{v['latent_identification']}\n\n## Previsão\n\n{v['prediction']}\n"
(RESULTS/'M38B_RECOVERY_RESULT_REPORT_PT_BR.md').write_text(report,encoding='utf-8')
# archive
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.rglob('*') if p.is_file() and p.name!='FINAL_SHA256SUMS.json'}
(RESULTS/'FINAL_SHA256SUMS.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
zip_path=Path('/mnt/data/ARARA_from_zero_M38B_recovery_complete.zip')
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in ROOT.rglob('*'):
        if p.is_file(): z.write(p,p.relative_to(ROOT))
print(json.dumps(v,indent=2)); print('ZIP',zip_path)
