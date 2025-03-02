# ADR 0001: Layered package with downward-only dependencies

## Status
Accepted.

## Context
A research platform mixing acquisition, parsing, modelling, simulation, serving,
and verification risks becoming a ball of mud where a change to one area breaks
distant code. We need a structure that keeps concerns separable and testable.

## Decision
Organise the package into layers (domain, ingest, parse, features, models,
simulate, registry, serving, coverage, quality, acceptance, verify, pipeline, cli)
where a lower layer never imports a higher one. The dependency graph is acyclic.

## Alternatives
- A flat module layout: simpler initially but import cycles and unclear ownership
  emerge quickly.
- A plugin architecture: more flexible but heavier than this project needs.

## Consequences
Each layer is unit-testable in isolation. New providers slot into `parse` without
touching models. The cost is some boilerplate (`__init__` re-exports) and
discipline to keep imports pointing downward.
