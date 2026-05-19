## What & why

<!-- The change, and which part of the pipeline (config / openapi / IR /
     emitter / runtime) it touches. -->

## Conformance

- [ ] `uv run pytest -q` green (37+ tests)
- [ ] `uv run ruff check src tests` clean
- [ ] New behavior covered by a fixture-driven test that failed first
- [ ] No fallback added; errors carry a source location

## Fidelity

<!-- If this changes generated output: how does it compare to the real
     Stainless-generated SDK? -->
