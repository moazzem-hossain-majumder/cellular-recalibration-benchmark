from scripts.replicate_nuwins_drive3 import RADIO, RATE, opportunities
import numpy as np
import pandas as pd


def test_drive3_features_and_labels_respect_transfer_and_clock():
    times=[55,61,119,120,130,141]
    frame=pd.DataFrame({'GPS Time':times,'TIME_STAMP':times,RATE:[99,1,2,3,4,100],
                        **{key:times for key in RADIO}})
    rows=opportunities(frame,[(59,140)],['1970-01-01'])
    assert rows.issue.tolist()==[60,120]
    assert np.isnan(rows.iloc[0].y_lag1)
    assert rows.iloc[0].y==2
    tick=rows.iloc[1]
    assert (tick.y_lag1,tick.lag_age_s,tick.prev_duration_s,tick.rsrp)==(2,1,58,119)
    assert tick.y==4 and tick.target_time==130
