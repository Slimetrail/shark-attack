# Shark Attack

An offline PWA game, played in **landscape** (tuned on 915x412, 844x390 and 740x360; portrait shows a "Turn your phone sideways" prompt and pauses). It has no ads, no sign-in, no analytics and no outside requests. It only loads its own files.

## How to play
- **Steer:** slide your finger and the shark swims in the direction you slide (it faces that way). The farther you keep sliding, the faster it goes, building up gradually. If you lift your finger it drifts and slows down.
- **Leap:** *Swim down to build speed, then swim up fast to leap!* Leap height depends on speed × run-up distance at speed, up to a cap. Too little just bumps the surface. The power gauge shows your launch power.
- **Surfers** can only be caught in the air, and only through HUD size 8. From size 9 they are too small to eat. Kneeling surfers are worth 15 and standing surfers 20 (build 52).
- **Landing on the beat:** if a landing comes within ±80 ms of the music beat, it gets nudged onto the beat for a +1 perfect bonus. The beat follows the gameplay track's eighth-note pulse, `BEAT.CHIPTUNE_BPM` = 80, so a beat every 0.75 s. `PLACEHOLDER_BPM` (100) is only used by the fallback loop.
- **Fish:**
  - Eat smaller fish to fill the growth meter. The shark keeps growing (no size cap). Top speed stops rising at HUD size 10.
  - Nothing marks which fish are bigger than you (v9): judge size by eye. If a clearly bigger creature touches you, it's **Gulp!** and the round ends.
  - Fish the same size as you just bump you.
  - You're safe from fish only while you're in the air.
- **Round:** 60 s (`ROUND_SECONDS`). **This length is UNCONFIRMED.** The round ends with "Time's up!" or "Gulp!". The score screen shows the final score, your best score (`localStorage.sharkAttack_best`), Play again and Home.

## Build 59 (owner, Nov 5)
- Version/build 59 (`version.json`, cache `sharkattack-v59`, `game.js?v=59`). A small fix on b58.
- **Surfers stop at HUD 9.** b57 stopped surfers when the tiny-sail depth was reached. b58 made them food at every depth, with no size cutoff. From HUD 9 (the same size cargo ships become food, `SURF_OFF`) a surfer is too small: drawn at the tiny-band fraction, not food, and no bump. HUD 8 and below they are still food. Sail, cargo, tanker, and deep-fish stages are unchanged.
- Tests: `tests/test_b59.py`. `tests/test_b58.py` only changes the surfer expectation.

## Build 58 (owner, Nov 5)
- Version/build 58 (`version.json`, cache `sharkattack-v58`, `game.js?v=58`). Built on b57. Not deployed.
- **No size cap.** The b53 stop at HUD size 10 (internal `MAX_LEVEL` 9, HUD text MAX) is reversed. `feed()` keeps leveling, the food bar keeps filling, and the HUD shows the real size (11, 12, 13…). `trueGrow` still clamps its exponent at 2000, and the food-bar exponent clamps at 1400, so the numbers stay finite. Top speed stays capped at the old HUD 10 (`SPEED_LVL_CAP` 9, 1.36× the start). Fish flee and dodge use that same cap, so they do not get faster without limit. Chase cap, `MAX_BIG`, and the spawn caps are unchanged.
- **Prey follows HUD size, not how deep you have been.** HUD size is internal level + 1. Depth still sets the water colours and which craft spawn.
  - HUD 7–9: sail boats are food.
  - HUD 9–12: cargo ships are food.
  - HUD 10+: sail boats are too small (not food, and they do not bump).
  - HUD 12+: edible deep-dark fish spawn in the black zone, about 0.4–0.84× your bite, so there is always food.
  - HUD 13+: cargo ships are too small (not food, no bump).
  - HUD 12 overlaps on purpose: cargo is still food, and the deep fish are already there.
  - Surfers stay food from HUD 5 at any depth.
  - **Oil tankers** are food from HUD 10 until the same retirement as cargo (HUD 13). Before HUD 10 they are not food, even after a deep dive. They still *start spawning* at the sail-shrink depth, and they still spawn in the black zone.
