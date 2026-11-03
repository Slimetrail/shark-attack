# b55 mutation check for tests/test_b55.py (pretend phone, Chromium touch emulation; never a real phone)
Each mutant = one edit to the b55 game.js, test_b55 run, game.js restored. Also: test_b55 run against b54 (d94a51b) game: 9 checks FAIL.

| Mutant | Edit | test_b55 result |
|---|---|---|
| vanish fade back | update loop: `if(!f.tiny&&goneAt(f.y))makeTiny(f);` -> `if(goneAt(f.y)){f.fade=VANISH.FADE;continue}` | FAIL (fish fade/vanish, not tiny) |
| spawn switched off back | spawn: `makeTiny(f)` -> `f.off=true;f.retry=1` | FAIL (new spawns in outgrown band switched off) |
| tiny fish edible | `const food=r<0&&!f.tiny` -> `r<0` | FAIL (tiny fish flees as prey) |
| tiny contact | `if(shark.air\|\|f.tiny)continue` -> `if(shark.air)continue` | FAIL (tiny fish bumps the shark) |
| no cap | `CHASE.CAP` 2 -> 99 | FAIL (4 checks) |
| cap not used | `if(P0&&chaseCapped(...))` -> `if(false)` | FAIL (max 16 eaters near) |
| surfers HUD 7 | `SURF_LVL:4` -> 6 | FAIL |
| sail boats HUD 8 | `SAIL_LVL:6` -> 7 | FAIL (2 checks) |
| cargo HUD 10 | `CARGO_LVL:8` -> 9 | FAIL (2 checks) |
| (none, real b55) | | 17 passed, 0 failed |

b55 (7): the tiny-contact check now holds the tiny fish on the shark each step (was ~50% flaky on the mutant); mutant fails 5/5, real passes 3/3.
