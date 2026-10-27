# Shark Attack

A family-friendly offline PWA game, built for portrait phones (it's tuned on 412x915, 390x844 and 360x740). It has no ads, no sign-in, no analytics and no outside requests. It only loads its own files.

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
