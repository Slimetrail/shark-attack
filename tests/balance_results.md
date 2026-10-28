# Balance sims (v8 E) — bots, not people

`tests/balance.py` (Timed, 60 s, 25 games/type/bot) → BALANCE OK.
`tests/balance_endless.py` (Endless, 30 games, 900 s cap) → ENDLESS BALANCE OK.

Time to first surfer (bot medians):
- Timed: reaches surfer size in 16–19/25 rounds, median 25–32 s; actually catches a surfer in 4–5/25, median 41–50 s.
- Endless: reaches surfer size in 26–29/30, median 27–37 s; first surfer caught in 15–24/30, median 65–109 s.

Changes: growth NEED_BASE 5→3, NEED_PER_LVL 2→1; prey flee 0.85–0.92× shark max and tire after 1.6 s
(0.55× for 1.1 s). Bots: camera-relative, aim with the mouth (the old bot orbited plankton
inside its turn circle — that was why the white looked stuck at lvl 0), rise when stalled at a depth limit.
The bot's surfer-leap is crude, so real players likely catch surfers sooner; not tested with people.
