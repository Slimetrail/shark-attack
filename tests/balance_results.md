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

## v9 (grow + get eaten, no indicators) — bots judge size from data (f.s / bite()); numbers at the final v9 code
balance.py (Timed, 25 rounds/type): BALANCE OK. Wiggling bot reaches time-up 20/19/20 of 25 (white/hammer/tiger), eaten 5/6/5; early losses 1 each.
Reaches surfer size in 19–22/25, median 19–23 s; catches a surfer in 3–16/25, median 35–44 s (v8: 25–32 s / 41–50 s).
balance_endless.py (30 games/type): ENDLESS BALANCE OK. Good bot: surfer size median 17–27 s; first surfer 15–24/30, median 95–113 s (v8 65–109 s); 12–14/30 eaten within 15 min.
balance_v9.py (8 rounds/type; diver = heads below 70% depth from the start, shallow = stays above 22%):
| mode | bot | eaten (of 24) | survived | eaten at depth <.3/.3-.6/>.6 | reached surfer size |
|---|---|---|---|---|---|
| Timed 80 s | early diver | 9 | 15 | 0/2/7 | 1/24 |
| Timed 80 s | shallow | 3 | 21 | 0/1/2 | 23/24 (median 19–34 s) |
| Endless 180 s | early diver | 22 | 2 | 1/7/14 | 4/24 |
| Endless 180 s | shallow | 3 | 21 | 2/0/1 | 21/24 |
A diving minnow is in real danger (~38% eaten in a Timed round, median ~30 s in; staying deep for 3 min is almost always fatal) but a short dive is usually survivable. It grows very slowly down there (plankton only).