- **Depth illusion.** The shark stays the same size on screen. As it grows, `worldK` keeps shrinking, so fish already in the water get smaller, and new fish spawn at the new size. The depth metre has no floor (the coloured track still fills at the black edge, as in b57).
- Kept: mouth-only bites, fewer chasers, b57 zone colours and the brightness fix, sail/cargo rewards (25 points / growth 3, and 40 / 4).
- Tests: `tests/test_b58.py`. `tests/test_b57.py` still covers rewards, sail shrink, spawns, lighting, and mouth-only kills. Its size-cap check and the depth-edibility bites are updated because those rules changed.

## Build 57 (Jeremy via Eve, Nov 5)
- Version/build 57 (version.json, cache `sharkattack-v57`, `game.js?v=57`). Built on b56 (mouth-only kill, fewer chasers). Not deployed.
- **Slower sail boats and cargo ships.** Same growth curve as before: the bar at internal level `l` needs `3 × 1.25^l`. A surfer is growth 2, about one good fish (food fish are `3 × size/bite`, roughly 1.2–2.5). At the surfer unlock (level 4) that 2 fills 27% of the bar.
  - Sail boat: points 40 → **25**, growth 5 → **3**. At its unlock (level 6, need 11.44) growth 5 filled 44% of the bar; growth 3 fills 26%, the same fraction a surfer is at its own unlock.
  - Cargo ship: points 100 → **40**, growth 10 → **4**. At its unlock (level 8, need 17.88) growth 10 filled 56% of the bar; growth 4 fills 22% (two surfers of growth, not five). One size takes about 5 cargo ships instead of 2.
- **Depth zones are edibility zones.** `depthRaw` 0 is the surface, 1 is the old bed, and there is still no floor (`allowedD` is Infinity).
  - **Light blue, above depth 1.6:** surfers are edible.
  - **At depth 1.6:** a sailboat's drawn length has shrunk to a surfer's length (`SAIL_SHRINK`). Surfers stop being edible. Tiny sailboats stay edible (that cutoff does not apply to them). Oil tankers start spawning here, with their own points 55 and growth 5.
  - **At depth 4.0:** the water is black and cargo ships can no longer be eaten. Deeper than that is the same black, and you can keep swimming.
  - Sail size, the surfer cutoff, tanker spawns and the cargo cutoff follow the deepest depth reached this round, so the rules are still on when you come back up to bite. The picture follows where you are right now.
- **Oil tanker.** Own code-drawn side view (round tanks, a pipe, a small bridge), one baked sprite in the existing surface slots. No new creature cap.
- **Deeper sharks keep growing.** Below the mid layer, sharks (and other deep creatures already bigger than you) scale by `1 + DEPTH_K × (depthRaw − 0.62)` with `DEPTH_K` 0.85. This does not fade out with level and does not stop at depth 1. Edible fish grow at most 1.5× and stay under 0.84× your bite. The old screen-width cap is not a depth ceiling. HUD size still stops at 10 (`MAX_LEVEL` 9, from b53): by then every band above depth 1.6 is too small to eat, so the last size is fed by the deeper, larger fish, and cargo stops once the black depth has been reached. The meter does not keep going past size 10.
- **Light travels further before it goes dark.** Old and new thresholds (depthRaw):

  | what | old | new |
  |---|---|---|
  | vignette starts | 0.34 | 1.6 (surfer / sail edge) |
  | vignette full | 0.86 | 4.0 (cargo / black edge) |
  | gradient reaches black | ~1.08 (old bed + a bit) | 4.0, then the same black continues |
  | `#2eaedb` surface | 0 | 0 |
  | `#1b8dc4` | ~0.065 | 1.28 |
  | `#12649f` | ~0.22 | 2.2 |
  | `#0f4479` | ~0.41 | 2.8 |
  | `#0a2652` | ~0.63 | 3.4 |
  | `#06122e` | ~0.86 | 3.8 |
  | `#03070f` black | ~1.08 | 4.0 |
  | depth-meter bands | 0 / 0.30 / 0.62 / 0.86 of the old bed | 0 / 1.6 / 2.8 / 3.8, meter full at depth 4 |
  | fog alphas | .14, .30 at ~0.32, .47 at ~0.76, .60 at ~1.08 | .12 at 0, .20 at 1.6, .34 at 2.8, .50 at 4.0 |

  The stops step down in brightness (about 150, 140, 120, 105, 87, 61, 35, 18, 7 luma) with no jump bigger than the old mid-water steps. The late-game water lift is unchanged, so size 9–10 stays readable. Rock spires are not drawn in the light-blue zone (they used to be near-black from depth 0.62, which put a dark hole in water that is still bright). From depth 1.6 they fade in softly toward the black edge. Zone edges stayed 1.6 and 4.0.
