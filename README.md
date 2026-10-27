# Shark Attack

An offline PWA game, played in **landscape** (tuned on 915x412, 844x390 and 740x360; portrait shows a "Turn your phone sideways" prompt and pauses). It has no ads, no sign-in, no analytics and no outside requests. It only loads its own files.

## How to play
- **Steer:** slide your finger and the shark swims in the direction you slide (it faces that way). The farther you keep sliding, the faster it goes, building up gradually. If you lift your finger it drifts and slows down.
- **Leap:** *Swim down to build speed, then swim up fast to leap!* Leap height depends on speed × run-up distance at speed, up to a cap. Too little just bumps the surface. The power gauge shows your launch power.
- **Surfers** can only be caught in the air. Kneeling surfers are worth 3 and standing surfers 5.
- **Landing on the beat:** if a landing comes within ±80 ms of the music beat, it gets nudged onto the beat for a +1 perfect bonus. The beat follows the gameplay track's eighth-note pulse, `BEAT.CHIPTUNE_BPM` = 80, so a beat every 0.75 s. `PLACEHOLDER_BPM` (100) is only used by the fallback loop.
- **Fish:**
  - Eat smaller fish to fill the growth meter. The shark grows in size steps (max 10) and gets a little faster each step.
  - Fish bigger than you are tinted red and marked "!". If one catches you, it's **Gulp!** and the round ends.
  - Fish the same size as you just bump you.
  - You're safe from fish only while you're in the air.
- **Round:** 60 s (`ROUND_SECONDS`). **This length is UNCONFIRMED.** The round ends with "Time's up!", "Gulp!" or "Caught!". The score screen shows the final score, your best score (`localStorage.sharkAttack_best`), Play again and Home.

## Divers and the ambush
- **Divers** turn up after you catch your **3rd surfer** in a round (`DIVER_TRIGGER_SURFERS`). You get a "Divers!" banner and a warning sound.
  - One more diver comes for every 3 more surfers, with up to 3 at once (`DIVER_MAX`).
  - Divers start at a screen edge or near the surface, away from you, and can't net you for their first 2 s.
  - They swim at 58% of your top speed (`DIVER_SPEED_FRACTION`) and only notice you within 1/3 of the screen height (`DIVER_DETECT_RANGE`). Out of range they wander, and they give up a chase after 3 s.
  - They stay underwater and can't net you mid-leap.
  - When an off-screen diver is close, an orange arrow shows at the screen edge.
- **Net hits:** you're stunned for 1 s (`STUN_MS`) and lose 2 points of growth, and that diver waits 2 s before it can net again.
  - The three icons under the timer show your hits.
  - **The 3rd net hit ends the round with "Caught!".**
- **Ambush:** a big dark shark, 1.6× your current size, may come for you while you're stunned.
  - Hit 1 never brings one. Hit 2 brings one half the time (`AMBUSH_CHANCE` 0.5). Hit 3 always would, but it ends the round first.
  - It comes in from the far edge with a red "!" and a warning sound, and reaches you 1.35 s after the hit (`AMBUSH_ARRIVE_MS`).
  - A hit that brings an ambush stuns you for 2 s (`AMBUSH_STUN_MS`) so the threat is real. Wiggle or drag to break free: every 1/5 screen width of finger travel takes 0.25 s off the stun (`STRUGGLE_SHORTEN_MS`), so about 3 quick wiggles gets you out in time.
  - If you're still stunned when it arrives, it's **Gulp!**. If you got free, it circles off and leaves after 3 s.
  - It can't eat a shark that isn't stunned or is mid-leap. Only one comes at a time, with 6 s between ambushes (`AMBUSH_COOLDOWN_MS`).
  - The first time divers appear, you get a tip: "Nets stun you. Big sharks love a stunned shark!"
- **The 3-hit lose rule and the ambush odds and timing are OUR choice, still to confirm with Jeremy.** Everything above is a constant at the top of `game.js`.

## Shark types (`TYPES_MECHANICAL`)
The **numbers below are our own choice and easy to tune** in the `TYPES` table in `game.js`. Add `?flat` to the URL to make all types play the same.

| type | size | top speed | accel | turn | surfer catch | leap | growth fill |
|---|---|---|---|---|---|---|---|
| Great white | 1.2 | 1.12 | 0.8 | 0.8 | 1.0 | 1.0 | 1.0 |
| Hammerhead | 1.0 | 1.0 | 1.0 | 1.3 | 1.35 | 0.9 | 1.0 |
| Tiger | 0.85 | 1.0 | 1.3 | 1.05 | 1.0 | 1.2 | 1.3 |

## Audio
- **Title music:** Debussy, *La Cathédrale engloutie*, performed by Ivan Ilić, CC BY 3.0. This is an 88 s excerpt. See AUDIO-LICENSES.md and the in-game Credits.
- **Gameplay music: the real chiptune is in.** It's Slopcore Studio's 8-bit "Reflets dans l'eau" v2, arranged from the public-domain 1905 Durand score with no recording used.
  - It ships as `audio/gameplay-chiptune.ogg`: 72 s, mono, 64 kbps, 511 KB.
  - The service worker precaches it, so it works offline.
  - It plays as a gapless WebAudio loop at volume 0.3 (`MUSIC_VOL.game`), which sits under the sound effects.
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
- **Volcanic floor**: at most `MAX_BIG` (3) sharks near you, spawns spread out (`SPREAD_PX`), glowing fish are always food-sized (`GLOW_MAX` .84 of your bite). Chasing starts in the Twilight zone (`CHASE_MIN_D` .3) and deep chasers are a bit slower (`CHASE_DEEP` .7).
- Cache `sharkattack-v7`, `game.js?v=7`.
- Tests: the diver perf check now asserts it is measuring real play (it used to time the game-over screen, which is capped at 30 fps); beat-assist landing tolerance allows 2 frames of measurement slack (`LAND_FRAME_SLACK`); balance_endless runs 30 games per type.
