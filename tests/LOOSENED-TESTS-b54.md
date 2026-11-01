# Tests changed or loosened since build 51 (e5e9b4f), checked in build 54

Each was checked by putting the bug back into game.js (a mutation), running the one test, then restoring game.js
(`git diff --quiet game.js` was clean afterwards). Runner used: a throwaway script, not committed. All on a pretend phone
(Chromium touch emulation), never a real phone. Nothing here was restored, because each change below is justified and
still catches its bug. Known limits are listed honestly.

| Test | What changed vs e5e9b4f / b51 | Why | Mutation | Result |
|---|---|---|---|---|
| test_b48 "no rocky floor drawn" | Row brightness spread is now p90-p10 instead of max-min (limit still < 60). The deep check now runs at setLevel(3) instead of 9 | One bubble ring or snow speck on the sampled row gave 58-75 under max-min (seen in a dumped frame). Size 9 is past the band-empty sizes after the b53 size-10 cap | Inside drawWater: draw a striped grey/black rock band from the old seabed down | **FAIL** as it should: spread 109/111/112. On b54 it passes 18/0. **Limit:** a rock band covering less than ~10% of the row width would not be caught (that is what p10/p90 ignores) |
| test_v6 flee / chase | setLevel(3) (size 4) before the check | b53 cap: depth bands empty at HUD 5/7/9/10. At the older default size the fish used for the check fade out, so the check tested nothing | Flee/chase reaction disabled (`if(!shark.air&&dist<sense)` -> `if(false)`) | **FAIL** on 6 checks (runs away, chases, gives up, at both sizes) |
| test_world zone / long swim | setLevel(9) -> setLevel(3) in the two zone checks. Diver lines removed (divers removed in b52) | Same band-empty reason. At size 10 the top and mid bands are empty by design, so a zone bug there would not show | Shallow creatures given the mid band (`bandOf(L===0?1:L)`) | **FAIL** on 3 checks (endless left, endless right, long swim) |
| test_v6 endless score card: feed 40 -> 8 (QA called this test_modes; the change is in test_v6. test_modes changed only for the b52 diver removal) | Endless now feeds 8 instead of 40 before the bigger shark bites (timed still feeds 40) | Feed 40 now reaches the size-10 cap, where the forced biter is in an emptied band and fades, so the round never ends and the check timed out | Endless score card forced taller than the screen | **FAIL**: "endless score card fits landscape" |
| test_b52 limits | Infinite growth checks replaced by MAX_LEVEL 9 + feed stops at size 10. Prey sizes 6/12/17 -> 5/7/8. Band sizes 9/13/17/22 -> 4/6/8/9. Size 401 -> size 10 | Jeremy's size-10 cap (t1365u) rescaled every limit. Full cap tests are in test_b53 | SURFACE.SAIL_LVL 7 -> 8 | **FAIL**: "size 8: sail boats appear" |

test_modes: its changes since e5e9b4f only remove the diver, net and "Caught!" checks (b52 removed divers). Nothing in it was loosened.
