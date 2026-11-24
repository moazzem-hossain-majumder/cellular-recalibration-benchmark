"""Recreate the existing 57-row source fit, verify archived Rome predictions, freeze it."""
import sys,json,hashlib,platform
from pathlib import Path
import numpy as np
import pandas as pd
import joblib,sklearn
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.data.loader import load_raw_8224890,extract_sessions_8224890
from src.data.splits import create_experiment_splits
from src.models.baselines import HistGradientBoostingThroughputPredictor
from src.features.builder import FEATURE_COLS
OUT=ROOT/'results/prospective_planning';OUT.mkdir(parents=True,exist_ok=True)
_,early=extract_sessions_8224890(load_raw_8224890());src=early[early.operator=='Op1']
split=create_experiment_splits(src,src,'within_domain',[10])
assert len(split.train)==57
model=HistGradientBoostingThroughputPredictor().fit(split.train,split.train.target_y.to_numpy())
source=pd.read_csv(ROOT/'results/marur/opportunities.csv.gz',float_precision='round_trip')
rome=source[source.cohort.isin(['E1','E3'])&source.HistGBM.notna()]
pred=model.predict(rome);np.testing.assert_allclose(pred,rome.HistGBM,rtol=1e-12,atol=1e-12)
artifact=OUT/'frozen_rome_histgbm.joblib';joblib.dump(model,artifact)
np.testing.assert_array_equal(joblib.load(artifact).predict(rome),pred)
initial=source[(source.cohort=='E1')&(source.partition=='cal')].sort_values(['issue','id']).head(10)
assert len(initial)==10 and initial.HistGBM.notna().all()
initial[['id','issue','ready','pattern','HistGBM','y']].rename(columns={'HistGBM':'point'}).to_csv(OUT/'proposed_initial_observations.csv',index=False)
receipt={'training_rows':57,'verified_rome_predictions':len(rome),'maximum_absolute_prediction_difference':float(np.max(abs(pred-rome.HistGBM))),
    'model_sha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),'features':FEATURE_COLS,'python':platform.python_version(),'sklearn':sklearn.__version__,
    'status':'existing model recreated and frozen; field feature compatibility unverified','initialization':'E1 earliest ten archived calibration labels; proposal only',
    'raw_source_sha256':hashlib.sha256((ROOT/'data/raw/8224890/Throughput Tests - Speedtest - Active Measurements.csv').read_bytes()).hexdigest()}
(OUT/'model_freeze.json').write_text(json.dumps(receipt,indent=2)+'\n')
profile=ROOT/'configs/prospective_video_profile.json';cfg=json.loads(profile.read_text());cfg['model_sha256']=receipt['model_sha256'];cfg['initial_observation_ids']=initial.id.tolist();profile.write_text(json.dumps(cfg,indent=2)+'\n')
print(receipt)
