# Mutations that used to pass the whole suite (Skeptic, build 53) and the b54 test that now catches each

Runs on a pretend phone (Chromium touch emulation), never a real phone. Each mutant was applied to game.js, then the test was run, then game.js was restored.
Mutants are the same edits as Skeptic's (`/workspace/skeptic/work/shark9/mut_*`), used only to locate the bug.

| Mutation | Edit | Test that now fails | Result on mutant | Result on b54 |
|---|---|---|---|---|
| (a) perf fix reverted | `busy=onScr>14\|\|SURF>camY&&SURF<camY+H` -> `busy=onScr>14` | tests/test_gaps_b54.py "waterline on screen, no creatures: busy is on" (`__sa.busy`, a new read-only hook) | FAIL (busy False with the waterline on screen) | PASS |
| (b) title head removed | `drawFront` returns at once (and the same holds for Skeptic's `renderFrontShark` returning an empty canvas: the check reads pixels) | test_gaps_b54 "title pose: head-on shark drawn behind the title" (samples the snout area above the words, which must be shark grey) | FAIL 0/165 grey | PASS 154/165 |
| (c) boat (surfer-row) size floor removed | `surfDrawK`: `return k` before the floor | test_gaps_b54 "boat floor holds when boats would otherwise draw small" | FAIL (sail .313 x shark length) | PASS (.550) |

Note on (c): at every reachable size in b54 the floor does not bind (at size 10 a sail boat already draws 1.25x and a cargo ship 4.0x the shark's length),
so in normal play the mutant looks the same. That is why the test makes the shark 4x longer for one call. Removing the floor is only visible if sizes are retuned later.
Note: the floor applies only to sail boats and cargo ships. Surfers (kneel/stand) have no floor by design (they stop spawning below 12 px).
