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

## v9 (grow + get eaten, no indicators) — bots judge size from data (f.s / bite())
balance.py (Timed, 25 rounds/type): BALANCE OK. Wiggling bot reaches time-up 19/19/22 of 25 (white/hammer/tiger), eaten 6/6/3; early losses ≤2.
Reaches surfer size in 18–21/25, median 18–28 s; catches a surfer in 2–7/25, median 29–49 s (v8: 25–32 s / 41–50 s).
balance_endless.py (30 games/type): ENDLESS BALANCE OK. Good bot: surfer size median 19–31 s; first surfer 16–27/30, median 76–93 s.
balance_v9.py (8 rounds/type; diver = heads below 70% depth from the start, shallow = stays above 22%):
| mode | bot | eaten (of 24) | survived | eaten at depth <.3/.3-.6/>.6 | reached surfer size |
|---|---|---|---|---|---|
| Timed 80 s | early diver | 10 | 14 | 0/6/4 | 1/24 |
| Timed 80 s | shallow | 1 | 23 | 0/0/1 | 23/24 (median 17–27 s) |
| Endless 180 s | early diver | 18 | 6 | 0/5/13 | 7/24 |
| Endless 180 s | shallow | 2 | 22 | 1/0/1 | 22/24 |
A diving minnow is in real danger (≈40% eaten in a Timed round, median ~45 s in) but usually survives a short dive; it grows very slowly down there (plankton only).