- Tests: `tests/test_b57.py`. b56 mouth-only kill is still checked in `tests/test_b56.py`.

## Build 56 (Jeremy t1637u, via Eve)
- Version/build 56 (version.json, cache `sharkattack-v56`, `game.js?v=56`).
- **Only the mouth kills.** A bigger creature eats you only when its drawn jaw (`MOUTH`, a small circle at the front of its head, on the side it swims toward) touches your body. Touching its top, belly, side or tail is a harmless bump (a small shove). Your own mouth and body still eat prey the same way.
- **Fewer larger sharks.** Chaser cap (`CHASE`) is 1 from HUD 9 (and at max size 10 / endless), 2 at HUD 5-8 as in b55. Fewer deep sharks overall (`SHARK_P_DEEP` .45 to .38, `MAX_BIG` 3 to 2).
- Eating thresholds unchanged: surfers HUD 5, sail boats HUD 7, cargo ships HUD 9.
- Tests: `tests/test_b56.py`; mutation checks `tools/mut_b56.py`; pace `tools/pace_b56.py`; shots `tools/b56_shots.py`.

## Build 54 (QA fixes on build 53)
- Version/build 54 (version.json, cache `sharkattack-v54`, `game.js?v=54`).
- A quick "Sound on" tap right after "Tap to start" now works (the ghost-click guard only drops the click left over from the start tap itself).
- `tests/balance.py` judges every bot row and prints `BALANCE FAILED` (exit 1) when any check fails; `--selftest` proves a failing run is never reported OK (`tests/test_balance_report.py`). Balance currently FAILS for the hammerhead; game balance is unchanged (Jeremy's decision).
- Look (own art, drawn in code, pre-rendered once): title head-on shark with a smaller crescent mouth, uneven teeth with gaps, matte mottled skin with scars, ragged countershading, triangular dorsal fin with a curved trailing edge. The closed mouth (also used for the head-on frame of the turn) is a small down-turned line with a few tooth tips: no smile. Caustics (light web) baked into the sun-ray sprite under the surface. Surfers get wet-suit sheen, a shadow side, hair strands and foam where the board sits.
- New tests: `tests/test_gaps_b54.py` (perf fix, title head, boat size floor; see `tests/MUTATIONS-b54.md`).
- Tools: `tools/pace.py` (growth pace: time and fish to HUD 4/5/7/10, stretch times; usage in its header) and `tools/perf_sbs.py` (same-script frame rate of several builds side by side).
- Loosened/changed tests since build 51 are explained in `tests/LOOSENED-TESTS-b54.md`.

## Build 52 (Jeremy, via Eve)
- **No divers.** Divers, nets, the stun, the wiggle-free and the ambush shark are gone (Jeremy: "for shark no more divers"). A round ends only with "Time's up!" or "Gulp!". Older notes below that mention them are history.
- **Size cap at 10.** The shark stops growing at HUD size 10 (`MAX_LEVEL` = 9 internally) and the HUD shows MAX SIZE. Each size needs 1.25x more food than the one before (need = 3 × 1.25^(size−1)). Surfers become prey from size 7, sail boats from 8, cargo ships from 9; the depth bands empty at sizes 5/7/9/10 and the deepest band always keeps fish. Top speed rises 4% per size up to the cap (`SPEED_LVL_CAP`).
- **Surface prey chain.** Surfers keep shrinking. From size 13 sail boats join them (`SURFACE.SAIL_LVL`), from size 18 cargo ships (`SURFACE.CARGO_LVL`). Boats can be caught in a leap or bitten from just under the surface. Boats and ships are drawn in code.
- **Bonus points.** Kneeling surfer 15, standing surfer 20, sail boat 40, cargo ship 100 (fish give about 1-4). Each shows a big gold "+N" pop.
- **Fish leave the shallows as you grow.** Depth bands 0-.3, .3-.62, .62-1.0 and 1.0-1.6 of the water empty out at sizes 10, 14, 18 and 23 (`VANISH`); fish there fade out. The water below 1.6 always has fish.
- **Boost** is now 2.2x top speed for 1.2 s, whatever the finger asks, then a 4 s recharge (`BOOST`), with a pale wake behind the tail.
- **3D turn.** When the shark reverses it no longer mirrors in one frame: the body narrows through a head-on view over about 0.6 s, the tail lags, and the belly catches the light (`TURN3D`). Based on general knowledge of how sharks turn, not on footage.
- Tests: `tests/test_b52.py`. Tested on a pretend phone (Chromium touch emulation), not a real phone.

## Shark types (`TYPES_MECHANICAL`)
The **numbers below are our own choice and easy to tune** in the `TYPES` table in `game.js`. Add `?flat` to the URL to make all types play the same.

| type | size | top speed | accel | turn | surfer catch | leap | growth fill |
|---|---|---|---|---|---|---|---|
| Great white | 1.2 | 1.12 | 0.8 | 0.8 | 1.0 | 1.0 | 1.0 |
| Hammerhead | 1.0 | 1.0 | 1.0 | 1.3 | 1.35 | 0.9 | 1.0 |
| Tiger | 0.85 | 1.0 | 1.3 | 1.05 | 1.0 | 1.2 | 1.3 |

## Audio
- **Music (v10):** `audio/intro-scary.ogg` (40 s intro, plays once on the title) and `audio/play-swim-piano.ogg` (90 s; currently a SILENT placeholder until the "Open Water" swim song is approved; beat assist at 120 eighths/min). Both CC0 (own work + VSCO-2 CE piano samples); see AUDIO-LICENSES.md.
  - The service worker precaches both, so they work offline.
  - The swim song plays as a gapless WebAudio loop at volume 0.5 (`MUSIC_VOL.game`), above the 0.3 sound-effects bus. Wave/water sounds were removed in build 25.
  - If the file ever fails to load, an original WebAudio fallback loop plays instead.
  - See AUDIO-LICENSES.md for the licensing.
- **Sound effects** are all synthesized in WebAudio, so there are no sound files: chomp, bubbles (when crossing 70% speed, with a 1.5 s cooldown), gulp, splash, launch and others. Mute is remembered.
- **Nobody has listened to the audio yet.** It was built on a computer with no speakers, so a phone listen is the first real test.

## Debug flags
- `?fps` shows a frame meter.
- `?round=N` sets the round length.
- `?flat` makes all shark types the same.

## Tests
`pip install playwright && playwright install chromium`, then `python3 tests/test_shark.py` (port 8872, override with `SA_PORT`), then `python3 tests/test_divers.py` (port 8873, override with `SA_PORT2`). Both and writes screenshots to /workspace/shark-shots/.

## Notes
Icons: `tools/make_icons.py` made the current icons from the earlier top-down shark art. It calls functions that no longer exist in game.js, so it won't run until it's switched to `render3DShark`. The icons themselves are fine as shipped.

## Polish pass (v4): picked defaults & tuning
Defaults kept (all are constants at the top of `game.js`, exposed in `__sa.DIV`):
60 s round (`?round=N` overrides), 3 net hits = "Caught!", ambush: hit 1 never, hit 2 = 50%, hit 3 ends.

Changed after headless balance runs (`python3 tests/balance.py`, 25 bot rounds per type × 4 modes):
- Divers slower (`DIVER_SPEED_FRACTION` .58→.5) and notice the shark from less far (`DIVER_DETECT_RANGE` 1/3→.28): they were catching too fast.
- After a net hit the diver backs off for 4 s (`DIVER_COOLDOWN_MS` 2000→4000) and the shark blinks, un-nettable, 1.5 s after a stun (new `DIVER_SAFE_AFTER_STUN_MS`): stops chain-hits.
- Smaller net (new `DIVER_NET_REACH` .25; was L·.35+14).
- Shallow angle into the surface now glides instead of bumping (bumps kept killing speed, trapping the shark near divers).
- Tiger shark size .85→.9, growth 1.3→1.5: it scored ~40% below white shark.
- Divers spawn apart; `amb.ate` reset each round (stat bug).

Results: wiggling bot never eaten by the ambush; ambush warning ≥1.35 s; all 3 types reach time-up in most normal rounds (avg score white≈100, hammer≈84, tiger≈79). With divers present the whole round the simple bot is usually "Caught!" — it's a poor dodger; a pure-flee bot took 0 hits.

Other: icons re-rendered with the 3D side-view shark (`tools/make_icons.py` works again, uses `__sa.render3DShark`), cache `sharkattack-v4`, long-press menu/callout disabled. Feel checks: `python3 tests/test_feel.py` (dead spot, speed cap, slow stop, wiggle, pointercancel, background pause/mute, no scroll/zoom). Perf headless: ~0.15 ms JS/frame (0.32 ms at 4× CPU throttle).

Not confirmed on a real phone: actual touch feel/latency on the S26 Ultra, portrait lock (only works when installed/fullscreen), audio resume after backgrounding on Samsung Internet/Chrome, real frame rate at 120 Hz, and whether kids find divers fair. Bot results are not human results.

## Game modes (v5): Timed and Endless
Jeremy asked for "a continue game that does not end until you are eaten and divers are faster the more surfers you eat".
- The pick screen has **⏱ Timed (60 s)** (default) and **♾️ Endless**. The choice is remembered.
- **Endless** has no timer. The HUD shows the time survived. The game ends only when you are eaten ("Gulp!").
- **OUR reading, to confirm with Jeremy:** in Endless, net hits never end the game. They only stun you and cost growth. From the 2nd hit on, every hit has a 50% ambush chance, and a big shark can still eat you. Timed keeps the rule that 3 net hits = "Caught!".
- **Divers speed up in both modes.** Diver speed = shark top speed × `DIVER_SPEED_FRACTION` (.5) × (1 + `DIVER_SPEEDUP_PER_SURFER` (.05) × each surfer past the 3rd). It is capped at `DIVER_SPEED_CAP` (1.05) × shark top speed, which is reached at about 24 surfers. Every `DIVER_SPEEDUP_HINT_EVERY` (3) extra surfers, "Divers are faster!" shows low on screen, away from the "Divers!" banner.
- The Endless score screen shows the score, surfers eaten and time survived. The best score is kept separately for each mode (`sharkAttack_best`, `sharkAttack_best_endless`).
- **Balance** (`python3 tests/balance_endless.py`, the same bot capped at 15 min):
  - A "good" bot (wiggles 4×/s when stunned) lasted a median of about 10–13 min.
  - A "weak" bot (1.5 wiggles/s) lasted about 2–3 min.
  - A real player who wiggles fast can therefore last several minutes.
- Tests: `python3 tests/test_modes.py`. Cache was `sharkattack-v5` (now v6, see below).

## Deep ocean (v6): landscape, depth, volcanic floor

- **Landscape**: manifest `orientation: landscape`; portrait shows "Turn your phone sideways" and pauses play. Pick cards sit in a row; score and credits cards fit 412 px tall screens.
- **Intro**: a face-on shark swims at the screen with its jaws wide open around the title words, then CHOMPS a bite out of them (`renderFrontShark`, `TITLE_BITE_AT`, `TITLE_SWIM`).
- **World** (`WORLD`): 5 screens tall, the camera follows the shark up and down (`CAM_EASE`). A depth meter on the right shows the zone (`ZONES`: Sunlit, Twilight, Midnight, Volcanic) and depth in metres.
- **Scenery**: bright sunlit shallows with light rays, kelp and rocks; darker twilight with jellies; near-black midnight with rock spires and no floor; then a huge volcanic floor with glowing lava cracks, vents and rising embers. A light circle around the shark shrinks as you go deeper. No blood or gore.
- **Creatures** (`CREATURES`): sizes are judged against your shark. Smaller ones run away (`FLEE`), bigger ones chase you (`CHASE_SHALLOW`..`CHASE_DEEP`, always slower than your top speed) but only below `CHASE_MIN_D` of depth, and they give up after `GIVEUP_S` and rest `REST_S`. Sharks get bigger and more common the deeper you go; glowing fish live near the floor. At least `FOOD_SHARE` of spawns are food-sized. Danger creatures get a red ring and "!", and off-screen chasers show red edge arrows.
- **Slower growth** (`GROW`): next size needs `NEED_BASE + NEED_PER_LVL x size` (16, 24, 32...); a creature gives `REL x its size / your bite` (about 1 per food fish), a surfer gives `SURFER` (2). Roughly 3x slower than v5.
- Divers, nets, ambush, Timed and Endless all still work (divers stay in the upper band, `DIVER_BAND`).
- Cache is `sharkattack-v6`. Tests: `python3 tests/test_v6.py` (port 8883). All suites run in landscape now.

## Lighter + fairer deep (v7)

- **Performance**: the tall world backdrop (water, sky, light rays, scenery, volcanic floor) is painted once into an offscreen canvas and blitted each frame; the deep-dark overlay is one drawImage; creatures off-screen are culled; particles, embers and surface waves are reduced while the screen is busy (divers, ambusher, or >14 creatures visible). Orientation is tracked with a media-query listener instead of every frame.
- **Title**: the face-on shark is sized so its whole head stays on screen (`TITLE_TOP_PAD`), jaws still open around the words.
- **Volcanic floor**: at most `MAX_BIG` (2 since b56) sharks near you, spawns spread out (`SPREAD_PX`), glowing fish are always food-sized (`GLOW_MAX` .84 of your bite). Chasing starts in the Twilight zone (`CHASE_MIN_D` .3) and deep chasers are a bit slower (`CHASE_DEEP` .7).
- Cache `sharkattack-v7`, `game.js?v=7`.
- Tests: the diver perf check now asserts it is measuring real play (it used to time the game-over screen, which is capped at 30 fps); beat-assist landing tolerance allows 2 frames of measurement slack (`LAND_FRAME_SLACK`); balance_endless runs 30 games per type.

## Endless ocean + realism (v8)

- **World**: endless sideways (3×3 tile pool, depth-locked spawns, camera snap). Bots and tests are camera-relative.
- **Look**: our own baked reef and deep species (`SPECIES`, `drawSpecies`; groupers with long bodies, big mouths, heavy heads; longer parrotfish, hogfish, wrasse, squirrelfish with pelvic fins and dorsal spines; anglers with a baked lure, octopus, starfish). Reference photos in /workspace/refs were only looked at, never loaded or traced. Great white (countershading), tiger (bars fade as it grows), hammerhead (cephalofoil, eyes at the tips). The red danger ring is gone; danger fish keep the "!". NPC tilt is clamped to ±0.5 rad.
- **Prey** (`CREATURES.FLEE_MIN/MAX`): fleeing fish swim at 0.85–0.92× your top speed and tire after `FLEE_BURST_S` (to `FLEE_TIRED` for `FLEE_TIRED_S`), so a minnow can catch them.
- **Growth** (`GROW`): next size needs 3 + 1 × size (retuned so Timed is winnable). Sim results: `tests/balance_results.md`.
- **Intro**: the shark swims past "SHARK ATTACK", turns, comes back and bites the C; the K is torn off and hangs, the A is knocked crooked — all baked into the one title layer (`tearTitle`). Start works at any time.
- **Quality**: `?rs=0.5..2` render scale, `?fx=0..3` effects, `?dprcap=`, `?adapt=0` to switch off adaptive quality (`ADAPT`: drops fx, then render scale to 0.6, when frames average >21 ms). Grid: `tests/perf_ceiling.py` → `tests/perf_ceiling_results.md` (a desktop proxy, not a phone). Recommended Galaxy S26 Ultra default = the shipped one (DPR cap 2, rs 1, fx 2, adapt on).
- Cache `sharkattack-v10`, `game.js?v=10`. Tests: test_shark, test_divers, test_feel, test_modes, test_v6, test_v8, test_update, test_world, plus balance.py and balance_endless.py. Not tested on a real phone.

## Grow and get eaten (v9)
- **No depth lock.** Every stage can swim anywhere (endless world, depth-locked spawn tables and creature zones are kept). Danger is the limit.
- **Your shark visibly grows**: drawn length ×1.15 per stage (`DRAW.STEP`), capped at ×1.52 (`DRAW.CAP`, reached at stage 4; was 1.75 but the 3× bigger drawn world failed the deep busy-screen perf test), eased in over ~0.4 s with a squash-pulse, a ring and sparks (the "BIGGER!" pop is your own growth, not a size hint about others). The world now shrinks only by the rest of the true growth (`wK = drawK/trueGrow`), so food/danger ratios are unchanged. No camera zoom was needed: at the cap the shark is ~0.3× screen height. Hitboxes use the drawn `shark.L`. Creature notice range also scales with the drawn shark (`SENSE_L`).
- **Bigger creatures eat you.** Any creature (not plankton or starfish) with size ≥ 1.3× your bite (`EAT.RATIO`) eats you when its MOUTH touches you (b56; before b56: on body contact) (red puff, "eaten"). 0.87–1.3× = same size: a silent push. Smaller: food as before (minnow: plankton only). Every eater inside the notice range below 30% depth chases at 0.6–0.7× your top speed and gives up after a while (flee/chase speed rules unchanged).
- **Deeper = bigger.** In the deep layer, non-prey creatures grow up to ×2.2 with depth for small sharks (`DEEP.GROW`, fades out by stage 6; capped at half the screen height). Rare **giants** (sharks/octopus, ~3–10% of deep spawns for a minnow, fading out by stage 6, one at a time; other very big ones max 2 around) are 3.8–5.5× your drawn length, up to 0.6× screen width: about half the screen for a minnow.
- **Removed size/danger indicators** (Jeremy: "the player judges size by eye"): the red "!" over bigger fish/chasers; the red "!" on the incoming ambush shark; red off-screen arrows pointing at chasers; the "Too small!" pop when bumping a same-size/bigger fish; the "Too small!" pop when a too-small shark leaps into a surfer; the "Too small to go deeper" hint (with the depth lock). There never was a diving score bonus; none added. Kept: red death puff, normal score, the control tip "Swim down to build speed…", the orange diver arrows/"Divers!" banner (not size-related), the "boing" surfer bump.
- **Balance**: bots judge size from data (`f.s / bite()`), see `tests/balance_v9.py` (early-diver vs shallow bot) and `tests/balance_results.md`.
- Perf: all creature sprites are cropped + mip-mapped at sprite build time (`warmSprites`); the bigger drawn world otherwise hit lazy crops mid-play.

## v9c (local, build 10; supersedes 647a9a2)
- Jeremy: "no circles around the shark or fish", "shark the same size but everything else bigger", "small fish by its fin".
- Removed: the yellow launch-power ring around the shark, the yellow grow-pop ring, and the white bubble circles on eat/grow (flag RINGS=false).
- Shark drawn size unchanged. Every creature except plankton is drawn LOOK.K=1.25x its true size (food touch radii match the drawing; danger contact stays on true size so balance holds); no non-plankton creature spawns under 0.4x bite. Eat/bump/danger still judged by true size vs bite (0.87 / 1.15, EAT.RATIO unchanged). Deep width caps and giants keep their old on-screen size (perf).
- Size 1 eats any fish clearly smaller than its bite (was plankton only).
- Food is eaten when it touches the mouth OR the drawn body: capsule from mouth (+0.48 L) to tail fin (-0.55 L), radius 0.12 L + 0.3 x drawn fish size. Same-size bump and bigger-eats-you rules unchanged.
- Cache `sharkattack-v10`, `game.js?v=10`. Not tested on a real phone.
