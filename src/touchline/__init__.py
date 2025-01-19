"""Touchline: spatial football intelligence and competition forecasting.

The package is organised in layers that depend only downward:

    domain      typed football objects, units, identifiers, clocks
    ingest      budgeted acquisition, checksums, change detection
    parse       provider-specific readers that emit domain objects
    features    chronological, leakage-aware feature construction
    models      Elo, Dixon-Coles, xG, expected threat, action value, encoders
    simulate    competition rules and Monte Carlo season/tournament draws
    serving     batched CPU inference and batch simulation
    verify      independent replay of decisive quantities

Nothing in a lower layer imports from a higher one.
"""

__version__ = "0.1.0"
