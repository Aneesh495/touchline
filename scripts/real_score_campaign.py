"""Real Dixon-Coles score-model campaign across leagues and seasons.

Fits a Dixon-Coles model per (league, season) on real football-data.co.uk results,
checks that it recovers sensible home advantage and that the champion is among its
strongest-attack teams, and evaluates its result-probability log loss against a
base rate on a within-season chronological holdout. Writes a run index.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from touchline.analysis.tables import load_season_matches, reproduce_table
from touchline.ingest.sources import FD_DIVISIONS
from touchline.models.dixon_coles import DixonColesModel
from touchline.parse.football_data_uk import DIV_TO_COMPETITION

CACHE = Path("data/raw/cache")


def _fit_and_eval(div: str, year: int):
    matches = load_season_matches(CACHE, div, year)
    if len(matches) < 200:
        return None
    # chronological holdout: last 20% of the season by date
    matches = [m for m in matches if m.match_date is not None]
    matches.sort(key=lambda m: m.match_date)
    cut = int(0.8 * len(matches))
    train, test = matches[:cut], matches[cut:]
    dc = DixonColesModel().fit(
        [m.home_team for m in train], [m.away_team for m in train],
        [m.fthg for m in train], [m.ftag for m in train], max_iter=120,
    )
    # evaluate result log loss on the holdout (teams seen in training only)
    seen = set(dc.teams)
    base_h = sum(1 for m in train if m.result == "H") / len(train)
    base_d = sum(1 for m in train if m.result == "D") / len(train)
    base_a = 1 - base_h - base_d
    eps = 1e-12
    model_ll, base_ll, n = 0.0, 0.0, 0
    for m in test:
        if m.home_team not in seen or m.away_team not in seen:
            continue
        ph, pd, pa = dc.result_probs(m.home_team, m.away_team)
        model_ll += -np.log(max({"H": ph, "D": pd, "A": pa}[m.result], eps))
        base_ll += -np.log(max({"H": base_h, "D": base_d, "A": base_a}[m.result], eps))
        n += 1
    if n == 0:
        return None
    table = reproduce_table(CACHE, div, year)
    champion = table["champion"] if table else None
    strongest = max(dc.attack, key=dc.attack.get)
    return {
        "competition": DIV_TO_COMPETITION[div],
        "season": f"{year}-{year + 1}",
        "home_adv_log": round(dc.home_adv, 4),
        "rho": round(dc.rho, 4),
        "strongest_attack_team": strongest,
        "champion": champion,
        "champion_is_top3_attack": champion in sorted(dc.attack, key=dc.attack.get, reverse=True)[:3] if champion else None,
        "model_log_loss": round(model_ll / n, 4),
        "base_log_loss": round(base_ll / n, 4),
        "holdout_matches": n,
    }


def main() -> int:
    runs = []
    for year in range(2014, 2023):
        for div in FD_DIVISIONS:
            r = _fit_and_eval(div, year)
            if r:
                runs.append(r)
    beats = sum(1 for r in runs if r["model_log_loss"] < r["base_log_loss"])
    champ_ok = sum(1 for r in runs if r["champion_is_top3_attack"])
    print(f"fitted {len(runs)} real Dixon-Coles season models", flush=True)
    print(f"model beats base rate on holdout: {beats}/{len(runs)}", flush=True)
    print(f"champion among top-3 attack: {champ_ok}/{len(runs)}", flush=True)
    for r in runs[:10]:
        print(f"  {r['competition']} {r['season']}: home_adv={r['home_adv_log']} "
              f"ll={r['model_log_loss']} base={r['base_log_loss']} "
              f"champ={r['champion']} top3={r['champion_is_top3_attack']}", flush=True)
    Path("docs/research/real_score_runs.json").write_text(
        json.dumps({"runs": runs, "beats_base": beats, "champion_top3": champ_ok}, indent=2)
    )
    print(f"\nwrote docs/research/real_score_runs.json ({len(runs)} runs)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
