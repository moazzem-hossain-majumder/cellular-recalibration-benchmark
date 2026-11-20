"""Evaluate fixed-clock persistence on the public NUWiNS Drive 2 AT&T subset."""
import bisect
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import pickle
import pickletools
import statistics
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw/nuwins-pam2025'
OUT = ROOT / 'results/external_validation'
COMMIT = '782b712599f3710f7d3acff57097af6ca14660ae'
BASE = f'https://raw.githubusercontent.com/NUWiNS/pam2025-multi-carrier-dataset/{COMMIT}'
SHARDS = {
    'atnt_day_1_d2_dl.csv': '74d89268f157d5bf0bab6d86fea580559f47e897',
    'atnt_day_2_d2_dl.csv': '6d28798d567d91924db534ba8c9f8e3bacd5e241',
    'atnt_day_3_d2_dl.csv': '30ca787c4da9a9c89d0e36fd7018c3eafe3d610e',
    'atnt_day_4_cst_d2_dl.csv': '46bf08c4b66dac00cdc2de8ecfb286d395d604eb',
    'atnt_day_4_d2_dl.csv': 'b9f84fe62ae2977d5edfa8a751c7635cbcd42c86',
}
META = 'downlink_start_end_times.pkl'
RATE = 'Smart Phone Smart Throughput Mobile Network DL Throughput [Mbps]'


def acquire():
    RAW.mkdir(parents=True, exist_ok=True)
    receipt = {}
    for name, oid in {**SHARDS, META: 'a219d8f44ba173745913bc83b13b61c9f8c3d2a4'}.items():
        folder = ('datasets/raw_files/xcal_raw/start_end_times' if name == META
                  else 'datasets/processed_files/extracted_tput_data/atnt/DL')
        url = f'{BASE}/{folder}/{name}'
        path = RAW / name
        if name == META:
            data = path.read_bytes() if path.exists() else urlopen(url, timeout=120).read()
            blob = data
        else:
            url = url.replace('raw.githubusercontent.com/', 'media.githubusercontent.com/media/')
            data = path.read_bytes() if path.exists() else urlopen(url, timeout=120).read()
            digest = hashlib.sha256(data).hexdigest()
            blob = f'version https://git-lfs.github.com/spec/v1\noid sha256:{digest}\nsize {len(data)}\n'.encode()
        if hashlib.sha1(f'blob {len(blob)}'.encode() + bytes(1) + blob).hexdigest() != oid:
            raise ValueError(f'Unexpected source bytes for {name}')
        if not path.exists():
            path.write_bytes(data)
        receipt[name] = dict(url=url, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), git_blob=oid)
    return receipt


def main():
    receipt = acquire()
    meta = (RAW / META).read_bytes()
    plain = set('TUPLE2 MARK MEMOIZE EMPTY_DICT SETITEMS SHORT_BINUNICODE FRAME BINFLOAT APPENDS STOP PROTO EMPTY_LIST'.split())
    if any(op.name not in plain for op, _, _ in pickletools.genops(meta)):
        raise ValueError('Unexpected object in source metadata')
    intervals = sorted(pickle.loads(meta)['AT&T'])
    assert all(end < next_start for (_, end), (next_start, _) in zip(intervals, intervals[1:]))
    samples = {}
    shard_dates = set()
    for name in SHARDS:
        with (RAW / name).open(newline='') as handle:
            for row in csv.DictReader(handle):
                if row['GPS Time']:
                    shard_dates.add(datetime.fromtimestamp(float(row['GPS Time']), timezone.utc).date().isoformat())
                if row[RATE] and row['GPS Time']:
                    rate = float(row[RATE])
                    if math.isfinite(rate) and rate >= 0:
                        gps = float(row['GPS Time'])
                        # GPS is whole seconds. Order same-second observations by logger time.
                        key = (float(row['TIME_STAMP']), rate)
                        if gps not in samples or key[0] > samples[gps][0]:
                            samples[gps] = key
    times = sorted(samples)
    selected = [(s,e) for s,e in intervals if datetime.fromtimestamp(s,timezone.utc).date().isoformat() in shard_dates]
    records = []
    for idx, (start, end) in enumerate(selected):
        for issue in range(math.ceil(start / 60) * 60, math.floor(end) + 1, 60):
            left = bisect.bisect_left(times, max(start, issue - 60))
            mid = bisect.bisect_left(times, issue)
            right = min(bisect.bisect_left(times, issue + 60), bisect.bisect_right(times, end))
            before = times[mid - 1] if mid > left else None
            after = times[right - 1] if right > mid else None
            records.append(dict(interval=idx, start=start, end=end, issue=issue,
                                date=datetime.fromtimestamp(issue, timezone.utc).date().isoformat(),
                                lag_time=before, target_time=after,
                                point=samples[before][1] if before is not None else None,
                                y=samples[after][1] if after is not None else None))
    dates = sorted(shard_dates)
    test = [r for r in records if r['date'] in dates[2:]]
    pool = [r for r in records if r['date'] in dates[:2] and r['point'] is not None and r['y'] is not None]
    cal = pool[:10]
    assert len(cal) == 10 and max(r['target_time'] for r in cal) < min(r['issue'] for r in test)
    offset = sorted(r['point'] - r['y'] for r in cal)[math.ceil((len(cal)+1)*0.90)-1]
    for r in records:
        r['partition'] = 'test' if r['date'] in dates[2:] else ('cal_used' if r in cal else 'cal_unused')
        r['lower'] = max(0, r['point'] - offset) if r['point'] is not None else None

    def metrics(rows):
        issued = [r for r in rows if r['point'] is not None]
        observed = [r for r in issued if r['y'] is not None]
        bad = sum(r['lower'] > r['y'] for r in observed)
        unresolved_positive = sum(r['lower'] > 0 and r['y'] is None for r in issued)
        return dict(ticks=len(rows), issued=len(issued), abstained=len(rows)-len(issued),
                    scored=len(observed), missing_issued=len(issued)-len(observed),
                    positive=sum(r['lower'] > 0 for r in issued), violations=bad,
                    observed_coverage=1-bad/len(observed), observed_violation=bad/len(observed),
                    mae_mbps=statistics.mean(abs(r['point']-r['y']) for r in observed),
                    supported=sum(min(r['lower'],r['y']) for r in observed)/sum(r['y'] for r in observed),
                    all_issued_violation_bounds=[bad/len(issued),(bad+unresolved_positive)/len(issued)])
    OUT.mkdir(parents=True,exist_ok=True)
    summary = dict(commit=COMMIT, cohort='AT&T Drive 2', files=receipt, source_windows=len(intervals), windows=len(selected),
                   dates=dates, calibration_dates=dates[:2], test_dates=dates[2:],
                   test_tick_counts={d:sum(r['date']==d for r in test) for d in dates[2:]},
                   calibration_pool=len(pool),
                   calibration_used=10, offset_mbps=offset, test=metrics(test),
                   by_test_date={d:metrics([r for r in test if r['date']==d]) for d in dates[2:] if any(r['date']==d for r in test)})
    (OUT/'nuwins_drive2_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    with (OUT/'nuwins_drive2_forecasts.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    print(json.dumps({k:v for k,v in summary.items() if k!='files'},indent=2))


if __name__ == '__main__':
    main()
