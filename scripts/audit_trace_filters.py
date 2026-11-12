"""Count raw exclusions and timestamp anomalies before/after target filtering."""
import sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.validate_session_boundaries import DATA_DIR, DIAGNOSTICS_DIR
from src.data.loader import clean_numeric

def main():
    checks=[]
    for path in sorted(DATA_DIR.glob('*.csv')):
        df=pd.read_csv(path,sep=';',low_memory=False)
        df.columns=df.columns.str.strip()
        times=pd.to_datetime(df.Day+' '+df['Timestamp [dd.mm.yyyy,hh:mm:ss.ss]'],format='%d.%m.%Y %H:%M:%S.%f',errors='coerce')
        for ue in (1,2):
            col=next(c for c in df if 'Mean Netw. DL' in c and f': [{ue}]' in c)
            y=clean_numeric(df[col])
            keep=y.notna() & (y>=0)
            gaps=times[keep].diff().dt.total_seconds()
            checks.append(dict(file=path.name,operator=f'Op{ue}',raw_rows=len(df),nonnumeric_or_missing=int(y.isna().sum()),negative=int((y<0).sum()),retained=int(keep.sum()),recorded_zero=int((y==0).sum()),invalid_retained_time=int(times[keep].isna().sum()),backward=int((gaps<0).sum()),same_time=int((gaps==0).sum()),raw_gaps_over_10s=int((times.diff().dt.total_seconds()>10).sum()),retained_gaps_over_10s=int((gaps>10).sum())))
    pd.DataFrame(checks).to_csv(DIAGNOSTICS_DIR/'trace_filters.csv',index=False)
if __name__=='__main__':
    main()

