#!/usr/bin/env bash
# stainful demo — paced for screen recording.
#
#   ./demo/demo.sh            # narrated, with pauses (record this)
#   DEMO_SLEEP=0 ./demo/demo.sh   # fast, no pauses (CI / dry-run)
#
# Reuses the REAL public OneBusAway Stainless config we conformance-test
# against (tests/fixtures/onebusaway) — the input is a genuine production
# stainless.yml, not a toy.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
SLEEP="${DEMO_SLEEP-2}"
SPEC=tests/fixtures/onebusaway/openapi.yml
CONFIG=tests/fixtures/onebusaway/stainless-config.yml
OUT=demo/out

say()  { printf '\n\033[1;36m# %s\033[0m\n' "$*"; sleep "$SLEEP"; }
run()  { printf '\033[1;32m$ %s\033[0m\n' "$*"; eval "$*"; sleep "$SLEEP"; }

clear || true
say "stainful — the open-source Stainless. Drop in your existing stainless.yml."

say "1. This is a REAL, public Stainless config (note the schema URL):"
run "head -3 $CONFIG"

say "2. Generate an idiomatic Python SDK — one command, no account, no SaaS:"
rm -rf "$OUT"; mkdir -p "$OUT"
run "uv run stainful generate --spec $SPEC --config $CONFIG --out $OUT"

say "3. What it produced — a real SDK tree (resources, types, vendored runtime):"
run "find $OUT/onebusaway -maxdepth 1 -type d | sort"
run "ls $OUT/onebusaway/resources | head -5"

say "4. The punchline: the client class name is IDENTICAL to the real"
say "   Stainless-generated OneBusAway SDK — existing imports keep working:"
run "grep -m1 'class OnebusawaySDK' $OUT/onebusaway/_client.py"

say "5. It actually works — import it and make a typed call (mocked, offline):"
run "uv run python demo/_use.py"

say "6. And it's faithful to the real Stainless SDK — measured, not claimed:"
run "grep -E '\"(resource_method_recall|method_signature_match)\"' tests/quality/baseline_onebusaway.json"
run "cat tests/quality/baseline_type_parity.json"

say "1.00 resource methods · 0.99 signatures · mypy-clean · 28/29 of"
say "Stainless's OWN test files import unchanged. github.com/stainlu/stainful"
