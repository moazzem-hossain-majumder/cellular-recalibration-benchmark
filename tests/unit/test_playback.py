import numpy as np
import pytest
from scripts.replay_oslo_playback import playback


def test_constant_capacity_playback_and_unfinished_bytes():
    s = np.ones(7)
    result = playback(s, np.ones(7), np.full(7,.75))
    assert result['segments']==3
    assert result['startup_s']==1.5
    assert result['stall_s']==0
    assert result['mean_bitrate']==.75
    assert result['unfinished_bytes']==pytest.approx(62500)


def test_zero_service_and_late_stall():
    result = playback(np.ones(9),np.array([1,1,1,0,0,0,0,0,0]),np.full(9,.3))
    assert result['segments']==1
    assert result['stall_s']==pytest.approx(4.4)
    empty = playback(np.ones(9),np.zeros(9),np.zeros(9))
    assert empty['segments']==0 and np.isnan(empty['stall_fraction'])

def test_request_delay_exhausts_trace_without_false_completion():
    result = playback(np.ones(7),np.ones(7),np.full(7,.75),request_delay_s=10)
    assert result['segments']==0 and np.isnan(result['startup_s'])
    assert result['unfinished_bytes']==0


def test_longer_segments_change_startup_and_completed_count():
    result = playback(np.ones(7),np.ones(7),np.full(7,.75),segment_s=4)
    assert result['segments']==1
    assert result['startup_s']==3
    assert result['mean_bitrate']==.75
    assert result['stall_s']==0
    assert result['unfinished_bytes']==pytest.approx(250000)
