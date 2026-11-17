# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=2.2"]
# ///
"""Run the reference solution of every lab of USE-SEC-202 on the participants' files.

    uv run labs/solutions/check.py            # all labs
    uv run labs/solutions/check.py 1.3 2.1    # some labs

Every number is recomputed from labs/files/ (the files a participant opens), the way the lab page
tells a participant to compute it, and compared with key.json, which the file generator wrote.
The text labs (1.1, 2.2, 2.3) are checked mechanically: levels and evidence against the guide,
the reference argument against the registers, the six planted faults in the draft.
No lab of this course calls a language model. Nothing is written to disk.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
LABS = HERE.parent
FILES = LABS / "files"
KEY = json.loads((HERE / "key.json").read_text(encoding="utf-8"))
LABS_RUN: dict[str, callable] = {}

LEVEL_AR = {"advisory": "استشاري", "supervisory": "إشرافي", "closed": "حلقة مغلقة"}
AR_LEVEL = {v: k for k, v in LEVEL_AR.items()}


def lab(lab_id):
    def wrap(fn):
        LABS_RUN[lab_id] = fn
        return fn
    return wrap


def rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def same(label: str, got, want, tol: float = 0.0) -> None:
    if isinstance(want, (int, float)) and not isinstance(want, bool):
        ok = abs(float(got) - float(want)) <= tol
    else:
        ok = got == want
    if not ok:
        raise AssertionError(f"{label}: computed {got!r}, key {want!r}")


def mape(err: pd.Series, actual: pd.Series) -> float:
    return float((err.abs() / actual).mean() * 100)


# ---------------------------------------------------------------- Day 1

def guide_evidence() -> dict[str, str]:
    """The evidence line of each level, as written in control_levels_guide.txt."""
    lines = text(FILES / "control_levels_guide.txt").splitlines()
    out, current = {}, None
    for line in lines:
        s = line.strip()
        if s in AR_LEVEL:
            current = AR_LEVEL[s]
        elif current and s.startswith("الأدلة:"):
            out[current] = s.removeprefix("الأدلة:").strip().rstrip(".")
            current = None
    assert set(out) == set(LEVEL_AR), out
    return out


@lab("1.1")
def lab_1_1():
    apps = {r["الرمز"]: r for r in rows(FILES / "applications.csv")}
    sol = {r["الرمز"]: r for r in rows(HERE / "applications.csv")}
    assert len(apps) == 10 and set(apps) == set(sol), "ten applications in both files"
    assert all(not r["مستوى التحكم"] for r in apps.values()), "the participants' file leaves the level blank"
    ev = guide_evidence()
    levels = {}
    for code, r in sol.items():
        level = AR_LEVEL[r["مستوى التحكم"]]
        levels[code] = level
        same(f"{code} level", level, KEY["applications"]["levels"][code])
        evidence = r["الأدلة المطلوبة قبل الاستعمال"]
        # the evidence line of the level, as the guide writes it (a level inherits the one below)
        same(f"{code} evidence", evidence, ev[level])
    counts = {k: list(levels.values()).count(k) for k in LEVEL_AR}
    same("counts", counts, KEY["applications"]["counts"])
    # the two pairs the session teaches: one model, two levels
    assert levels["U03"] != levels["U04"] and levels["U08"] != levels["U09"]
    # what decides the level is in the description: an automatic write means not advisory
    for code in ("U04", "U06", "U09"):
        assert re.search("تلقائي|دون موافقة|دون انتظار", apps[code]["ماذا يحدث لمخرج النموذج"]), code
    print(f"  levels: {counts['advisory']} advisory, {counts['supervisory']} supervisory, {counts['closed']} closed-loop")
    print(f"  pass mark of the outcome: {KEY['applications']['pass_rows']} correct rows of 10")


def load_2024() -> pd.DataFrame:
    df = pd.read_csv(FILES / "load" / "load_hourly.csv", encoding="utf-8-sig")
    assert len(df) == 17544, len(df)
    # the baselines are issued 24 hours ahead, like the vendor's forecast
    df["persistence"] = df.demand_mw.shift(24)
    df["seasonal"] = df.demand_mw.shift(168)
    t = df[df.year == 2024].copy()
    assert t.vendor_forecast_mw.notna().all() and df[df.year == 2023].vendor_forecast_mw.isna().all()
    t["vendor"] = t.vendor_forecast_mw
    t["operator"] = t.operator_forecast_mw
    return t


@lab("1.2")
def lab_1_2():
    t = load_2024()
    k = KEY["forecast"]
    same("hours of 2024", len(t), k["hours"])
    res = {}
    for name in ("vendor", "persistence", "seasonal", "operator"):
        err = t[name] - t.demand_mw
        res[name] = (round(float(err.abs().mean())), round(mape(err, t.demand_mw), 2))
        same(f"{name} MAE", res[name][0], k[name]["mae"], 1)
        same(f"{name} MAPE", res[name][1], k[name]["mape"], 0.01)
        print(f"  {name:<12} MAE {res[name][0]:>6,} MW   MAPE {res[name][1]:5.2f}%")
    # improvement on a baseline: 1 - MAE of the forecast / MAE of the baseline
    skill_p = round((1 - res["vendor"][0] / res["persistence"][0]) * 100, 1)
    skill_s = round((1 - res["vendor"][0] / res["seasonal"][0]) * 100, 1)
    same("skill on persistence", skill_p, k["skill_vs_persistence"], 0.15)
    same("skill on seasonal naive", skill_s, k["skill_vs_seasonal"], 0.15)
    brochure = text(FILES / "load" / "vendor_brochure.txt")
    assert "4.1%" in brochure and "2023" in brochure, "the brochure's in-sample claim"
    assert res["vendor"][1] > 4.1, "on 2024 the vendor's error is above its brochure figure"
    print(f"  skill: {skill_p}% on persistence, {skill_s}% on seasonal naive; brochure claims 4.1% on 2023, 2024 gives {res['vendor'][1]}%")


@lab("1.3")
def lab_1_3():
    k = KEY["forecast"]
    e = pd.read_csv(FILES / "start" / "forecast_errors_2024.csv", encoding="utf-8-sig")
    t = load_2024()
    # the start file agrees with what lab 1.2 builds
    for name, col in (("vendor", "vendor_mw"), ("persistence", "persistence_mw"), ("seasonal", "seasonal_mw")):
        assert (e[col].values == t[name].values).all(), f"start file: {col}"
    names = {"vendor": "vendor_error_mw", "persistence": "persistence_error_mw",
             "seasonal": "seasonal_error_mw", "operator": "operator_error_mw"}
    for name, col in names.items():
        for m in range(1, 13):
            sub = e[e.month == m]
            same(f"{name} month {m}", round(mape(sub[col], sub.demand_mw), 2), k["by_month"][str(m)][name], 0.01)
    loses = [m for m in range(1, 13) if k["by_month"][str(m)]["vendor"] > k["by_month"][str(m)]["persistence"]]
    same("months the vendor loses", loses, k["months_vendor_loses_to_persistence"])
    peak = e[e.peak_hour == 1]
    same("peak hours", len(peak), k["peak_hours"])
    same("peak floor", int(peak.demand_mw.min()), k["peak_floor_mw"])
    for name, col in names.items():
        same(f"{name} peak MAPE", round(mape(peak[col], peak.demand_mw), 2), k[name]["peak_mape"], 0.01)
        same(f"{name} peak bias", round(float(peak[col].mean())), k[name]["peak_bias"], 1)
        # an error below zero is a forecast under the load: 4 units per MWh; above: 1 unit
        under = (-e[col].clip(upper=0)).sum()
        over = e[col].clip(lower=0).sum()
        cost = round((4 * under + over) / 1e6, 1)
        same(f"{name} cost", cost, k[name]["cost_units_m"], 0.05)
        print(f"  {name:<12} peak MAPE {k[name]['peak_mape']:5.2f}%  peak bias {k[name]['peak_bias']:>6,} MW  cost {cost} M units")
    same("cost vs persistence", round((k["vendor"]["cost_units_m"] / k["persistence"]["cost_units_m"] - 1) * 100, 1),
         k["cost_vs_persistence"], 0.15)

    # the historian week: four recording faults
    h = pd.read_csv(FILES / "load" / "historian_export_week.csv", encoding="utf-8-sig")
    same("historian rows", len(h), KEY["historian"]["rows"])
    dup = h[h.duplicated(["local_date", "local_hour"], keep="first")]
    zeros = h[h.demand_recorded_mw == 0]
    run = (h.demand_recorded_mw != h.demand_recorded_mw.shift()).cumsum()
    # a frozen value repeats the last good reading: the fault starts at the second row of the run
    stuck = h[(h.groupby(run).demand_recorded_mw.transform("size") >= 3) & (h.demand_recorded_mw > 0)
              & (h.groupby(run).cumcount() > 0)]
    ratio = h.demand_recorded_mw / h.vendor_forecast_mw
    spike = h[ratio > 3]
    found = {"stuck": stuck, "zeros": zeros, "spike": spike, "duplicate": dup}
    for p in KEY["historian"]["planted"]:
        f = found[p["fault"]]
        first = f.iloc[0]
        same(f"{p['fault']} start", [first.local_date, int(first.local_hour)], p["from"])
        same(f"{p['fault']} hours", len(f), p["hours"])
    # the vendor's error on that week, on the true load and on what the historian recorded
    week = t[(t.local_date >= "2024-08-05") & (t.local_date <= "2024-08-11")]
    same("true-load MAPE", round(mape(week.vendor - week.demand_mw, week.demand_mw), 2), KEY["historian"]["mape_true"], 0.01)
    rec = h[h.demand_recorded_mw > 0]  # what a quick look does: drop the zeros only
    same("recorded MAPE", round(mape(rec.vendor_forecast_mw - rec.demand_recorded_mw, rec.demand_recorded_mw), 2),
         KEY["historian"]["mape_recorded_nonzero"], 0.01)
    print(f"  worst month {k['worst_month']}; vendor loses to persistence in months {loses}")
    print(f"  historian: 4 faults found; vendor MAPE {KEY['historian']['mape_true']}% on true load, "
          f"{KEY['historian']['mape_recorded_nonzero']}% on recorded values")


def price_turbines(a: pd.DataFrame, unplanned: int) -> dict:
    c = KEY["turbines"]
    out = {}
    for th, g in a.groupby("alert_threshold_cycles"):
        lead = g.failure_cycle - g.first_alert_cycle
        no_alert = int(g.first_alert_cycle.isna().sum())
        late = int(((lead < 15) | lead.isna()).sum())
        timely = len(g) - late
        wasted = int((lead[lead >= 15] - 15).sum())
        cost = late * unplanned + timely * 400_000 + wasted * 6_000
        out[int(th)] = {"no_alert": no_alert, "late": late, "timely": timely,
                        "median_lead": float(lead.median()), "wasted_cycles": wasted, "cost": int(cost)}
    assert len(out) == len(c["per_threshold"])
    return out


@lab("1.4")
def lab_1_4():
    a = pd.read_csv(FILES / "turbines" / "alerts_by_threshold.csv", encoding="utf-8-sig")
    k = KEY["turbines"]
    same("turbines", a.turbine.nunique(), k["turbines"])
    costs = {r["البند"]: r["القيمة"] for r in rows(FILES / "turbines" / "cost_table.csv")}
    assert any("1800000" in v for v in costs.values()) and any("6000" in v for v in costs.values())
    res = price_turbines(a, 1_800_000)
    print("  threshold  late  timely  median lead  wasted   cost (SAR)")
    for th, r in res.items():
        kk = k["per_threshold"][str(th)]
        for f in ("no_alert", "late", "timely", "wasted_cycles", "cost"):
            same(f"threshold {th} {f}", r[f], kk[f])
        same(f"threshold {th} median lead", r["median_lead"], kk["median_lead"], 0.01)
        print(f"  {th:>9} {r['late']:>5} {r['timely']:>7} {r['median_lead']:>12} {r['wasted_cycles']:>7} {r['cost']:>12,}")
    best = min(res, key=lambda t: res[t]["cost"])
    same("best threshold", best, k["best_threshold"])
    same("saving against the vendor's 20", res[20]["cost"] - res[best]["cost"], k["saving_vs_default"])
    half = price_turbines(a, 900_000)
    best_half = min(half, key=lambda t: half[t]["cost"])
    same("best threshold, unplanned halved", best_half, k["best_threshold_if_unplanned_halves"])
    for th, r in half.items():
        same(f"halved {th}", r["cost"], k["cost_if_unplanned_halves"][str(th)])
    start = rows(FILES / "start" / "cost_sheet_after_1_4.csv")[0]
    assert str(res[best]["cost"]) in start["التكلفة (ريال)"], "the start file of 2.1 carries this row"
    print(f"  cheapest: {best} cycles; the vendor's 20 costs {k['saving_vs_default']:,} SAR more; "
          f"with the unplanned stop at half price: {best_half}")


# ---------------------------------------------------------------- Day 2

def log_detector(d: pd.DataFrame) -> dict:
    onset = KEY["detector"]["onset_sample"]
    out = {}
    for run, g in d.groupby("run"):
        g = g.sort_values("sample")
        normal = run == KEY["detector"]["normal_run"]
        entry = {}
        for s in "ABC":
            col = f"alarm_{s}"
            if normal:
                entry[s] = {"false_alarms": int(g[col].sum())}
                continue
            before, after = g[g["sample"] < onset], g[g["sample"] >= onset]
            first = after[after[col] == 1]["sample"].min()
            entry[s] = {"false_alarms": int(before[col].sum()),
                        "delay_min": int((first - onset) * 3),
                        "share_after": round(float(after[col].mean()), 2)}
        out[run] = entry
    return out


def price_detector(log: dict, false_alarm: int) -> dict:
    out = {}
    for s in "ABC":
        fa = sum(v[s]["false_alarms"] for v in log.values())
        det = [v[s] for r, v in log.items() if "share_after" in v[s] and v[s]["share_after"] >= 0.5]
        missed = sum(1 for v in log.values() if "share_after" in v[s] and v[s]["share_after"] < 0.5)
        delay = sum(x["delay_min"] for x in det)
        out[s] = {"false_alarms": fa, "detected": len(det), "missed": missed, "delay_minutes": delay,
                  "cost": fa * false_alarm + delay * 2_000 + missed * 400_000}
    return out


@lab("2.1")
def lab_2_1():
    d = pd.read_csv(FILES / "process" / "detector_runs.csv", encoding="utf-8-sig")
    k = KEY["detector"]
    same("runs", d.run.nunique(), k["runs"])
    assert (d.minute == d["sample"] * 3).all(), "one sample every 3 minutes"
    log = log_detector(d)
    for run, v in log.items():
        for s in "ABC":
            for f, val in v[s].items():
                same(f"{run} {s} {f}", val, k["log"][run][s][f], 0.001)
    cost = price_detector(log, 3_000)
    for s in "ABC":
        for f, val in cost[s].items():
            same(f"setting {s} {f}", val, k["per_setting"][s][f])
        print(f"  setting {s}: {cost[s]['false_alarms']:>3} false alarms, {cost[s]['detected']} detected, "
              f"{cost[s]['missed']} missed, {cost[s]['delay_minutes']} min delay, {cost[s]['cost']:,} SAR")
    best = min(cost, key=lambda s: cost[s]["cost"])
    same("best setting", best, k["best_setting"])
    missed_all = sorted(r for r, v in log.items() if all(v[s].get("share_after", 1) < 0.5 for s in "ABC"))
    same("missed by every setting", missed_all, k["missed_by_all"])
    rate = round(log["R04"]["A"]["false_alarms"] / len(d[d.run == "R04"]) * 100, 1)
    same("false-alarm rate of A on the normal run", rate, k["normal_run_rate_A"])
    cheap = price_detector(log, 500)
    best_cheap = min(cheap, key=lambda s: cheap[s]["cost"])
    assert best_cheap == "A", best_cheap
    sheet = rows(HERE / "cost_of_errors_sheet.csv")
    assert str(cost[best]["cost"]) in sheet[1]["التكلفة (ريال)"]
    print(f"  cheapest: {best}; missed by every setting: {', '.join(missed_all)}; "
          f"setting A alarms on {rate}% of normal samples")
    print(f"  stretch, false alarm at 500 SAR: " + ", ".join(f"{s} {cheap[s]['cost']:,}" for s in "ABC") + f" -> {best_cheap}")


def register_codes(name: str) -> set[str]:
    return {r["الرمز"] for r in rows(FILES / "safety" / name)}


@lab("2.2")
def lab_2_2():
    hazards = register_codes("hazard_log.csv")
    evidence = register_codes("evidence_register.csv")
    checklist = rows(FILES / "safety" / "checklist.csv")
    s = KEY["safety"]
    same("hazards", len(hazards), s["hazards"])
    same("evidence items", len(evidence), s["evidence_items"])
    same("checklist items", len(checklist), s["checklist_items"])
    arg = text(HERE / "argument_reference.txt")
    lines = {m.group(1): m.group(2) for m in re.finditer(r"^([GCSX]\d+)\s+(.*)$", arg, re.M)}
    for code in ["G1", "C1", "C2", "S1"] + [f"G{i}" for i in range(2, 11)]:
        assert code in lines, f"the reference argument has {code}"
    cited = set(re.findall(r"\bE\d+\b", arg))
    assert cited <= evidence, f"cited evidence not in the register: {cited - evidence}"
    covered = set(re.findall(r"\(H(\d)\)", arg))
    same("hazards covered", {f"H{c}" for c in covered}, hazards)
    gaps = set(re.findall(r"\bX\d+\b", arg))
    assert len(gaps) >= 6, gaps
    # the envelope is limited to what E3 covers
    assert all(w in lines["C1"] for w in ("مارس", "سبتمبر", "الثلاثة", "مستقر"))
    assert "مدير سلامة العمليات" in lines["G8"] or "مشرف" in lines["G8"], "an override holder by job"
    assert "المرحلة الثانية" in lines["G10"], "phase two reopens the argument"
    # E4 proves the protection layers, never the quality of advice: it is cited only on H1
    assert [g for g, l in lines.items() if "E4" in l] == ["G2"]
    print(f"  reference argument: 13 lines, {len(covered)} of {len(hazards)} hazards, evidence {sorted(cited)}, {len(gaps)} written gaps")


@lab("2.3")
def lab_2_3():
    draft = text(FILES / "start" / "argument_ai_draft.txt")
    lines = {m.group(1): m.group(2) for m in re.finditer(r"^([GCS]\d+)\s+(.*)$", draft, re.M)}
    evidence = register_codes("evidence_register.csv")
    s = KEY["safety"]
    faults = {
        "F1": "G8" in lines and not re.search("مشرف|مدير|مسؤول", lines["G8"]),
        "F2": "مدار السنة" in lines["C1"] and "كل الفصول" in lines["G6"],
        "F3": bool(set(re.findall(r"\bE\d+\b", draft)) - evidence),
        "F4": "G9" not in lines,
        "F5": "المرحلة الثانية" in lines["C2"] and "استشارية" in lines["C2"],
        "F6": not re.search(r"\b[EX]\d+\b", lines["G7"]),
    }
    missing = [f for f, ok in faults.items() if not ok]
    assert not missing, f"planted faults not found: {missing}"
    same("faults", sorted(faults), s["draft_faults"])
    same("the evidence that does not exist", sorted(set(re.findall(r"\bE\d+\b", draft)) - evidence), [s["missing_evidence"]])
    same("draft total", sum(s["draft_scores"].values()), s["draft_total"])
    assert "لم يكتبها نموذج" in draft, "the draft says it was written by hand"
    print(f"  six planted faults found: {', '.join(sorted(faults))}; the draft scores {s['draft_total']} of {s['max_score']}")


TIER = {"economic": (1, 1, 2), "production": (1, 2, 3), "safety": (2, 3, 3)}
CONSEQ = {"مالية فقط": "economic", "توقف إنتاج": "production", "سلامة أو بيئة": "safety"}


def value_score(v: float) -> int:
    return 1 if v < 1 else 2 if v < 5 else 3 if v < 15 else 4 if v < 40 else 5


@lab("2.4")
def lab_2_4():
    cases = {r["الرمز"]: r for r in rows(FILES / "map" / "use_cases.csv")}
    ref = {r["الرمز"]: r for r in rows(HERE / "map_reference.csv")}
    m = KEY["map"]
    assert len(cases) == 12 and set(ref) == set(cases)
    yes = lambda s: s.strip() == "نعم"
    for code, c in cases.items():
        k = m["scores"][code]
        value = float(c["القيمة السنوية على خط الأساس المقيس (مليون ريال)"])
        mwh = float(c["طاقة الذكاء الاصطناعي (ميغاواط ساعة في السنة)"])
        energy = round(mwh * m["price_per_mwh"] / 1e6, 2)
        net = round(value - energy, 2)
        events = c["الأحداث الموسومة"]
        crit = [int(float(c["سنوات السجل التاريخي"]) >= 2),
                int(events == "لا تحتاج" or float(events) >= 30),
                int(yes(c["القراءات محققة الجودة"])),
                int(yes(c["خط أساس مقيس"])),
                int(yes(c["مشاركة البيانات مغطاة"]))]
        readiness = max(1, sum(crit))
        level = AR_LEVEL[ref[code]["مستوى التحكم"]]
        tier = TIER[CONSEQ[c["أسوأ عاقبة معقولة"]]][["advisory", "supervisory", "closed"].index(level)]
        for f, val in (("energy_cost_m", energy), ("net_value", net), ("value_score", value_score(net)),
                       ("value_score_before_energy", value_score(value)), ("criteria", crit),
                       ("readiness", readiness), ("level", level), ("tier", tier)):
            same(f"{code} {f}", val, k[f], 0.001 if isinstance(val, float) else 0)
        r = ref[code]
        same(f"{code} reference net", float(r["القيمة الصافية (مليون ريال)"]), net, 0.001)
        same(f"{code} reference readiness", int(r["جاهزية البيانات"]), readiness)
        same(f"{code} reference tier", int(r["مستوى المخاطر"].split()[0]), tier)
        needs = level != "advisory"
        same(f"{code} needs an override holder", needs, k["needs_authority"])
        if needs:
            assert r["صاحب صلاحية التجاوز"] and not r["صاحب صلاحية التجاوز"].startswith("لا يلزم"), code
    cand = sorted(c for c, k in m["scores"].items() if k["readiness"] >= 4 and k["tier"] <= 2)
    same("pilot candidates", cand, m["candidates"])
    pilot = max(cand, key=lambda c: m["scores"][c]["net_value"])
    same("pilot", pilot, m["pilot"])
    changed = sorted(c for c, k in m["scores"].items() if k["value_score"] != k["value_score_before_energy"])
    same("energy changes the score", changed, m["energy_changes_score"])
    same("need an override holder", sorted(c for c, k in m["scores"].items() if k["needs_authority"]), m["need_authority"])
    start = {r["الرمز"]: r for r in rows(FILES / "start" / "map_four_scored.csv")}
    same("the four cases of the lab", sorted(start), sorted(m["lab_cases"]))
    for code, r in start.items():
        same(f"start {code}", r["القيمة الصافية (مليون ريال)"], ref[code]["القيمة الصافية (مليون ريال)"])
    print("  code  net value  value  readiness  level        tier")
    for code in sorted(m["scores"]):
        k = m["scores"][code]
        print(f"  {code}  {k['net_value']:>9}  {k['value_score']:>5}  {k['readiness']:>9}  {k['level']:<11}  {k['tier']}")
    print(f"  candidates {', '.join(cand)}; pilot {pilot}; energy changes the score of {', '.join(changed)}")


def main(argv):
    wanted = argv or list(LABS_RUN)
    failed = 0
    for lab_id in wanted:
        if lab_id not in LABS_RUN:
            print(f"no lab {lab_id}; labs: {', '.join(LABS_RUN)}")
            return 2
        print(f"Lab {lab_id}")
        try:
            LABS_RUN[lab_id]()
            print("  PASS")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {e}")
    print(f"{len(wanted) - failed} of {len(wanted)} labs pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
