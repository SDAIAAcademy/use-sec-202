# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy>=2", "pandas>=2.2"]
# ///
"""Writes the file pack of USE-SEC-202 into labs/files/ and the trainer's key into labs/solutions/.

  uv run labs/_tools/prepare_files.py --raw <a folder outside the course>

Two kinds of files come out of it:

1. Extracts derived from three public datasets. The raw files are never committed: they are read
   from the folder given with --raw and downloaded into it when they are missing.
     <raw>/eia/     EIA-930 six-month balance files, 2023 and 2024 (U.S. Energy Information
                    Administration, Hourly Electric Grid Monitor): hourly demand and the operator's
                    day-ahead demand forecast of one balancing authority.
     <raw>/cmapss/  train_FD001.txt of the NASA C-MAPSS turbofan degradation simulation data.
     <raw>/te/      d00.dat and d<nn>_te.dat of the Tennessee Eastman process simulation data
                    (the files of the Braatz group). Only the detector's index computed from
                    them is written out, never the process variables.
   The three "provided" models are trained here, for real: a day-ahead load forecast on 2023
   scored on 2024, a remaining-life model on 60 engines scored on 40 held-out engines, and a
   principal-component fault detector fitted on normal operation only.

2. The synthetic case files of Dhura Energy (case_texts.py): everything about the company, its
   people, its vendors, its costs and its use cases is invented.

No random number is drawn: the same raw files give the same bytes on every run.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import case_texts as T  # noqa: E402

LABS = Path(__file__).resolve().parent.parent
FILES = LABS / "files"
SOL = LABS / "solutions"

EIA = "https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_BALANCE_{}.csv"
EIA_PARTS = ["2023_Jan_Jun", "2023_Jul_Dec", "2024_Jan_Jun", "2024_Jul_Dec"]
EIA_AUTHORITY = "ERCO"
CMAPSS = "https://phm-datasets.s3.amazonaws.com/NASA/6.+Turbofan+Engine+Degradation+Simulation+Data+Set.zip"
TE = "https://raw.githubusercontent.com/camaramm/tennessee-eastman-profBraatz/master/{}.dat"
TE_RUNS = ["04", "01", "13", "00", "10", "03", "06", "11", "02", "15", "08", "05", "09"]  # R01..R13
TE_ONSET = 160  # samples of normal operation before the fault starts in every test file

# The cost tables of the case (synthetic). The labs and the key read the same numbers.
FORECAST_COST = {"under": 4, "over": 1}
TURBINE = {"needed_lead": 15, "unplanned": 1_800_000, "planned": 400_000, "per_cycle": 6_000,
           "thresholds": [10, 20, 30, 40, 50, 60, 80], "vendor_default": 20}
DETECTOR = {"false_alarm": 3_000, "per_minute": 2_000, "missed": 400_000, "min_share": 0.5}


# ---------------------------------------------------------------- writing

def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip("\n") + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    path.write_text(buf.getvalue(), encoding="utf-8-sig", newline="\n")


def fetch(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    last = None
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=300) as r:
                dest.write_bytes(r.read())
            return
        except Exception as e:  # a transient network error: wait and retry
            last = e
            time.sleep(5 * (attempt + 1))
    raise SystemExit(f"could not fetch {url}: {last}")


# ---------------------------------------------------------------- 1. load forecast

def load_public(raw: Path) -> pd.DataFrame:
    parts = []
    for name in EIA_PARTS:
        f = raw / "eia" / f"{name}.csv"
        fetch(EIA.format(name), f)
        d = pd.read_csv(f, thousands=",", low_memory=False, usecols=[
            "Balancing Authority", "Local Time at End of Hour", "UTC Time at End of Hour",
            "Demand Forecast (MW)", "Demand (MW)"])
        parts.append(d[d["Balancing Authority"] == EIA_AUTHORITY])
    d = pd.concat(parts)
    d = d.rename(columns={"Local Time at End of Hour": "local", "UTC Time at End of Hour": "utc",
                          "Demand Forecast (MW)": "operator", "Demand (MW)": "demand"})
    fmt = "%m/%d/%Y %I:%M:%S %p"
    d["utc"] = pd.to_datetime(d["utc"], format=fmt)
    d["local"] = pd.to_datetime(d["local"], format=fmt) - pd.Timedelta(hours=1)  # hour beginning
    d = d.sort_values("utc").drop_duplicates("utc").reset_index(drop=True)
    hours = pd.date_range(d.utc.min(), d.utc.max(), freq="h")
    assert len(d) == len(hours) == 17544, len(d)
    assert d.demand.notna().all() and d.operator.notna().all()
    d["demand"] = d.demand.astype(float)
    d["operator"] = d.operator.astype(float)
    d["year"] = d.local.dt.year
    d["month"] = d.local.dt.month
    d["hour"] = d.local.dt.hour
    d["dow"] = d.local.dt.dayofweek
    return d


def learned_forecast(d: pd.DataFrame) -> tuple[pd.Series, float]:
    """The vendor's model: a linear model on lagged load and the calendar, trained on 2023.

    Every input is known 24 hours ahead. It sees no weather. Returns the forecast for every
    hour that has its lags, and the in-sample error on 2023 that the brochure quotes."""
    lag = {k: d.demand.shift(k) for k in (24, 48, 168, 192)}

    def design(idx):
        q = d.loc[idx]
        cols = [np.ones(len(q))] + [lag[k].loc[idx].values for k in (24, 48, 168, 192)]
        slot = (q.hour + 24 * (q.dow >= 5)).values
        cols += [(slot == k).astype(float) for k in range(1, 48)]
        cols += [((q.hour.values == h) * lag[24].loc[idx].values) / 1e4 for h in range(24)]
        return np.column_stack(cols)

    ok = lag[192].notna()
    train = d.index[(d.year == 2023) & ok]
    beta, *_ = np.linalg.lstsq(design(train), d.demand.loc[train].values, rcond=None)
    out = pd.Series(np.nan, index=d.index)
    out.loc[d.index[ok]] = design(d.index[ok]) @ beta
    in_sample = float(np.mean(np.abs(out.loc[train] - d.demand.loc[train]) / d.demand.loc[train]) * 100)
    return out.round(0), in_sample


def forecast_files(raw: Path, key: dict) -> None:
    d = load_public(raw)
    vendor, in_sample = learned_forecast(d)
    d["vendor"] = vendor
    d["persistence"] = d.demand.shift(24)
    d["seasonal"] = d.demand.shift(168)
    names = ["vendor", "persistence", "seasonal", "operator"]

    rows = []
    for n, r in enumerate(d.itertuples(), start=1):
        rows.append([n, r.local.strftime("%Y-%m-%d"), r.hour, r.month, r.year,
                     int(r.demand), int(r.operator), "" if r.year == 2023 else int(r.vendor)])
    write_csv(FILES / "load" / "load_hourly.csv",
              ["hour_no", "local_date", "local_hour", "month", "year", "demand_mw",
               "operator_forecast_mw", "vendor_forecast_mw"], rows)

    t = d[d.year == 2024].copy()
    assert len(t) == 8784
    peak_floor = float(np.sort(t.demand.values)[-440])  # the 440 highest hours: the top 5%
    t["peak"] = (t.demand >= peak_floor).astype(int)
    assert int(t.peak.sum()) == 440

    def mae(q, n):
        return float(np.mean(np.abs(q[n] - q.demand)))

    def mape(q, n):
        return float(np.mean(np.abs(q[n] - q.demand) / q.demand) * 100)

    def cost(q, n):
        e = q[n] - q.demand
        return float((-e[e < 0]).sum() * FORECAST_COST["under"] + e[e > 0].sum() * FORECAST_COST["over"])

    rows = []
    for r in t.itertuples():
        row = [r.Index + 1, r.local.strftime("%Y-%m-%d"), r.month, r.hour, r.peak, int(r.demand)]
        for n in names:
            f = getattr(r, n)
            row += [int(f), int(f - r.demand)]
        rows.append(row)
    head = ["hour_no", "local_date", "month", "local_hour", "peak_hour", "demand_mw"]
    for n in names:
        head += [f"{n}_mw", f"{n}_error_mw"]
    write_csv(FILES / "start" / "forecast_errors_2024.csv", head, rows)

    k = {"hours": len(t), "in_sample_mape_2023": round(in_sample, 1), "peak_hours": 440,
         "peak_floor_mw": int(peak_floor)}
    for n in names:
        k[n] = {"mae": round(mae(t, n)), "mape": round(mape(t, n), 2),
                "peak_mape": round(mape(t[t.peak == 1], n), 2),
                "peak_bias": round(float((t[t.peak == 1][n] - t[t.peak == 1].demand).mean())),
                "cost_units_m": round(cost(t, n) / 1e6, 1)}
    k["skill_vs_persistence"] = round((1 - mae(t, "vendor") / mae(t, "persistence")) * 100, 1)
    k["skill_vs_seasonal"] = round((1 - mae(t, "vendor") / mae(t, "seasonal")) * 100, 1)
    k["cost_vs_persistence"] = round((cost(t, "vendor") / cost(t, "persistence") - 1) * 100, 1)
    by_month = {}
    for m in range(1, 13):
        q = t[t.month == m]
        by_month[str(m)] = {n: round(mape(q, n), 2) for n in names}
    k["by_month"] = by_month
    k["months_vendor_loses_to_persistence"] = [m for m in range(1, 13)
                                               if by_month[str(m)]["vendor"] > by_month[str(m)]["persistence"]]
    k["worst_month"] = max(range(1, 13), key=lambda m: by_month[str(m)]["vendor"])
    key["forecast"] = k

    # The historian export: one public week, with four planted recording faults (synthetic).
    w = t[(t.local >= "2024-08-05") & (t.local < "2024-08-12")].copy()
    assert len(w) == 168
    rec = w.demand.astype(int).tolist()
    stamps = [[x.strftime("%Y-%m-%d"), x.hour] for x in w.local]
    planted = []
    for i in range(30, 36):          # a stuck value for six hours
        rec[i] = rec[29]
    planted.append({"fault": "stuck", "from": stamps[30], "hours": 6})
    for i in range(75, 78):          # a gap written as zero for three hours
        rec[i] = 0
    planted.append({"fault": "zeros", "from": stamps[75], "hours": 3})
    rec[110] = rec[110] * 10         # a spike: one value ten times too large
    planted.append({"fault": "spike", "from": stamps[110], "hours": 1})
    rows = [[*stamps[i], rec[i], int(w.vendor.iloc[i])] for i in range(168)]
    rows.insert(141, rows[140][:])   # one hour written twice
    planted.append({"fault": "duplicate", "from": stamps[140], "hours": 1})
    write_csv(FILES / "load" / "historian_export_week.csv",
              ["local_date", "local_hour", "demand_recorded_mw", "vendor_forecast_mw"], rows)
    bad = [r for r in rows if r[2] > 0]
    key["historian"] = {
        "rows": len(rows), "planted": planted, "faulty_rows": 6 + 3 + 1 + 1,
        "mape_true": round(mape(w, "vendor"), 2),
        "mape_recorded_nonzero": round(float(np.mean([abs(r[3] - r[2]) / r[2] for r in bad]) * 100), 2),
    }

    write_csv(FILES / "load" / "error_table.csv", T.ERROR_TABLE[0], T.ERROR_TABLE[1])
    write_csv(FILES / "load" / "cost_table.csv", T.FORECAST_COST_TABLE[0],
              [[a, b.format(**FORECAST_COST)] for a, b in T.FORECAST_COST_TABLE[1]])
    write(FILES / "load" / "vendor_brochure.txt", T.brochure(k))


# ---------------------------------------------------------------- 2. turbine remaining life

def turbine_files(raw: Path, key: dict) -> None:
    f = raw / "cmapss" / "train_FD001.txt"
    if not f.exists():
        z = raw / "cmapss" / "cmapss.zip"
        fetch(CMAPSS, z)
        with zipfile.ZipFile(z) as outer:
            inner = [n for n in outer.namelist() if n.endswith("CMAPSSData.zip")][0]
            with zipfile.ZipFile(io.BytesIO(outer.read(inner))) as zz:
                f.write_bytes(zz.read("train_FD001.txt"))
    a = np.loadtxt(f)
    df = pd.DataFrame(a[:, :26], columns=["unit", "cycle", "o1", "o2", "o3"] + [f"s{i}" for i in range(1, 22)])
    assert df.unit.nunique() == 100
    df["fail"] = df.groupby("unit").cycle.transform("max")
    df["rul"] = df.fail - df.cycle
    sens = ["s2", "s3", "s4", "s7", "s8", "s9", "s11", "s12", "s13", "s14", "s15", "s17", "s20", "s21"]
    sm = df.groupby("unit")[sens].transform(lambda s: s.rolling(10, min_periods=1).mean())
    train = (df.unit <= 60).values
    z = ((sm - sm[train].mean()) / sm[train].std()).values
    x = np.column_stack([np.ones(len(z)), z, z ** 2])
    beta, *_ = np.linalg.lstsq(x[train], np.minimum(df.rul.values, 125)[train], rcond=None)
    df["pred"] = np.clip(x @ beta, 0, 125).round(0)
    test = df[~train]
    late = test[test.rul <= 60]

    rows, leads = [], {}
    for thr in TURBINE["thresholds"]:
        leads[thr] = []
        for u, g in test.groupby("unit"):
            hit = (g.pred <= thr).values
            two = hit & np.roll(hit, 1)
            two[0] = False
            first = int(g.cycle.iloc[int(np.argmax(two))]) if two.any() else None
            fail = int(g.fail.iloc[0])
            rows.append([f"T{int(u) - 60:02d}", thr, fail, "" if first is None else first])
            leads[thr].append(None if first is None else fail - first)
    rows.sort(key=lambda r: (r[1], r[0]))
    write_csv(FILES / "turbines" / "alerts_by_threshold.csv",
              ["turbine", "alert_threshold_cycles", "failure_cycle", "first_alert_cycle"], rows)

    trace = []
    for u in (64, 81, 96):
        g = test[test.unit == u]
        trace += [[f"T{u - 60:02d}", int(r.cycle), int(r.rul), int(r.pred)] for r in g.itertuples()]
    write_csv(FILES / "turbines" / "turbine_traces.csv",
              ["turbine", "cycle", "true_remaining_cycles", "predicted_remaining_cycles"], trace)

    need = TURBINE["needed_lead"]
    per = {}
    for thr, ls in leads.items():
        late_n = sum(1 for v in ls if v is None or v < need)
        timely = [v for v in ls if v is not None and v >= need]
        wasted = sum(v - need for v in timely)
        total = late_n * TURBINE["unplanned"] + len(timely) * TURBINE["planned"] + wasted * TURBINE["per_cycle"]
        known = [v for v in ls if v is not None]
        per[str(thr)] = {"no_alert": sum(1 for v in ls if v is None), "late": late_n, "timely": len(timely),
                         "median_lead": float(np.median(known)), "wasted_cycles": int(wasted),
                         "cost": int(total)}
    best = min(per, key=lambda t: per[t]["cost"])
    half = {t: per[t]["late"] * TURBINE["unplanned"] // 2 + per[t]["timely"] * TURBINE["planned"]
            + per[t]["wasted_cycles"] * TURBINE["per_cycle"] for t in per}
    key["turbines"] = {
        "turbines": 40, "train_engines": 60,
        "rmse_all": round(float(np.sqrt(np.mean((test.pred - np.minimum(test.rul, 125)) ** 2))), 1),
        "rmse_last_60": round(float(np.sqrt(np.mean((late.pred - late.rul) ** 2))), 1),
        "bias_last_60": round(float((late.pred - late.rul).mean()), 1),
        "per_threshold": per, "best_threshold": int(best),
        "vendor_default": TURBINE["vendor_default"],
        "saving_vs_default": per[str(TURBINE["vendor_default"])]["cost"] - per[best]["cost"],
        "best_threshold_if_unplanned_halves": int(min(half, key=half.get)),
        "cost_if_unplanned_halves": {t: int(v) for t, v in half.items()},
    }
    write_csv(FILES / "turbines" / "cost_table.csv", T.TURBINE_COST_TABLE[0],
              [[a, b.format(**TURBINE)] for a, b in T.TURBINE_COST_TABLE[1]])


# ---------------------------------------------------------------- 3. process fault detector

def detector_files(raw: Path, key: dict) -> None:
    def read(name):
        f = raw / "te" / f"{name}.dat"
        fetch(TE.format(name), f)
        return np.loadtxt(f)

    d0 = read("d00")
    if d0.shape[0] == 52:      # the normal training file is stored transposed
        d0 = d0.T
    assert d0.shape == (500, 52), d0.shape
    fit, cal = d0[:300], d0[300:]
    mu, sd = fit.mean(0), fit.std(0, ddof=1)
    _, sv, vt = np.linalg.svd((fit - mu) / sd, full_matrices=False)
    k = 9
    p, lam = vt[:k].T, (sv ** 2 / (len(fit) - 1))[:k]

    def index(x):
        z = (x - mu) / sd
        t = z @ p
        return np.sum(t ** 2 / lam, 1), np.sum((z - t @ p.T) ** 2, 1)

    t2, q = index(cal)
    lim_t2, lim_q = np.quantile(t2, 0.99), np.quantile(q, 0.99)   # the vendor's "1% false alarms"

    rows, log = [], {}
    for i, name in enumerate(TE_RUNS, start=1):
        x = read(f"d{name}_te")
        assert x.shape == (960, 52), x.shape
        t2, q = index(x)
        d = np.round(np.maximum(t2 / lim_t2, q / lim_q), 3)
        a = (d > 1).astype(int)
        b = (a & np.roll(a, 1) & np.roll(a, 2)).astype(int)
        b[:2] = 0
        c = (d > 1.5).astype(int)
        run = f"R{i:02d}"
        normal = name == "00"
        for s in range(960):
            phase = "normal" if normal else ("before" if s < TE_ONSET else "after")
            rows.append([run, s + 1, (s + 1) * 3, phase, f"{d[s]:.3f}", a[s], b[s], c[s]])
        log[run] = {"fault": "none" if normal else int(name)}
        for nm, al in (("A", a), ("B", b), ("C", c)):
            if normal:
                log[run][nm] = {"false_alarms": int(al.sum())}
                continue
            post = al[TE_ONSET:]
            first = int(np.argmax(post)) if post.any() else None
            log[run][nm] = {"false_alarms": int(al[:TE_ONSET].sum()),
                            "delay_min": None if first is None else first * 3,
                            "share_after": round(float(post.mean()), 2)}
    write_csv(FILES / "process" / "detector_runs.csv",
              ["run", "sample", "minute", "phase", "deviation_index", "alarm_A", "alarm_B", "alarm_C"], rows)

    c = DETECTOR
    per = {}
    for nm in "ABC":
        fa = sum(log[r][nm]["false_alarms"] for r in log)
        missed, delay = 0, 0
        for r in log:
            if log[r]["fault"] == "none":
                continue
            e = log[r][nm]
            if e["delay_min"] is None or e["share_after"] < c["min_share"]:
                missed += 1
            else:
                delay += e["delay_min"]
        per[nm] = {"false_alarms": fa, "missed": missed, "detected": 12 - missed, "delay_minutes": delay,
                   "cost": fa * c["false_alarm"] + delay * c["per_minute"] + missed * c["missed"]}
    normal_run = [r for r in log if log[r]["fault"] == "none"][0]
    key["detector"] = {
        "runs": 13, "fault_runs": 12, "normal_run": normal_run, "onset_sample": TE_ONSET + 1,
        "components": k, "log": log, "per_setting": per,
        "best_setting": min(per, key=lambda s: per[s]["cost"]),
        "normal_run_rate_A": round(log[normal_run]["A"]["false_alarms"] / 960 * 100, 1),
        "missed_by_all": sorted(r for r in log if log[r]["fault"] != "none" and all(
            log[r][s]["delay_min"] is None or log[r][s]["share_after"] < c["min_share"] for s in "ABC")),
    }
    write_csv(FILES / "process" / "cost_table.csv", T.DETECTOR_COST_TABLE[0],
              [[a, b.format(**DETECTOR)] for a, b in T.DETECTOR_COST_TABLE[1]])
    write_csv(FILES / "process" / "run_log.csv", T.RUN_LOG[0],
              [[r, "", "", "", ""] for r in sorted(log)])


# ---------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, help="a folder outside the course for the raw public files")
    raw = Path(ap.parse_args().raw).resolve()
    if LABS.parent in raw.parents or raw == LABS.parent:
        raise SystemExit("--raw must be outside the course: the raw files are not committed")
    key: dict = {}
    forecast_files(raw, key)
    turbine_files(raw, key)
    detector_files(raw, key)
    T.write_case(FILES, SOL, key, write, write_csv)
    write(SOL / "key.json", json.dumps(key, ensure_ascii=False, indent=1))
    T.write_solutions(SOL, key, write, write_csv)
    print(json.dumps({k: v for k, v in key.items() if k in ("forecast", "turbines")}, ensure_ascii=False, indent=1)[:6000])
    print(json.dumps(key["detector"]["per_setting"], indent=1), key["detector"]["best_setting"],
          key["detector"]["missed_by_all"], key["detector"]["normal_run_rate_A"])
    print(json.dumps(key["historian"], ensure_ascii=False))


if __name__ == "__main__":
    main()
