# stainful demo

A paced, narrated terminal walkthrough — built to be screen-recorded.

```bash
./demo/demo.sh                # narrated, ~2s pauses between beats (record this)
DEMO_SLEEP=0 ./demo/demo.sh   # fast, no pauses (sanity / CI)
DEMO_SLEEP=4 ./demo/demo.sh   # slower, for a calmer recording
```

It reuses the **real public OneBusAway Stainless config**
(`tests/fixtures/onebusaway/`) — the input is a genuine production
`stainless.yml`, not a toy. Output goes to `demo/out/` (gitignored).

## The 6 beats (what's on screen / what to say)

1. **Real config.** `head` of the `stainless.yml` showing the
   `$schema=https://app.stainlessapi.com/...` line — *"this is an actual
   Stainless config, unmodified."*
2. **One command.** `stainful generate …` — *"no account, no SaaS, runs
   here."*
3. **Real SDK tree.** `resources/`, `types/`, vendored `_core/` — *"a full
   idiomatic SDK, not a transport shim."*
4. **The punchline.** `class OnebusawaySDK` — *"identical class name to the
   real Stainless-generated SDK; existing import lines keep working."*
5. **It works.** Import + a typed call returning `AgencyRetrieveResponse`
   (mocked, offline so it's reliable on camera).
6. **Faithful, measured.** `resource_method_recall 1.00`,
   `method_signature_match 0.99`, `mypy_errors 0` — *"not claimed, gated in
   CI against the real Stainless SDK."*

Closing line on screen: *1.00 resource methods · 0.99 signatures ·
mypy-clean · 28/29 of Stainless's own test files import unchanged.*

## Recording tips

- Any external recorder works (Kap, CleanShot, QuickTime, asciinema). The
  script paces itself with `DEMO_SLEEP`; tune it to your narration speed.
- Terminal ~100 cols, large font, dark theme — the script uses color so the
  `$ command` / `# narration` lines read clearly.
- Total runtime ≈ 30–40 s at `DEMO_SLEEP=2`. Trim beat 6 if you want a
  sub-30s clip; beats 1–5 are the story, beat 6 is the proof.
- Hero shot if you want a single frame: beat 4 (the `OnebusawaySDK` line)
  next to the real `github.com/openai/openai-python` README's
  "generated with Stainless" — same shape, open source.
