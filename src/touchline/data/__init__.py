"""Sample data for the bundled demo.

The committed sample is clearly synthetic. It is generated from a fixed seed by a
documented process so the demo runs offline and deterministically, and it is never
presented as real match data. Real data is acquired through the ingest layer from
permitted providers; see docs/DATASETS.md.
"""

from touchline.data.sample import (
    SampleLeague,
    generate_sample_league,
    generate_sample_shots,
)

__all__ = ["SampleLeague", "generate_sample_league", "generate_sample_shots"]
