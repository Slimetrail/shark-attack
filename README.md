# Shark Attack

A family-friendly offline PWA game, built for portrait phones (it's tuned on 412x915, 390x844 and 360x740). It has no ads, no sign-in, no analytics and no outside requests. It only loads its own files.

## How to play
- **Steer:** slide your finger and the shark swims in the direction you slide (it faces that way). The farther you keep sliding, the faster it goes, building up gradually. If you lift your finger it drifts and slows down.
- **Leap:** *Swim down to build speed, then swim up fast to leap!* Leap height depends on speed × run-up distance at speed, up to a cap. Too little just bumps the surface. The power gauge shows your launch power.
- **Surfers** can only be caught in the air. Kneeling surfers are worth 3 and standing surfers 5.
- **Landing on the beat:** if a landing comes within ±80 ms of the music beat, it gets nudged onto the beat for a +1 perfect bonus. Set the tempo with `BEAT.CHIPTUNE_BPM` / `PLACEHOLDER_BPM` (100).
- **Fish:**
  - Eat smaller fish to fill the growth meter. The shark grows in size steps (max 10) and gets a little faster each step.
  - Fish bigger than you are tinted red and marked "!". If one catches you, it's **Gulp!** and the round ends.
  - Fish the same size as you just bump you.
  - You're safe from fish only while you're in the air.
- **Round:** 60 s (`ROUND_SECONDS`). **This length is UNCONFIRMED.** The round ends either with "Time's up!" or "Gulp!". The score screen shows the final score, your best score (`localStorage.sharkAttack_best`), Play again and Home.

## Shark types (`TYPES_MECHANICAL`)
The **numbers below are our own choice and easy to tune** in the `TYPES` table in `game.js`. Add `?flat` to the URL to make all types play the same.

| type | size | top speed | accel | turn | surfer catch | leap | growth fill |
|---|---|---|---|---|---|---|---|
| Great white | 1.2 | 1.12 | 0.8 | 0.8 | 1.0 | 1.0 | 1.0 |
| Hammerhead | 1.0 | 1.0 | 1.0 | 1.3 | 1.35 | 0.9 | 1.0 |
| Tiger | 0.85 | 1.0 | 1.3 | 1.05 | 1.0 | 1.2 | 1.3 |

## Audio
- **Title music:** Debussy, *La Cathédrale engloutie*, performed by Ivan Ilić, CC BY 3.0. This is an 88 s excerpt. See AUDIO-LICENSES.md and the in-game Credits.
- **Gameplay music:** this will be Slopcore Studio's chiptune "Reflets dans l'eau", but it **hasn't been delivered yet**. Until then an original WebAudio placeholder loop plays.
  - To swap it in, drop the file at `audio/gameplay-chiptune.ogg`, set `BEAT.CHIPTUNE_BPM`, and bump `VER` in sw.js and `?v=` in index.html.
  - The game checks for the file with a HEAD request, so a **404 for it in the console is expected** until it exists.
- **Sound effects** are all synthesized in WebAudio, so there are no sound files: chomp, bubbles (when crossing 70% speed, with a 1.5 s cooldown), gulp, splash, launch and others. Mute is remembered.
- **Nobody has listened to the audio yet.** It was built on a computer with no speakers, so a phone listen is the first real test.

## Debug flags
- `?fps` shows a frame meter.
- `?round=N` sets the round length.
- `?flat` makes all shark types the same.

## Tests
`pip install playwright && playwright install chromium`, then `python3 tests/test_shark.py`. It uses port 8872 (override with `SA_PORT`) and writes screenshots to /workspace/shark-shots/.

## Notes
`tools/make_icons.py` made the icons from the earlier top-down art. It needs updating to use `render3DShark` before you can run it again.
