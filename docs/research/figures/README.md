# Research figures

Generated from frozen artifacts by `scripts/generate_figures.py`. Each figure
embeds the run identity it was produced from, so a figure in the report corresponds
to an exact run.

| Figure | Content | Run |
|--------|---------|-----|
| xg_reliability.svg | reliability diagram of the logistic xG (predicted vs observed per bin, point size = bin count) | xg_logistic sample seed=11 |
| title_probabilities.svg | simulated title probabilities for the top teams | forecast DC sample, 5000 draws |

Regenerate:

```bash
python scripts/generate_figures.py
```

These are diagnostic-scale figures on synthetic data, labelled accordingly. The
full-profile figures come from the same generators over acquired real data.
