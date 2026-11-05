// Shark Attack v1 — side-view 2D ocean. Original art & code. 2D canvas, light on CPU.
"use strict";
/* b53 (B13): storage-safe settings. If localStorage is blocked or throws, the game still starts and keeps best score / settings / sound in memory for this visit. */
const LS=(()=>{const m={};let s=null;try{s=window.localStorage;const k="__sa_t";s.setItem(k,"1");s.removeItem(k)}catch(e){s=null}return {mem:()=>!s,getItem:k=>{try{if(s)return s.getItem(k)}catch(e){}return Object.prototype.hasOwnProperty.call(m,k)?m[k]:null},setItem:(k,v)=>{m[k]=String(v);try{if(s)s.setItem(k,v)}catch(e){}}}})();window.__saLS=LS;
// ======================= EASY-TO-CHANGE SETTINGS =======================
// ROUND_SECONDS: round length. 60 s is the DEFAULT and is NOT YET CONFIRMED by Jeremy. Test override: ?round=N
const ROUND_SECONDS=(()=>{const m=/[?&]round=(\d+(\.\d+)?)/.exec(location.search);return m?+m[1]:60})();
const N_SURF=5,/* b53: 5 surface slots; slots 4-5 only wake from HUD SIZE 8 (sail boats), so the early game keeps 3 */MAX_LEVEL=9,/* b53 (Jeremy t1365u "stops growing at size 10"): internal level 9 = HUD SIZE 10 is the cap (replaces b52 infinite growth) */MAX_PARTS=30,BEST_KEY="sharkAttack_best",SND_KEY="sharkAttack_sound",SONGS_KEY="sharkAttack_songs",SFX_KEY="sharkAttack_sfx",CALM_KEY="sharkAttack_calm",TYPE_KEY="sharkAttack_type",HINT_KEY="sharkAttack_hinted";
// Fish tiers: small / medium / big / giant. Fish clearly bigger than the shark eat it (v9: no markers; judge size by eye).
const TIERS=[{s:16,pts:1,grow:1,col:"#ffd23f",n:8},{s:28,pts:2,grow:2,col:"#7be04a",n:3},{s:44,pts:3,grow:3,col:"#b06cff",n:1},{s:62,pts:5,grow:4,col:"#ff7a1e",n:1}];
const N_FISH=TIERS.reduce((a,t)=>a+t.n,0);
// Steering: the finger's SLIDE direction = swim direction. Each px slid adds "drive" (speed); drive fades when the finger rests.
const STEER={MIN:.2,FULL:.25,DIR_PX:1.5,DRIVE_DECAY:.5,TURN:12,ACC:1.8,DEC:1.2,VK:.45,VDEAD:.18,PITCH_TURN:.6};/* b46 (Jeremy: "way too sensitive with up and down"): VK scales the up/down part of a finger move (0.45: a 45-degree drag now aims about 24 degrees), VDEAD ignores small up/down wobble (|uy|<0.18 of the move), PITCH_TURN slows turning when the turn is mostly up/down */
const TURN3D={SEC:.75,TAIL:5.5,DEAD:.06,PITCH_MIN:.35,BANK:.12,HEAD:.42,N:16,PERSP:2.6,TILT:.16,ARC:.05,FAR_DARK:.32};/* b52: visual yaw eases through 180 deg, tail lags. b53 (Skeptic B5): the body is drawn as N slices along a bending spine in fake 3D (each slice turned by its own yaw, head leads, tail follows), with perspective (near parts bigger), a slight pitch tilt and a rising banked arc, belly light on the side turned to the camera, far side darker, and a head-on view at the head when it points at the camera. Based on general knowledge of how great whites turn (no footage watched). */
const BOOST={MUL:2.2,ACC:4,DUR:1.2,CD:4};/* b52 (Jeremy: "the shark should go really fast"): 1.2 s at 2.2x top speed, whatever the finger asks, then 4 s recharge *//* b46 boost: 1.2 s at 1.15x speed (1.4x acceleration), then 4 s recharge. Tuned with tests/measure_flee.py: a slight edge, not a sure catch */
const boost={t:0,cd:0,n:0};// v10 ANALOG: drive = distance of the finger from its FIRST touch point / (FULL x screen width), 0..1. Held = no decay (the shark never tires; top speed depends only on size). DRIVE_DECAY only after the finger lifts (back to the MIN idle drift).
// Launch: heading up through the surface. power = LAUNCH.K * (speed/max) * (run-up distance at speed / screen height), capped at 1.
const LAUNCH={K:2.2,MIN_POWER:.22,MIN_SPEED:.45,UP:-.35,H_MAX:.32,G:1.6,COOL:.3};// H_MAX: max height as fraction of screen height, G: gravity in screen-heights/s^2
const SURFERS=[{kind:"kneel",pts:15,hy:16,grow:2,label:"SPLASH!"},{kind:"stand",pts:20,hy:46,grow:2,label:"SPLASH!"},{kind:"sail",pts:25,hy:8,hw:100,grow:3,label:"SAIL BOAT!"},{kind:"cargo",pts:40,hy:16,hw:320,grow:4,label:"CARGO SHIP!"},{kind:"tanker",pts:55,hy:18,hw:360,grow:5,label:"OIL TANKER!"}];
/* b57 (Jeremy via Eve): sail and cargo were skipping the growth bar. need(l)=NEED_BASE*NEED_RATIO^l = 3*1.25^l.
   A surfer is grow 2 (about one good fish: food fish are GROW.REL*s/bite = 3*s/bite, about 1.2-2.5). At the surfer unlock (lvl 4) that is 2/7.32 = 27% of the bar.
   Old sail grow 5 at its unlock (lvl 6, need 11.44) filled 44% of the bar; old cargo grow 10 at lvl 8 (need 17.88) filled 56%.
   New sail grow 3 fills 26% at lvl 6 (same fraction a surfer is at its own unlock, 1.5 fish). New cargo grow 4 fills 22% at lvl 8 (two surfers, not five).
   Points follow: sail 40→25, cargo 100→40. Tanker is the next surface prey (55 pts, grow 5 = 28% of the bar at lvl 8), still a step, not a skip.
   Fish stay about 1-4 points. */
const SURFACE={SAIL_LVL:6,CARGO_LVL:8,MINK:.0005};/* b55 (Jeremy): surfers HUD 5 (GROW.SURF_LVL 4), sail boats HUD 7, cargo ships HUD 9 *//* b53 (size-10 cap): surfers are prey from HUD SIZE 7 (GROW.SURF_LVL 6, unchanged b51 rule), sail boats join from HUD SIZE 8, cargo ships from HUD SIZE 9 (world px: sail 200 long, cargo 640) */// hy: how high above the water the surfer's catch point is
/* b57 zones, in depthRaw (0 = surface, 1 = old BED). No depth ceiling: allowedD stays Infinity and nothing stops the shark.
   SURF is where a sailboat's drawn length has shrunk to a surfer's length. Above it: surfers edible, water stays light blue.
   At/below it: surfers stop being edible, tiny sailboats stay edible, oil tankers start. Same number for all three.
   CARGO is where cargo ships stop being edible and the water reaches black. The sea keeps going. */
const ZONE={SURF:1.6,CARGO:4};
const SAIL_SPAN=200,SURFER_SPAN=36,SAIL_SHRINK=(SAIL_SPAN/SURFER_SPAN-1)/ZONE.SURF;/* 2*sail hw vs 2*(surfer hw||18). sailDepthK(ZONE.SURF)=SURFER_SPAN/SAIL_SPAN */
/* Colour stops are depthRaw, stretched from the surface to ZONE.CARGO, then held at CAP_COL (the colour continues; it is not a floor).
   b56 and earlier packed these hues into SURF..BED+0.35 screens (depthRaw about 0..1.08), so the picture was black by the old bed.
   b57 spreads them so the surfer zone stays light blue, the sail zone is the middle blues, and black starts at the cargo edge. */
const LIGHT={
 STOPS:[[0,"#2eaedb"],[.6,"#3aa8d4"],[1.28,"#1b8dc4"],[1.6,"#1780b8"],[2.2,"#12649f"],[2.8,"#0f4479"],[3.4,"#0a2652"],[3.8,"#06122e"],[4,"#03070f"]],
 FOG:[[0,"rgba(16,80,120,.12)"],[1.6,"rgba(16,80,120,.20)"],[2.8,"rgba(8,40,80,.34)"],[4,"rgba(4,18,44,.50)"]]
};
const BEAT={PLACEHOLDER_BPM:100,CHIPTUNE_BPM:120/*v10: eighth-note pulse of "Open Water" v2 (6/8, eighth = 0.5 s)*/,ASSIST_MS:80,PERFECT_MS:45,PERFECT_BONUS:1,on:true};
const SAFE_SPAWN_S=1.5;
// ---- v6: LANDSCAPE WORLD + DEPTH ----
// WORLD.SCREENS: world height in screen heights (camera follows the shark up/down). SKY: sky band above the surface (screen heights).
// FLOOR: volcanic floor thickness (screen heights) at the very bottom.
const WORLD={SCREENS:5,SKY:.3,FLOOR:.5,CAM_EASE:6};
// Depth zones (0 = surface, 1 = volcanic floor). Shown on the depth meter.
const ZONES=[{d:0,name:"Sunlit",col:"#3fc4f0"},{d:ZONE.SURF/ZONE.CARGO,name:"Sail",col:"#1780b8"},{d:2.8/ZONE.CARGO,name:"Deep",col:"#0f4479"},{d:3.8/ZONE.CARGO,name:"Abyss",col:"#05070f"}];/* b57: meter runs 0..1 across depthRaw 0..ZONE.CARGO (was 0..1 = the old bed, bands at .3/.62/.86) */
// GROWTH: b53 (Jeremy t1367u/t1368u, one smooth curve measured as size-bar movement per fish): growth needed to fill the bar at internal level l (HUD size l+1) = NEED_BASE × NEED_RATIO^l, so a fish worth g moves the bar g / (3 × 1.25^l) of its width (1.25x less every size; no tiers); a creature gives size/GROW_DIV growth; a surfer gives SURFER.
// v8 growth: the shark starts as a minnow (START x full size) and gets STEP x bigger per level. Surfers need level SURF_LVL.
// The shark is DRAWN the same size all game; instead the world shrinks around it (worldK = 1/true size), eased so nothing pops.
const GROW={NEED_BASE:3,NEED_RATIO:1.25,REL:3,SURFER:2,START:.4,STEP:1.175,SURF_LVL:4,FOOD_LVL:6,EASE:3,NUM_L:2000};
const trueGrow=l=>GROW.START*Math.pow(GROW.STEP,Math.min(l,GROW.NUM_L));/* b52: exponent clamped only so the number stays finite (1.175^2000 ~ 1e140); the world keeps shrinking far past any reachable size */
// v10 b42 DIVE: swimming DOWN takes longer the smaller the shark is. Down speed x diveK = true size / true size at SURF_LVL (clamped MIN..1).
// The world (zones, floor, spawn bands) stays the same; only the downward part of the shark's swim is slowed, so depth in body lengths grows as the shark shrinks.
const DIVE={REF_LVL:6,MIN:.4};const diveK=l=>Math.max(DIVE.MIN,Math.min(1,trueGrow(l)/trueGrow(DIVE.REF_LVL)));
// SEA CREATURES (fish + sharks), judged against YOUR current size: smaller ones flee, bigger ones chase.
// N: creatures alive near you. SIZE_*: creature size (px "bite size") range shallow -> deep. SHARK_P_*: chance a creature is a shark, shallow -> deep.
// FOOD_SHARE: share of spawns forced smaller than you (so there is always food). SENSE: notice range (screen heights).
// b46 (Jeremy: "the fish still swim away too fast"): flee speeds cut: shallow .725-.785 -> .62-.66, deep .785-.865 -> .66-.69, per level .01 -> .008, cap .90 -> .72.
// v10 fish speed (Dynamics): sprint = FLEE_SHALLOW..FLEE_DEEP by depth (0.60-0.70 shallow, 0.70-0.82 deep; FLEE_MIN..FLEE_MAX = 0.60-0.72 is the typical spawn range), +FLEE_LVL per shark level, capped FLEE_CAP; fish bigger than FLEE_NEAR_R of your bite (near the bite limit) x FLEE_NEAR_K. Only FISH tire; the shark never does. (old: rolled per spawn, 0.85-0.92; plankton just drifts at .15); after FLEE_BURST_S of sprinting it tires to FLEE_TIRED for FLEE_TIRED_S and CHASE_*: chasing speed, both × YOUR current top speed (chasers are always slower than your top speed).
// GIVEUP_S: a chaser gives up after this long, then rests REST_S. GLOW_DEPTH: below this depth, glowing fish + big sharks.
// v10 item 6 DODGE (Dynamics Lead design, tuned with tests/measure_flee.py): only while sprinting, never tired. Shark within R shark lengths + cooldown ready ->
// WIG s readable wiggle, then the fish snaps sideways to the flee line (GAIN instead of the normal 2.2) for DUR s, away from the side the shark is turning to,
// then flees again. Same flee speed (fish stay slower than the shark). Never turns into the surface or the floor.
const DODGE={ON:true,TIRED:true,R:2.5,R_TIRED:1.2,WIG:.15,GAIN:7,ANG_SHALLOW:60,ANG_DEEP:80,CD_SHALLOW:1.4,CD_DEEP:.8,ZIG_P:.25,ZIG_AT:.25,DUR:.45,
 SMALL_Q:.35,SMALL:{ang:85,dur:.35,cd:.8},MID:{ang:55,dur:.55,cd:1.2},NEAR_Q:.7,NEAR:{ang:40,dur:.45,cdS:2.5},CD_LVL:.03,CD_MIN:.6};
const CREATURES={N:45,SIZE_MIN:6,SIZE_SHALLOW:34,SIZE_DEEP:95,SHARK_P_SHALLOW:.04,SHARK_P_DEEP:.38,FOOD_SHARE:.55,SENSE:.55,SENSE_L:2.4,FLEE_MIN:.60,FLEE_MAX:.72,FLEE_SHALLOW:[.62,.66],FLEE_DEEP:[.66,.69],FLEE_LVL:.008,FLEE_CAP:.72,FLEE_NEAR_R:.7,FLEE_NEAR_K:.9,FLEE_BURST_S:1.8,FLEE_TIRED:.65,FLEE_TIRED_S:.8,CHASE_SHALLOW:.6,CHASE_DEEP:.7,GIVEUP_S:3.5,REST_S:3,GLOW_DEPTH:.8,CHASE_MIN_D:.3,MAX_BIG:2,SPREAD_PX:110,GLOW_MAX:.84,REF_BITE:34,DEPTH_K:.85};
/* b57 DEPTH_K: below LAYERS.MID, sharks (and other deep creatures already bigger than you) keep growing as 1+DEPTH_K*(depthRaw-MID).
   No fade-out with level (the old DEEP.GROW fade still exists on top, and dies by lvl 6) and no stop at depth 1.
   Edible fish get a smaller bump and stay under 0.84× bite, so deeper food is larger but still food. MAX_LEVEL stays 9 (HUD 10, b53).
   By HUD 9-10 every band above depth 1.6 is tiny, so the last sizes are fed below that, and those fish/sharks are larger the deeper you go.
   Cargo itself stops once you have been to ZONE.CARGO, so past the black edge only those fish feed you. The meter still stops at HUD 10. */
// GAME MODES. "timed" = 60 s round. "endless" = no timer, ends only when eaten (Gulp!). b52 (Jeremy t1343u "no more divers"): no divers, nets or ambush.
// v8b world: endless left/right/down (only the surface is a boundary). Depth layers (fractions of SURF..BED, BED = start of the dark cap):
const LAYERS={TOP:.3,MID:.62};const VANISH={EDGES:[.3,.62,1,1.6],LVL:[4,6,8,9],FADE:.8,TINY:.3};/* b55 (Jeremy t1627u): an outgrown band is NOT emptied any more: its fish stay and swim, but are too small to eat (f.tiny: size TINY x bite, harmless, not food) *//* b52 (Jeremy): LVL is the internal level (HUD size - 1): b53 rescale for the size-10 cap (Jeremy t1365u): the fish in each depth band are gone from HUD SIZE 5 / 7 / 9 / 10 (lvl>=4/6/8/9); the band below depth 1.6 always has fish. b53: all sizes in comments, tests and reports are HUD sizes. */// top < .3 <= mid < .62 <= deep (deep continues forever below)
// v9: no depth lock. Every stage may dive anywhere; the danger (big creatures that eat you) is the limit.
const DEPTH_LIMIT={FREE_LVL:0};const allowedD=l=>Infinity;
// depth-locked spawn tables (weights per layer). Fish = small fish on top, mid fish in the middle; deep = glow fish, anglerfish, octopus, starfish (seabed strip)
const SPAWN=[[["plankton",.45],["fish",.55]],[["fish",.84],["shark",.16]],[["glow",.4],["octo",.16],["angler",.08],["shark",.36]]];
const ALLOWED={plankton:[0],fish:[0,1],shark:[1,2],glow:[2],octo:[2],angler:[2],star:[2]};
const ANGLER_D=.75,STAR_P=.5;// anglerfish only in the lower deep (needs stage 5+ to reach); starfish: share of deep spawns on the seabed strip
const CAP_COL="#03070f",FLOOR_CUT=.62;// seabed sprite reaches the cap colour at 62% of its height; below that a solid fill is drawn
const MODES=["timed","endless"],MODE_KEY="sharkAttack_mode";
// Shark types — they differ in size and play (decided with Jeremy: numbers are OUR choice, tune them here).
// size: start-size multiplier (fish danger is always judged against the shark's CURRENT size), speed: top speed, acc: acceleration,
// turn: turning rate, catchR: air catch radius for surfers, leap: launch height, grow: growth-meter fill rate. bars: pick-screen stat bars 1..5.
const TYPES_MECHANICAL=!/[?&]flat/.test(location.search);// true = types play differently (decided). ?flat (tests) makes all three identical, looks only
const SHARK_PALS=[];const TYPES={
 white:{name:"Great White",desc:"Biggest and fastest, but turns wide and speeds up slowly.",body:"#5d6e7e",hi:"#93a3b0",belly:"#eceff1",ext:"#26323d",stripe:null,hammer:false,
  size:1.2,speed:1.12,acc:.8,turn:.8,catchR:1.0,leap:1.0,grow:1.0,bars:{Size:5,Speed:5,Jump:3}},
 hammer:{name:"Hammerhead",desc:"Turns the tightest and grabs surfers best. Jumps a bit lower.",body:"#6a7a74",hi:"#a2afa9",belly:"#e9ece8",ext:"#2e3a35",stripe:null,hammer:true,
  size:1.0,speed:1.0,acc:1.0,turn:1.3,catchR:1.35,leap:.9,grow:1.0,bars:{Size:3,Speed:3,Jump:2}},
 tiger:{name:"Tiger Shark",desc:"Smallest, but quick off the mark, jumps highest and grows fast.",body:"#7a7660",hi:"#b0a988",belly:"#efe9d8",ext:"#3a3626",stripe:"#2c281b",hammer:false,
  size:.9,speed:1.0,acc:1.3,turn:1.05,catchR:1.0,leap:1.2,grow:1.5,bars:{Size:2,Speed:3,Jump:5}}};
SHARK_PALS.push(TYPES.white,TYPES.hammer,TYPES.tiger);// enemy sharks use the same three real species
// =======================================================================
const SHOW_FPS=/[?&]fps/.test(location.search);
// ---- RENDER QUALITY (v8 G). Canvas pixel ratio = min(device DPR, DPR_CAP) x render scale. ?rs=0.5..2 sets the scale, ?dprcap= the cap,
// ?fx=0..3 the effects level (0 minimal, 1 low, 2 default, 3 extra), ?adapt=0 turns adaptive quality off (fixed measurements).
// ADAPTIVE: during play, if the average frame over a 1.5 s window is slower than ADAPT.SLOW_MS, step down one notch
// (fx 2->1, then render scale x0.85 down to ADAPT.RS_MIN, then fx 0). Steps back up after ADAPT.GOOD_WIN fast windows in a row.
const QP=(k,d)=>{const m=new RegExp("[?&]"+k+"=([0-9.]+)").exec(location.search);return m?+m[1]:d};
const DPR_CAP=Math.max(.5,Math.min(4,QP("dprcap",2))),RS0=Math.max(.5,Math.min(2,QP("rs",1))),FX0=Math.max(0,Math.min(3,Math.round(QP("fx",2)))),ADAPT_ON=QP("adapt",1)!==0;
const ADAPT={WIN_S:.75,SLOW_MS:21,FAST_MS:13,GOOD_WIN:6,RS_STEP:.85,RS_MIN:.6};
let FX=FX0,RSK=1;const adapt={t:0,n:0,sum:0,good:0,steps:0,log:[]};
const C=document.getElementById("c"),X=C.getContext("2d",{alpha:false});
const $=id=>document.getElementById(id);
let W=0,H=0,DPR=1,state="tap",roundLen=ROUND_SECONDS,SURF=150,BED=800;
let sType=TYPES[LS.getItem(TYPE_KEY)]?LS.getItem(TYPE_KEY):"white";
const trait=k=>TYPES_MECHANICAL?TYPES[sType][k]:1;
const P={ink:"#082a3d",foam:"rgba(220,248,255,.45)",red:"#e2463c",yel:"#ffcc33"};
function mk(w,h){const c=document.createElement("canvas");c.width=Math.max(1,Math.ceil(w));c.height=Math.max(1,Math.ceil(h));return c}

// ---------- art ----------
// v8 shaded art helpers: mix a #rrggbb colour toward black (k<0) or white (k>0)
function tone(hex,k){const n=parseInt(hex.slice(1),16);let r=n>>16,g=n>>8&255,b=n&255;const t=k<0?0:255,a=Math.abs(k);r=Math.round(r+(t-r)*a);g=Math.round(g+(t-g)*a);b=Math.round(b+(t-b)*a);return `rgb(${r},${g},${b})`}
// shaded fish, side view facing right, centred at 0,0, length ~1.6s. tier 0 slim minnow, 1 perch, 2 striped snapper, 3 heavy grouper. No cartoon outline.
function drawFish(g,s,col,tier,danger){g.lineJoin="round";const bh=s*[.24,.3,.33,.38][tier],nose=s*.62,tail=-s*.5;
 const body=()=>{g.beginPath();g.moveTo(nose,s*.02);g.bezierCurveTo(nose*.8,-bh*1.05,-s*.1,-bh*1.1,tail,-bh*.18);g.lineTo(tail,bh*.18);g.bezierCurveTo(-s*.1,bh*1.05,nose*.8,bh*.95,nose,s*.02);g.closePath()};
 const fin=(pts,c0)=>{g.beginPath();g.moveTo(pts[0]*s,pts[1]*s);for(let i=2;i<pts.length;i+=4)g.quadraticCurveTo(pts[i]*s,pts[i+1]*s,pts[i+2]*s,pts[i+3]*s);g.closePath();g.fillStyle=c0;g.fill()};
 const dark=tone(col,-.45),fc=tone(col,-.25);
 fin([tail+s*.04,0,tail-s*.12,-bh*.6/s,tail-s*.3/1,-bh*1.25/s,tail-s*.18,0,tail-s*.3,bh*1.25/s,tail-s*.12,bh*.6/s,tail+s*.04,0].map((v,i)=>i%2?v:v/s),fc);
 fin([s*.12,-bh*.9/s,s*.0,-bh*1.7/s,-s*.18/1,-bh*1.25/s,-s*.25,-bh*.85/s,-s*.25,-bh*.85/s].map((v,i)=>i%2?v:v/s),fc);
 body();const gr=g.createLinearGradient(0,-bh,0,bh);gr.addColorStop(0,dark);gr.addColorStop(.35,col);gr.addColorStop(.62,tone(col,.45));gr.addColorStop(1,tone(col,.2));g.fillStyle=gr;g.fill();
 g.save();body();g.clip();
 if(tier>=2){g.fillStyle=tone(col,-.55);g.globalAlpha=.45;for(let i=0;i<3;i++){g.beginPath();g.ellipse(-s*.22+i*s*.2,-bh*.1,s*.035,bh*.9,.1,0,7);g.fill()}g.globalAlpha=1}
 let q=g.createRadialGradient(s*.2,-bh*.5,0,s*.2,-bh*.5,s*.6);q.addColorStop(0,"rgba(210,235,255,.16)");q.addColorStop(1,"rgba(255,255,255,0)");g.fillStyle=q;g.fillRect(-s,-s,2*s,2*s);
 q=g.createLinearGradient(nose,0,tail,0);q.addColorStop(0,"rgba(0,0,0,0)");q.addColorStop(1,"rgba(0,10,20,.35)");g.fillStyle=q;g.fillRect(-s,-s,2*s,2*s);
 g.strokeStyle="rgba(0,0,0,.28)";g.lineWidth=Math.max(1,s*.025);g.beginPath();g.moveTo(s*.32,-bh*.6);g.quadraticCurveTo(s*.24,0,s*.32,bh*.6);g.stroke();
 g.restore();/* v10 gfx: no emoji gloss */
 fin([s*.2,bh*.35/s,s*.12,bh*.9/s,s*.02,bh*.75/s,s*.08,bh*.5/s,s*.2,bh*.35/s].map((v,i)=>i%2?v:v/s),"rgba(0,0,0,.18)");
 body();g.strokeStyle="rgba(0,10,20,.18)";g.lineWidth=Math.max(.6,s*.01);g.stroke();
 const ex=s*.44,ey=-bh*.25,er=s*(tier===3?.03:.035);g.fillStyle="#7d7356";g.beginPath();g.arc(ex,ey,er*1.25,0,7);g.fill();g.fillStyle="#080b0e";g.beginPath();g.arc(ex,ey,er,0,7);g.fill();g.fillStyle="rgba(230,240,255,.35)";g.beginPath();g.arc(ex+er*.3,ey-er*.3,er*.2,0,7);g.fill();
 g.strokeStyle="rgba(0,0,0,.45)";g.lineWidth=Math.max(1,s*.02);g.beginPath();g.moveTo(nose,s*.03);g.lineTo(nose-s*(tier===3?.14:.07),s*.05+(tier===3?bh*.15:0));g.stroke()}
// ---- SPECIES: our own original stylized sprites (shapes/colours loosely inspired by Florida reef & deep-sea species; no reference art used).
// z: 0 shallow / small prey, 1 mid reef, 2 deeper reef (lower mid layer), 3 deep (drawn for "glow"-kind deep creatures). h = half body height / s.
const SPECIES=[
 {n:"Yellowtail damselfish",z:0,c:"#1d2f6b",c2:"#ffd21f",h:.36,tail:"fork",pat:"dots",eye:.06},
 {n:"Bluehead wrasse",el:1.3,z:0,c:"#3fc46a",c2:"#2a5cff",h:.2,tail:"fork",pat:"head",eye:.05},
 {n:"Bigeye",z:0,c:"#e2352b",c2:"#ff8a70",h:.32,tail:"fork",pat:"none",eye:.11},
 {n:"Blue tang",z:1,c:"#2f55d4",c2:"#ffd84a",h:.5,tail:"lunate",pat:"lines",eye:.06,spine:1},
 {n:"Queen angelfish",z:1,c:"#2fa7a0",c2:"#ffcf1f",h:.58,tail:"round",pat:"crown",eye:.055,trail:1},
 {n:"Queen parrotfish",el:1.2,z:1,c:"#1f9fb0",c2:"#7be04a",h:.32,tail:"lunate",pat:"bands",eye:.05,beak:1},
 {n:"Princess parrotfish",el:1.2,z:1,c:"#3a6fe0",c2:"#ffae2a",h:.3,tail:"lunate",pat:"stripe",eye:.05,beak:1},
 {n:"Striped parrotfish",el:1.2,z:1,c:"#5a7fa8",c2:"#e8f0ff",h:.3,tail:"lunate",pat:"stripes",eye:.05,beak:1},
 {n:"Gray triggerfish",z:1,c:"#8a9aa6",c2:"#5c6b78",h:.46,tail:"lunate",pat:"dots",eye:.05,trig:1},
 {n:"Tiger grouper",el:1.4,z:2,c:"#c8563a",c2:"#5a1e14",h:.34,tail:"round",pat:"bars",eye:.05,big:1},
 {n:"Black grouper",el:1.4,z:2,c:"#4a5560",c2:"#1c2228",h:.34,tail:"round",pat:"blotch",eye:.05,big:1},
 {n:"Nassau grouper",el:1.4,z:2,c:"#c9a27e",c2:"#5b3a26",h:.34,tail:"round",pat:"bars",eye:.05,big:1},
 {n:"Hogfish",el:1.15,z:2,c:"#f0b0a0",c2:"#9c3a3a",h:.38,tail:"lunate",pat:"mask",eye:.045,snout:1,tall:1},
 {n:"Squirrelfish",el:1.2,z:2,c:"#e8402e",c2:"#ffe3d8",h:.3,tail:"fork",pat:"stripes",eye:.1,spiny:1},
 {n:"Silver spinyfin",z:3,c:"#c9ccd2",c2:"#8a2a1c",h:.5,tail:"fork",pat:"none",eye:.12,ring:1},
 {n:"Mirrorbelly",z:3,c:"#a08a62",c2:"#e8e4d4",h:.26,tail:"fork",pat:"belly",eye:.07,dome:1},
 {n:"Fangtooth",z:3,c:"#6b6a3a",c2:"#3a3a20",h:.4,tail:"fork",pat:"none",eye:.04,fang:1},
 {n:"Dragonfish",z:3,c:"#5a3a26",c2:"#c8b89a",h:.16,tail:"round",pat:"hex",eye:.06,fang:1,barbel:1,lng:1.5},
 {n:"Pelican eel",z:3,c:"#22242a",c2:"#ff5a8a",h:.14,tail:"whip",pat:"none",eye:.025,gulp:1,lng:1.7}];
const PLANK_SP=[{n:"Silverside fry",z:0,c:"#b8d8e0",c2:"#eaffff",h:.16,tail:"fork",pat:"belly",eye:.08},{n:"Glass minnow",z:0,c:"#9fd8b0",c2:"#e0fff0",h:.18,tail:"fork",pat:"belly",eye:.09}];
const SP_Z=[0,1,2,3].map(z=>SPECIES.map((p,i)=>p.z===z?i:-1).filter(i=>i>=0));
function drawSpecies(g,s,p){g.lineJoin="round";g.lineCap="round";const L=p.lng||1,E=p.el||1,bh=s*p.h,nose=s*.62*(p.lng?1.05:1)*(1+(E-1)*.4),tail=-s*.5*L*(1+(E-1)*.6),col=p.c,dark=tone(col,-.45),fc=tone(col,-.22);
 const body=()=>{g.beginPath();if(p.lng){g.moveTo(nose,0);g.bezierCurveTo(nose*.85,-bh*1.2,nose*.2,-bh,0,-bh*.9);g.lineTo(tail,-bh*.25);g.lineTo(tail,bh*.25);g.lineTo(0,bh*.9);g.bezierCurveTo(nose*.2,bh,nose*.85,bh*1.2,nose,0)}
  else{const nz=p.snout?nose*1.08:nose;g.moveTo(nz,p.snout?bh*.15:s*.02);g.bezierCurveTo(nose*(p.snout?.55:p.big?.98:.8),-bh*(p.big?1.3:1.1),-s*.12*E,-bh*1.18,tail,-bh*.2);g.lineTo(tail,bh*.2);g.bezierCurveTo(-s*.12*E,bh*1.12,/* rounder */nose*(p.big?.98:.8),bh*(p.big?1.15:.95),nz,p.snout?bh*.15:s*.02)}g.closePath()};
 const poly=(pts,c0,rays)=>{const path=()=>{g.beginPath();g.moveTo(pts[0]*s,pts[1]*s);for(let i=2;i<pts.length;i+=4)g.quadraticCurveTo(pts[i]*s,pts[i+1]*s,pts[i+2]*s,pts[i+3]*s);g.closePath()};path();g.fillStyle=c0;g.globalAlpha=.7;g.fill();g.globalAlpha=1;/* translucent fins */
  if(rays!==0){g.save();path();g.clip();g.strokeStyle="rgba(0,0,0,.22)";g.lineWidth=Math.max(.6,s*.008);const bx=pts[0]*s,by=pts[1]*s;for(let i=2;i<pts.length;i+=2){const ex=pts[i]*s,ey=pts[i+1]*s;for(let k=0;k<3;k++){g.beginPath();g.moveTo(bx,by);g.lineTo(ex+(k-1)*s*.05,ey+(k-1)*s*.05);g.stroke()}}g.fillStyle="rgba(255,255,255,.12)";g.fillRect(-2*s,-2*s,4*s,4*s);g.restore();path();g.strokeStyle="rgba(0,10,20,.3)";g.lineWidth=Math.max(.6,s*.01);g.stroke()}};
 const t0=tail/s,hh=p.h,tc=p.tail==="lunate"||p.n==="Yellowtail damselfish"?p.c2:fc;
 // tail
 if(p.tail==="whip"){g.strokeStyle=fc;g.lineWidth=s*.05;g.beginPath();g.moveTo(tail,0);g.bezierCurveTo(tail-s*.3,s*.25,tail-s*.5,-s*.2,tail-s*.75,s*.05);g.stroke();g.fillStyle=p.c2;g.beginPath();g.arc(tail-s*.75,s*.05,s*.035,0,7);g.fill()}
 else if(p.tail==="round")poly([t0+.03,0,t0-.1,-hh*.9,t0-.28,-hh*.5,t0-.32,0,t0-.28,hh*.5,t0-.1,hh*.9,t0+.03,0],tc);
 else if(p.tail==="lunate")poly([t0+.03,0,t0-.12,-hh*.4,t0-.3,-hh*1.15,t0-.2,0,t0-.3,hh*1.15,t0-.12,hh*.4,t0+.03,0],tc);
 else poly([t0+.04,0,t0-.12,-hh*.5,t0-.32,-hh*1.1,t0-.17,0,t0-.32,hh*1.1,t0-.12,hh*.5,t0+.04,0],tc);
 // dorsal / anal fins
 if(p.spiny||p.tall){g.fillStyle=p.tall?p.c2:tone(col,-.15);g.beginPath();g.moveTo(s*.28,-bh*.8);for(let i=0;i<7;i++){const x=(s*.28-i*s*.09)*E;g.lineTo(x-s*.03,-bh*(p.tall&&i<3?1.9:1.45));g.lineTo(x-s*.09,-bh*.95)}g.lineTo(-s*.35*E,-bh*.5);g.closePath();g.fill();g.strokeStyle="rgba(0,0,0,.3)";g.lineWidth=Math.max(.6,s*.008);for(let i=0;i<7;i++){const x=(s*.28-i*s*.09)*E;g.beginPath();g.moveTo(x-s*.03,-bh*(p.tall&&i<3?1.9:1.45));g.lineTo(x-s*.03,-bh*.8);g.stroke()}}
 else if(p.trail){poly([.15,-hh*.9,-.05,-hh*1.7,-.62,-hh*1.25,-.32,-hh*.75,-.3,-hh*.6],p.c2);poly([.1,hh*.9,-.05,hh*1.7,-.62,hh*1.25,-.32,hh*.75,-.3,hh*.6],p.c2)}
 else if(!p.lng){poly([.22*E,-hh*.9,.05*E,-hh*1.4,-.3*E,-hh*1.25,-.4*E,-hh*.55,-.4*E,-hh*.45],fc);poly([.0,hh*.9,-.15*E,hh*1.35,-.36*E,hh*.8,-.38*E,hh*.5,-.38*E,hh*.4],fc)}
 if(E>1&&!p.lng){poly([.12*E,hh*.95,.02*E,hh*1.55,-.04*E,hh*1.45,.02*E,hh*1.1,.06*E,hh*.95],fc)}// pelvic fin
 else{g.fillStyle=fc;g.fillRect(tail,-bh*.4,-tail*.9,bh*.15)}
 if(p.trig){g.fillStyle=dark;g.beginPath();g.moveTo(s*.2,-bh*.85);g.lineTo(s*.12,-bh*1.45);g.lineTo(s*.06,-bh*.9);g.fill()}
 // body with Echo-style shading
 body();const gr=g.createLinearGradient(0,-bh,0,bh);gr.addColorStop(0,dark);gr.addColorStop(.35,col);gr.addColorStop(.65,tone(col,.4));gr.addColorStop(1,tone(col,.15));g.fillStyle=gr;g.fill();
 g.save();body();g.clip();const c2=p.c2;g.fillStyle=c2;
 if(p.pat==="dots"){g.globalAlpha=.85;for(let i=0;i<9;i++){g.beginPath();g.arc(s*(.35-i*.09),-bh*(.5-(i%3)*.35),s*.022,0,7);g.fill()}}
 else if(p.pat==="head"){g.fillRect(s*.12,-s,s,2*s);g.fillStyle="#111";g.fillRect(s*.02,-s,s*.07,2*s);g.fillStyle="#fff";g.fillRect(-s*.04,-s,s*.06,2*s)}
 else if(p.pat==="lines"){g.strokeStyle=tone(col,-.35);g.lineWidth=s*.015;for(let i=0;i<4;i++){g.beginPath();g.moveTo(s*.4,-bh*.6+i*bh*.35);g.quadraticCurveTo(0,-bh*.9+i*bh*.4,-s*.45,-bh*.3+i*bh*.2);g.stroke()}}
 else if(p.pat==="crown"){g.fillStyle="#0e1d40";g.beginPath();g.arc(s*.28,-bh*.75,s*.07,0,7);g.fill();g.fillStyle=c2;g.globalAlpha=.5;g.beginPath();g.ellipse(s*.05,bh*.55,s*.35,bh*.3,0,0,7);g.fill()}
 else if(p.pat==="bands"){g.globalAlpha=.6;for(let i=0;i<3;i++)g.fillRect(-s*.3+i*s*.25,-s,s*.06,2*s)}
 else if(p.pat==="stripe"){g.fillRect(-s,-bh*.1,2*s,bh*.28);g.fillStyle="#fff";g.globalAlpha=.6;g.fillRect(-s,bh*.35,2*s,bh*.18)}
 else if(p.pat==="stripes"){g.globalAlpha=.75;for(let i=0;i<4;i++)g.fillRect(-s,-bh*.7+i*bh*.42,2*s,bh*.12)}
 else if(p.pat==="bars"){g.globalAlpha=.55;for(let i=0;i<5;i++){g.save();g.translate(s*(.3-i*.18),0);g.rotate(.25);g.fillRect(-s*.035,-s,s*.07,2*s);g.restore()}}
 else if(p.pat==="blotch"){g.globalAlpha=.6;for(let i=0;i<10;i++){g.beginPath();g.ellipse(s*(.35-i*.08),bh*((i%2)?.3:-.4),s*.05,bh*.22,0,0,7);g.fill()}}
 else if(p.pat==="mask"){g.globalAlpha=.75;g.beginPath();g.moveTo(s*.75,0);g.lineTo(s*.2,-bh*1.1);g.lineTo(s*.08,-bh*1.1);g.lineTo(s*.5,0);g.closePath();g.fill()}
 else if(p.pat==="belly"){g.globalAlpha=.8;g.fillRect(-s,bh*.15,2*s,bh)}
 else if(p.pat==="hex"){g.globalAlpha=.4;g.strokeStyle=c2;g.lineWidth=s*.012;for(let x=-s*.9;x<s*.3;x+=s*.08){g.beginPath();g.arc(x,bh*.4,s*.04,0,7);g.stroke()}}
 g.globalAlpha=1;
 if(!p.gulp){const sc=s*(p.lng?.035:.045);g.strokeStyle=p.z===3?"rgba(255,255,255,.12)":"rgba(0,0,0,.16)";g.lineWidth=Math.max(.5,s*.007);for(let r=0,y=-bh;y<bh;y+=sc*.8,r++)for(let x=nose-s*.18-(r%2)*sc*.5;x>tail;x-=sc){g.beginPath();g.arc(x,y,sc*.55,-1.2,1.2);g.stroke()}
  g.strokeStyle="rgba(255,255,255,.18)";g.lineWidth=Math.max(.6,s*.01);g.beginPath();g.moveTo(nose*.7,-bh*.05);g.quadraticCurveTo(0,bh*.08,tail,0);g.stroke()}// scale rows + lateral line
 let q=g.createRadialGradient(s*.2,-bh*.5,0,s*.2,-bh*.5,s*.6);q.addColorStop(0,"rgba(210,235,255,.16)");q.addColorStop(1,"rgba(255,255,255,0)");g.fillStyle=q;g.fillRect(-2*s,-s,4*s,2*s);
 q=g.createLinearGradient(nose,0,tail,0);q.addColorStop(0,"rgba(0,0,0,0)");q.addColorStop(1,"rgba(0,10,20,.35)");g.fillStyle=q;g.fillRect(-2*s,-s,4*s,2*s);
 g.strokeStyle="rgba(0,0,0,.28)";g.lineWidth=Math.max(1,s*.025);g.beginPath();g.moveTo(s*.32,-bh*.6);g.quadraticCurveTo(s*.24,0,s*.32,bh*.6);g.stroke();
 g.restore();/* v10 gfx: no emoji gloss */
 if(p.spine){g.fillStyle="#fff";g.beginPath();g.ellipse(tail+s*.06,0,s*.04,s*.012,0,0,7);g.fill()}
 if(!p.lng)poly([.2,hh*.35,.12,hh*.9,.02,hh*.75,.08,hh*.5,.2,hh*.35],"rgba(0,0,0,.18)");
 body();g.strokeStyle="rgba(0,10,20,.18)";g.lineWidth=Math.max(.6,s*.01);g.stroke();
 // jaws: fangs (stylized white points, no gore), parrot beak, pelican-eel gulper
 if(p.gulp){g.fillStyle=tone(col,.12);g.beginPath();g.moveTo(nose*.2,bh*.5);g.quadraticCurveTo(nose*.9,bh*3,nose*1.15,bh*.6);g.lineTo(nose,0);g.closePath();g.fill();g.strokeStyle="rgba(0,0,0,.5)";g.stroke()}
 if(p.fang){g.fillStyle="#f4f0e0";for(let i=0;i<4;i++){const x=nose-s*.03-i*s*.05;g.beginPath();g.moveTo(x,s*.01);g.lineTo(x-s*.015,s*.01+bh*(i%2?.25:.45));g.lineTo(x-s*.03,s*.01);g.fill()}}
 if(p.big){g.strokeStyle="rgba(20,5,0,.6)";g.lineWidth=Math.max(1,s*.022);g.beginPath();g.moveTo(nose,s*.03);g.quadraticCurveTo(nose*.8,bh*.45,nose*.55,bh*.3);g.stroke();g.fillStyle="rgba(0,0,0,.18)";g.beginPath();g.moveTo(nose,s*.04);g.quadraticCurveTo(nose*.85,bh*.75,nose*.5,bh*.5);g.quadraticCurveTo(nose*.8,bh*.4,nose,s*.04);g.fill()}
 if(p.beak){g.fillStyle="#e9f2e8";g.beginPath();g.arc(nose-s*.02,s*.02,s*.04,-1.4,1.4);g.fill()}
 if(p.dome){g.fillStyle="rgba(220,240,255,.55)";g.beginPath();g.ellipse(s*.42,-bh*.55,s*.07,s*.05,0,0,7);g.fill()}
 if(p.barbel){g.strokeStyle=tone(p.c2,-.2);g.lineWidth=Math.max(1,s*.015);g.beginPath();g.moveTo(nose*.85,bh*.9);g.quadraticCurveTo(nose*.7,bh*3,nose*.95,bh*4.2);g.stroke()}
 const ex=p.snout?nose*.62:nose*(p.big?.66:.71),ey=-bh*(p.lng?.3:.25),er=s*Math.min(.035,p.eye*.42);/* v10 item 12: smaller realistic eyes */g.fillStyle="rgba(0,0,0,.35)";g.beginPath();g.arc(ex,ey,er*1.45,0,7);g.fill();{const ig=g.createRadialGradient(ex,ey,er*.6,ex,ey,er*1.3);ig.addColorStop(0,p.ring?p.c2:p.z===3?"#c8d0c0":"#e8c050");ig.addColorStop(1,p.ring?tone(p.c2,-.4):p.z===3?"#606858":"#8a5a20");g.fillStyle=ig;g.beginPath();g.arc(ex,ey,er*1.3,0,7);g.fill()}g.fillStyle="#04060a";g.beginPath();g.arc(ex,ey,er*.85,0,7);g.fill();g.fillStyle="rgba(230,240,255,.35)";g.beginPath();g.arc(ex+er*.3,ey-er*.3,er*.2,0,7);g.fill();
 if(!p.fang&&!p.gulp){g.strokeStyle="rgba(0,0,0,.45)";g.lineWidth=Math.max(1,s*.02);g.beginPath();g.moveTo(nose*(p.snout?1.08:1),s*.03);g.lineTo(nose-s*.07,s*.05);g.stroke()}}
// the cheap lure / eye dot (baked into a tiny glow sprite, drawn with the halo pass): offset of the lit spot per deep species
function spLure(p,s){const nose=s*.62*1.05,bh=s*p.h;return p.barbel?[nose*.95,bh*4.2]:p.gulp?[-s*.5*p.lng-s*.75,s*.05]:null}
// b52: sail boat, side view facing right, waterline at y=0, 200 px long. Our own art, drawn in code.
function drawSailBoat(g){g.lineJoin="round";g.lineCap="round";
 let q=g.createLinearGradient(0,0,0,26);q.addColorStop(0,"rgba(20,40,55,.55)");q.addColorStop(1,"rgba(20,40,55,0)");g.fillStyle=q;g.beginPath();g.moveTo(-70,0);g.quadraticCurveTo(-10,10,60,0);g.lineTo(18,0);g.lineTo(6,24);g.lineTo(-14,24);g.lineTo(-22,0);g.closePath();g.fill();
 q=g.createLinearGradient(0,-19,0,2);q.addColorStop(0,"#ffffff");q.addColorStop(.55,"#e4eaee");q.addColorStop(1,"#a9b6bf");g.fillStyle=q;g.beginPath();g.moveTo(-97,-15);g.quadraticCurveTo(0,-13,104,-19);g.quadraticCurveTo(96,-8,86,0);g.quadraticCurveTo(0,3,-88,0);g.quadraticCurveTo(-96,-6,-97,-15);g.closePath();g.fill();
 g.strokeStyle="#1d3550";g.lineWidth=2.2;g.beginPath();g.moveTo(-96,-12.5);g.quadraticCurveTo(0,-10.5,101,-16);g.stroke();
 g.fillStyle="#1d3550";g.beginPath();g.moveTo(-89,-2.5);g.quadraticCurveTo(0,.5,87,-2.5);g.lineTo(86,0);g.quadraticCurveTo(0,3,-88,0);g.closePath();g.fill();
 q=g.createLinearGradient(0,-29,0,-15);q.addColorStop(0,"#fbfcfd");q.addColorStop(1,"#c9d2d8");g.fillStyle=q;g.beginPath();g.moveTo(-46,-15);g.lineTo(-40,-27);g.lineTo(22,-28);g.lineTo(34,-16);g.closePath();g.fill();
 g.fillStyle="#22313d";for(const x of[-30,-16,-2,12])g.fillRect(x,-24,8,3.5);
 g.strokeStyle="#9aa3aa";g.lineWidth=1;g.beginPath();g.moveTo(14,-246);g.lineTo(102,-19);g.moveTo(10,-246);g.lineTo(-96,-15);g.moveTo(12,-200);g.lineTo(-6,-16);g.lineTo(28,-16);g.lineTo(12,-200);g.stroke();
 q=g.createLinearGradient(-86,0,10,0);q.addColorStop(0,"#cfc9bd");q.addColorStop(.6,"#f1eee6");q.addColorStop(1,"#fbfaf6");g.fillStyle=q;g.beginPath();g.moveTo(9,-244);g.quadraticCurveTo(-30,-150,-86,-40);g.lineTo(9,-38);g.closePath();g.fill();
 g.strokeStyle="rgba(120,112,98,.35)";g.lineWidth=.8;g.beginPath();for(let i=1;i<6;i++){const y=-38-i*34;g.moveTo(9,y);g.lineTo(9-(y+244)/206*95*.98,y)}g.stroke();
 q=g.createLinearGradient(14,0,100,0);q.addColorStop(0,"#fbfaf6");q.addColorStop(1,"#d3cdc1");g.fillStyle=q;g.beginPath();g.moveTo(15,-212);g.quadraticCurveTo(62,-110,98,-22);g.lineTo(20,-30);g.closePath();g.fill();
 g.strokeStyle="rgba(90,84,74,.35)";g.lineWidth=1;g.beginPath();g.moveTo(15,-212);g.lineTo(20,-30);g.stroke();
 q=g.createLinearGradient(6,0,13,0);q.addColorStop(0,"#d8dde0");q.addColorStop(.5,"#ffffff");q.addColorStop(1,"#8f989e");g.fillStyle=q;g.fillRect(8,-250,4.5,236);
 g.fillStyle="#7d868c";g.fillRect(-88,-41,98,3.5);
 g.fillStyle="rgba(255,255,255,.55)";g.beginPath();g.ellipse(84,1,22,2.2,0,0,7);g.fill()}
// b52: cargo ship, side view facing right, waterline at y=0, 640 px long. Our own art, drawn in code.
function drawCargoShip(g){g.lineJoin="round";
 let q=g.createLinearGradient(0,0,0,24);q.addColorStop(0,"rgba(90,24,20,.6)");q.addColorStop(1,"rgba(40,12,10,0)");g.fillStyle=q;g.beginPath();g.moveTo(-316,0);g.lineTo(300,0);g.quadraticCurveTo(318,10,296,22);g.lineTo(-300,22);g.closePath();g.fill();
 q=g.createLinearGradient(0,-46,0,0);q.addColorStop(0,"#2c3d4c");q.addColorStop(.25,"#1c2833");q.addColorStop(1,"#0c1218");g.fillStyle=q;g.beginPath();g.moveTo(-320,-44);g.lineTo(312,-46);g.quadraticCurveTo(318,-24,302,0);g.lineTo(-312,0);g.lineTo(-322,-30);g.closePath();g.fill();
 g.fillStyle="#8a2a22";g.beginPath();g.moveTo(-313,-7);g.lineTo(305,-7);g.lineTo(302,0);g.lineTo(-312,0);g.closePath();g.fill();
 g.strokeStyle="rgba(230,236,240,.7)";g.lineWidth=1.4;g.beginPath();g.moveTo(-318,-40);g.lineTo(312,-42);g.stroke();
 g.strokeStyle="rgba(255,255,255,.12)";g.lineWidth=1;g.beginPath();for(let x=-280;x<300;x+=40){g.moveTo(x,-38);g.lineTo(x,-8)}g.stroke();
 const C=["#8c3b2c","#2f5a87","#7c8388","#3d6b4a","#c9c4b8","#b8652a","#5d3f6a","#2a6f78"];let sd=7;const r=()=>(sd=(sd*9301+49297)%233280)/233280;
 for(let x=-196;x<282;x+=13){if(Math.abs(x+40)<5||Math.abs(x-120)<5)continue;const tiers=4+Math.floor(r()*3);for(let t=0;t<tiers;t++){const y=-46-(t+1)*6.4,c=C[Math.floor(r()*C.length)];q=g.createLinearGradient(0,y,0,y+6.4);q.addColorStop(0,c);q.addColorStop(1,"rgba(0,0,0,.35)");g.fillStyle=c;g.fillRect(x,y,12.4,6.2);g.fillStyle=q;g.fillRect(x,y,12.4,6.2);g.fillStyle="rgba(0,0,0,.25)";g.fillRect(x+12.2,y,.8,6.2)}}
 q=g.createLinearGradient(-262,0,-196,0);q.addColorStop(0,"#d9dee2");q.addColorStop(.5,"#f6f8f9");q.addColorStop(1,"#b9c1c7");g.fillStyle=q;g.fillRect(-254,-96,52,52);
 g.fillStyle="#26323c";for(let y=-90;y<-50;y+=9)for(let x=-250;x<-206;x+=7)g.fillRect(x,y,4.2,3.2);
 g.fillStyle="#e9edf0";g.fillRect(-266,-104,76,8);g.fillStyle="#1a242c";g.fillRect(-264,-102,72,3.4);
 q=g.createLinearGradient(-300,0,-276,0);q.addColorStop(0,"#1a1f24");q.addColorStop(.5,"#3a4148");q.addColorStop(1,"#15191d");g.fillStyle=q;g.beginPath();g.moveTo(-298,-44);g.lineTo(-296,-100);g.lineTo(-276,-102);g.lineTo(-278,-44);g.closePath();g.fill();g.fillStyle="#a8322a";g.fillRect(-297,-90,20,6);
 g.strokeStyle="#c8cfd4";g.lineWidth=1.6;g.beginPath();g.moveTo(-228,-104);g.lineTo(-228,-122);g.moveTo(-236,-116);g.lineTo(-220,-116);g.moveTo(296,-46);g.lineTo(296,-66);g.stroke();
 g.fillStyle="rgba(255,255,255,.55)";g.beginPath();g.ellipse(300,1,40,2.6,0,0,7);g.fill();g.beginPath();g.ellipse(-310,1,28,2,0,0,7);g.fill()}
// b57: oil tanker, side view facing right, waterline at y=0, 720 px long. Own art, drawn in code (one baked sprite, same as sail/cargo).
function drawOilTanker(g){g.lineJoin="round";g.lineCap="round";
 let q=g.createLinearGradient(0,0,0,28);q.addColorStop(0,"rgba(20,40,55,.5)");q.addColorStop(1,"rgba(20,40,55,0)");g.fillStyle=q;g.beginPath();g.moveTo(-360,0);g.lineTo(350,0);g.quadraticCurveTo(370,12,340,26);g.lineTo(-340,26);g.closePath();g.fill();
 q=g.createLinearGradient(0,-40,0,2);q.addColorStop(0,"#3d4e46");q.addColorStop(.35,"#24302b");q.addColorStop(1,"#121816");g.fillStyle=q;g.beginPath();g.moveTo(-350,-36);g.lineTo(340,-38);g.quadraticCurveTo(356,-18,338,0);g.lineTo(-348,0);g.lineTo(-358,-22);g.closePath();g.fill();
 g.fillStyle="#8d2e2a";g.beginPath();g.moveTo(-348,-8);g.lineTo(336,-8);g.lineTo(334,0);g.lineTo(-348,0);g.closePath();g.fill();
 g.strokeStyle="rgba(220,230,226,.7)";g.lineWidth=1.4;g.beginPath();g.moveTo(-346,-34);g.lineTo(336,-36);g.stroke();
 for(const [x,y,w,h] of[[-280,-36,86,26],[-150,-36,86,26],[0,-36,86,26],[130,-36,70,24]]){q=g.createLinearGradient(x,y-h,x+w,y+4);q.addColorStop(0,"#6a5a48");q.addColorStop(.4,"#d2c4ac");q.addColorStop(.75,"#8c7b62");q.addColorStop(1,"#3e352c");g.fillStyle=q;g.beginPath();g.moveTo(x,y);g.lineTo(x,y-h+8);g.quadraticCurveTo(x,y-h-6,x+w/2,y-h-6);g.quadraticCurveTo(x+w,y-h-6,x+w,y-h+8);g.lineTo(x+w,y);g.closePath();g.fill();g.strokeStyle="rgba(0,0,0,.28)";g.lineWidth=1;g.stroke()}
 g.strokeStyle="#5c6560";g.lineWidth=3;g.beginPath();g.moveTo(-250,-52);g.lineTo(210,-54);g.stroke();
 q=g.createLinearGradient(230,0,340,0);q.addColorStop(0,"#d5dbd6");q.addColorStop(.5,"#f7faf8");q.addColorStop(1,"#9aa39c");g.fillStyle=q;g.fillRect(236,-86,96,50);
 g.fillStyle="#1c2420";for(let y=-78;y<-42;y+=9)for(let x=244;x<322;x+=12)g.fillRect(x,y,7,4);
 g.fillStyle="#2a2420";g.fillRect(292,-118,24,34);g.fillStyle="#8d2e2a";g.fillRect(292,-104,24,8);
 g.fillStyle="rgba(255,255,255,.5)";g.beginPath();g.ellipse(330,2,36,2.4,0,0,7);g.fill()}
// surfer on a board, side view, board centred at 0,0 on the water line. Shaded skin, wetsuit, hair, board with stringer.
function drawSurfer(g,s,stand){g.lineJoin="round";g.lineCap="round";const skin="#d89a6a",skinD="#a8693f",suit=stand?"#1f4f7a":"#27313b";
 let q=g.createLinearGradient(0,-s*.08,0,s*.09);q.addColorStop(0,stand?"#fdfdf7":"#ffe7b0");q.addColorStop(.5,stand?"#d7e4ea":"#f2c76f");q.addColorStop(1,stand?"#8aa2ae":"#b08436");g.fillStyle=q;g.beginPath();g.moveTo(-s*.7,0);g.quadraticCurveTo(-s*.68,-s*.08,0,-s*.08);g.quadraticCurveTo(s*.62,-s*.08,s*.74,-s*.02);g.quadraticCurveTo(s*.6,s*.08,0,s*.08);g.quadraticCurveTo(-s*.66,s*.08,-s*.7,0);g.fill();
 g.strokeStyle="rgba(40,40,40,.5)";g.lineWidth=1.2;g.beginPath();g.moveTo(-s*.6,-s*.01);g.lineTo(s*.6,-s*.03);g.stroke();
 const limb=(pts,w,c)=>{g.strokeStyle=c;g.lineWidth=w;g.beginPath();g.moveTo(pts[0]*s,pts[1]*s);for(let i=2;i<pts.length;i+=2)g.lineTo(pts[i]*s,pts[i+1]*s);g.stroke()};
 if(stand){limb([-.16,-.07,-.1,-.24,-.04,-.36],s*.08,tone(suit,-.3));limb([.16,-.07,.1,-.24,.04,-.36],s*.085,suit);
  q=g.createLinearGradient(-s*.12,0,s*.12,0);q.addColorStop(0,tone(suit,-.35));q.addColorStop(.5,tone(suit,.15));q.addColorStop(1,tone(suit,-.2));g.fillStyle=q;g.beginPath();g.ellipse(0,-s*.52,s*.1,s*.18,-.08,0,7);g.fill();
  limb([-.06,-.62,-.24,-.56,-.4,-.5],s*.055,skinD);limb([.06,-.63,.22,-.7,.38,-.76],s*.055,skin);
  q=g.createRadialGradient(-s*.03,-s*.8,1,0,-s*.78,s*.1);q.addColorStop(0,tone(skin,.2));q.addColorStop(1,skinD);g.fillStyle=q;g.beginPath();g.arc(0,-s*.78,s*.085,0,7);g.fill();
  g.fillStyle="#3b2414";g.beginPath();g.arc(-s*.01,-s*.81,s*.088,Math.PI*.95,Math.PI*2.05);g.fill()}
 else{limb([-.22,-.07,-.05,-.1,.08,-.07],s*.085,tone(suit,-.2));
  q=g.createLinearGradient(0,-s*.4,0,-s*.08);q.addColorStop(0,tone(suit,.15));q.addColorStop(1,tone(suit,-.3));g.fillStyle=q;g.beginPath();g.ellipse(-s*.08,-s*.24,s*.1,s*.16,.35,0,7);g.fill();
  limb([.0,-.3,.16,-.18,.3,-.1],s*.055,skin);
  q=g.createRadialGradient(s*.02,-s*.46,1,s*.03,-s*.44,s*.1);q.addColorStop(0,tone(skin,.2));q.addColorStop(1,skinD);g.fillStyle=q;g.beginPath();g.arc(s*.03,-s*.44,s*.08,0,7);g.fill();
  g.fillStyle="#d8b04a";g.beginPath();g.arc(s*.02,-s*.47,s*.083,Math.PI*.9,Math.PI*2.05);g.fill()}
 /* b54 (realistic surfers, not painted flat): wet wetsuit sheen from the sun side, darker shadow side, hair strands, foam and a soft wake where the board sits in the water */
 g.save();g.globalCompositeOperation="source-atop";q=g.createLinearGradient(-s*.3,-s*.9,s*.3,-s*.1);q.addColorStop(0,"rgba(255,255,255,.18)");q.addColorStop(.45,"rgba(255,255,255,0)");q.addColorStop(1,"rgba(0,10,20,.28)");g.fillStyle=q;g.fillRect(-s*.75,-s*.98,s*1.5,s*.9);g.restore();
 g.strokeStyle="rgba(235,245,255,.35)";g.lineWidth=s*.012;g.beginPath();if(stand){g.moveTo(-s*.07,-s*.66);g.quadraticCurveTo(-s*.1,-s*.52,-s*.06,-s*.38)}else{g.moveTo(-s*.15,-s*.36);g.quadraticCurveTo(-s*.18,-s*.24,-s*.1,-s*.12)}g.stroke();
 g.strokeStyle=stand?"rgba(30,16,8,.55)":"rgba(150,110,30,.6)";g.lineWidth=s*.008;for(let i=0;i<5;i++){const hx=(stand?-.06:-.03)+i*.025,hy=stand?-.86:-.52;g.beginPath();g.moveTo(hx*s,hy*s);g.quadraticCurveTo((hx-.02)*s,(hy+.04)*s,(hx-.035)*s,(hy+.08)*s);g.stroke()}
 q=g.createLinearGradient(0,s*.02,0,s*.12);q.addColorStop(0,"rgba(240,250,255,.75)");q.addColorStop(1,"rgba(240,250,255,0)");g.fillStyle=q;g.beginPath();g.ellipse(0,s*.06,s*.78,s*.05,0,0,7);g.fill();
 g.fillStyle="rgba(255,255,255,.8)";for(let i=0;i<9;i++){const x=(-.72+i*.18)*s;g.beginPath();g.ellipse(x,s*.05,s*(.03+(i%3)*.012),s*.014,0,0,7);g.fill()}}
// v8 shark art: realistic side silhouette, no cartoon outline. Origin: shark centre = canvas centre + (L*.05, 0)
// ---- deep creatures + plankton (shaded, cheap glow baked into the sprite once) ----
function drawPlankton(g,s,col){g.shadowColor=col;g.shadowBlur=s*.25;const gr=g.createRadialGradient(-s*.06,-s*.06,1,0,0,s*.3);gr.addColorStop(0,"#ffffff");gr.addColorStop(.35,col);gr.addColorStop(1,tone(col,-.45));g.fillStyle=gr;g.beginPath();g.ellipse(0,0,s*.3,s*.22,0,0,7);g.fill();g.shadowBlur=0;
 g.fillStyle=tone(col,.5);for(const [x,y,r] of[[-.42,-.12,.07],[.4,.16,.06],[-.2,.3,.05],[.25,-.28,.05]]){g.beginPath();g.arc(x*s,y*s,r*s,0,7);g.fill()}}
function drawAngler(g,s){const body="#3b3346",hi="#6a5d78",dk="#17121d";g.lineJoin="round";
 // lure stalk + bulb (baked glow)
 g.strokeStyle="#5b4d68";g.lineWidth=s*.035;g.lineCap="round";g.beginPath();g.moveTo(s*.05,-s*.3);g.quadraticCurveTo(s*.25,-s*.78,s*.6,-s*.58);g.stroke();
 g.shadowColor="#fff4a0";g.shadowBlur=s*.45;g.fillStyle="#fffbd0";g.beginPath();g.arc(s*.6,-s*.56,s*.075,0,7);g.fill();g.shadowBlur=s*.2;g.fill();g.shadowBlur=0;
 // tail + fins
 g.fillStyle=dk;g.beginPath();g.moveTo(-s*.32,0);g.lineTo(-s*.72,-s*.24);g.quadraticCurveTo(-s*.62,0,-s*.72,s*.24);g.closePath();g.fill();
 // body
 const gr=g.createRadialGradient(-s*.02,-s*.16,s*.04,0,0,s*.46);gr.addColorStop(0,hi);gr.addColorStop(.55,body);gr.addColorStop(1,dk);g.fillStyle=gr;g.beginPath();g.moveTo(s*.44,-s*.08);g.quadraticCurveTo(s*.34,-s*.4,0,-s*.36);g.quadraticCurveTo(-s*.36,-s*.3,-s*.38,0);g.quadraticCurveTo(-s*.34,s*.28,0,s*.32);g.quadraticCurveTo(s*.34,s*.34,s*.5,s*.1);g.closePath();g.fill();
 // mouth: dark gape + needle teeth
 g.fillStyle="#0a0610";g.beginPath();g.moveTo(s*.47,-s*.06);g.quadraticCurveTo(s*.2,s*.02,s*.12,s*.08);g.quadraticCurveTo(s*.3,s*.2,s*.5,s*.1);g.closePath();g.fill();
 g.fillStyle="#f1ecd8";for(let i=0;i<5;i++){const x=s*(.16+i*.07);g.beginPath();g.moveTo(x,s*(.02-i*.012));g.lineTo(x+s*.02,s*(.1-i*.01));g.lineTo(x+s*.04,s*(.02-i*.012));g.fill();g.beginPath();g.moveTo(x,s*(.14-i*.008));g.lineTo(x+s*.02,s*(.05-i*.008));g.lineTo(x+s*.04,s*(.14-i*.008));g.fill()}
 g.fillStyle="#e8f36a";g.beginPath();g.arc(s*.2,-s*.16,s*.045,0,7);g.fill();g.fillStyle="#000";g.beginPath();g.arc(s*.21,-s*.16,s*.022,0,7);g.fill();
 g.fillStyle="rgba(255,255,255,.12)";g.beginPath();g.ellipse(-s*.04,-s*.22,s*.16,s*.05,-.2,0,7);g.fill()}
function drawOcto(g,s,col){const dk=tone(col,-.5),hi=tone(col,.35);g.lineCap="round";
 // tentacles trail back (left) and down, shaded
 for(let i=0;i<6;i++){const k=i/5,y0=s*(.02+k*.12);g.strokeStyle=i%2?tone(col,-.25):col;g.lineWidth=s*(.085-k*.02);g.beginPath();g.moveTo(-s*.05,y0);g.bezierCurveTo(-s*.3,y0+s*.25,-s*.5,y0-s*.05,-s*(.62+k*.1),y0+s*(.18-k*.08));g.stroke()}
 g.fillStyle=tone(col,.45);for(let i=0;i<5;i++){g.beginPath();g.arc(-s*(.2+i*.08),s*(.27-i*.02),s*.018,0,7);g.fill()}
 // mantle
 const gr=g.createRadialGradient(s*.12,-s*.2,s*.03,s*.05,-s*.08,s*.38);gr.addColorStop(0,hi);gr.addColorStop(.6,col);gr.addColorStop(1,dk);g.fillStyle=gr;g.beginPath();g.ellipse(s*.08,-s*.1,s*.36,s*.27,-.25,0,7);g.fill();
 g.fillStyle="#fff7d8";g.beginPath();g.ellipse(s*.24,s*.04,s*.06,s*.05,0,0,7);g.fill();g.fillStyle="#111";g.fillRect(s*.2,s*.03,s*.08,s*.025);
 g.fillStyle="rgba(255,255,255,.18)";g.beginPath();g.ellipse(s*.08,-s*.24,s*.15,s*.05,-.25,0,7);g.fill()}
function drawStar(g,s,col){const ro=s*.42,ri=s*.18,gr=g.createRadialGradient(-s*.06,-s*.08,s*.02,0,0,ro);gr.addColorStop(0,tone(col,.4));gr.addColorStop(.6,col);gr.addColorStop(1,tone(col,-.4));g.fillStyle=gr;g.beginPath();
 for(let i=0;i<10;i++){const r=i%2?ri:ro,a=-Math.PI/2+i*Math.PI/5;g.lineTo(Math.cos(a)*r,Math.sin(a)*r)}g.closePath();g.fill();
 g.fillStyle=tone(col,.55);for(let i=0;i<5;i++){const a=-Math.PI/2+i*Math.PI*.4;for(const k of[.15,.26]){g.beginPath();g.arc(Math.cos(a)*s*k,Math.sin(a)*s*k,s*.02,0,7);g.fill()}}}
function sideSharkPath(g,L,open,T){const h=L*.2,bl=T&&T.stripe?1:0;g.beginPath();g.moveTo(L*.5,h*.05);
 if(T&&T.hammer){g.lineTo(L*.5,-h*.25);g.lineTo(L*.48,-h*.68);g.lineTo(L*.42,-h*.72);g.bezierCurveTo(L*.36,-h*.62,L*.3,-h*.6,L*.2,-h*.68)}
 else g.bezierCurveTo(L*(.48-bl*.01),-h*(.3+bl*.18),L*.36,-h*.6,L*.2,-h*.68);
 g.bezierCurveTo(L*.14,-h*.72,L*.1,-h*.74,L*.07,-h*.76);g.bezierCurveTo(L*.02,-h*1.2,-L*.03,-h*1.6,-L*.07,-h*(T&&T.hammer?2.1:1.85));
 g.quadraticCurveTo(-L*.09,-h*1.1,-L*.17,-h*.62);g.bezierCurveTo(-L*.28,-h*.45,-L*.38,-h*.25,-L*.45,-h*.14);
 g.bezierCurveTo(-L*.5,-h*.5,-L*.56,-h*1.0,-L*.64,-h*1.45);g.quadraticCurveTo(-L*.58,-h*.6,-L*.53,-h*.02);
 g.quadraticCurveTo(-L*.57,h*.45,-L*.6,h*(bl?1.1:.85));g.quadraticCurveTo(-L*.52,h*.4,-L*.45,h*.14);
 g.bezierCurveTo(-L*.36,h*.3,-L*.28,h*.42,-L*.22,h*.46);g.bezierCurveTo(-L*.05,h*.64,L*.15,h*.68,L*.3,h*.52);
 if(open){g.lineTo(L*.41,h*.44);g.lineTo(L*.26,h*.2);g.lineTo(L*.47,h*.13)}else g.bezierCurveTo(L*.4,h*.44,L*.47,h*.26,L*.5,h*.05);g.closePath()}
// pre-rendered once per size/type: countershaded gradient, depth shading toward the tail, top-light volume highlight, rim light, belly occlusion, baked caustics, gills, fins, glossy eye
// v10 step 1 (Jeremy "start with one realistic great white"): painted-realistic great white side sprite. Original procedural art.
// Same canvas size, origin and silhouette (sideSharkPath) as render3DShark, so bite size, collisions and growth are unchanged. Baked once per build.
function renderGW(L,open,T){const h=L*.2,pad=L*.12,c=mk(L*1.3+pad*2,h*4.6+pad*2),g=c.getContext("2d");const ox=c.width/2+L*.05,oy=c.height*.56;g.translate(ox,oy);g.lineJoin="round";
 let sd=1234567;const rnd=()=>(sd=(sd*16807)%2147483647)/2147483647;// seeded: same shark every build
 const back="#3b4c5c",mid="#6c7e8d",belly="#eef0ee",deep="#1d2833";
 const fin=(pts,c0,c1,edge)=>{g.beginPath();g.moveTo(L*pts[0],h*pts[1]);g.quadraticCurveTo(L*pts[2],h*pts[3],L*pts[4],h*pts[5]);g.quadraticCurveTo(L*pts[6],h*pts[7],L*pts[8],h*pts[9]);g.closePath();const fg=g.createLinearGradient(L*pts[0],h*pts[1],L*pts[4],h*pts[5]);fg.addColorStop(0,c0);fg.addColorStop(.75,c1);fg.addColorStop(1,edge||c1);g.fillStyle=fg;g.fill()};
 fin([.24,.3,.2,.9,.13,1.3,.15,.8,.12,.4],"#2a3743","#0e151c");// far pectoral, in shadow
 const P=()=>sideSharkPath(g,L,open,T);
 P();let q=g.createLinearGradient(0,-h*.9,0,h*.7);q.addColorStop(0,deep);q.addColorStop(.25,back);q.addColorStop(.48,mid);q.addColorStop(.6,"#a9b3ba");q.addColorStop(1,"#c9cfd2");g.fillStyle=q;g.fill();
 g.save();P();g.clip();
 // countershading: sharp, irregular line typical of great whites, dipping behind the pectoral and rising to the tail
 const cl=x=>h*(.16+(x<-.15?(-.15-x)*.55:0)-(x>.3?(x-.3)*.6:0)+Math.sin(x*61)*.03+Math.sin(x*23+1)*.035+Math.sin(x*9)*.02);
 g.beginPath();g.moveTo(L*.55,cl(.55));for(let x=.55;x>=-.7;x-=.01)g.lineTo(L*x,cl(x));g.lineTo(-L*.7,h*2);g.lineTo(L*.6,h*2);g.closePath();
 q=g.createLinearGradient(0,h*.05,0,h*.7);q.addColorStop(0,belly);q.addColorStop(.7,"#e2e6e6");q.addColorStop(1,"#b8c2c8");g.fillStyle=q;g.fill();
 g.strokeStyle="rgba(20,30,40,.35)";g.lineWidth=Math.max(1,L*.004);g.beginPath();for(let x=.55;x>=-.7;x-=.01)x>.549?g.moveTo(L*x,cl(x)):g.lineTo(L*x,cl(x));g.stroke();
 // skin grain: mottled noise baked at reduced resolution then scaled (soft, painterly), multiplied on
 const nw=Math.max(16,Math.ceil(L*.35)),nh=Math.max(8,Math.ceil(nw*.5)),nc=mk(nw,nh),ng=nc.getContext("2d"),id=ng.createImageData(nw,nh);
 for(let i=0;i<id.data.length;i+=4){const v=200+rnd()*55;id.data[i]=v;id.data[i+1]=v;id.data[i+2]=v+4;id.data[i+3]=255}ng.putImageData(id,0,0);
 g.globalCompositeOperation="multiply";g.globalAlpha=.55;g.imageSmoothingEnabled=true;g.drawImage(nc,-L*.7,-h*2,L*1.3,h*3.2);
 // larger blotches (dermal mottling) on the back
 for(let i=0;i<70;i++){const x=L*(rnd()*1.1-.6),y=-h*(.15+rnd()*.7),r=L*(.008+rnd()*.025);g.globalAlpha=.06+rnd()*.08;g.fillStyle=rnd()<.5?"#24313c":"#55687a";g.beginPath();g.ellipse(x,y,r*1.6,r,rnd()*.4-.2,0,7);g.fill()}
 g.globalCompositeOperation="source-over";g.globalAlpha=1;
 // fine dermal-denticle streaks along the flank (follow body flow)
 g.lineWidth=Math.max(.5,L*.0022);for(let i=0;i<120;i++){const x=L*(rnd()*1.05-.55),y=-h*(rnd()*.75-.05),len=L*(.015+rnd()*.04);g.strokeStyle=rnd()<.5?"rgba(255,255,255,.07)":"rgba(0,10,20,.09)";g.beginPath();g.moveTo(x,y);g.lineTo(x-len,y+len*.05);g.stroke()}
 // scars: a few pale healed scratches + one bite-crescent behind the gills
 g.lineCap="round";const scar=(x0,y0,x1,y1,w)=>{g.lineWidth=w*1.8;g.strokeStyle="rgba(15,22,30,.25)";g.beginPath();g.moveTo(x0,y0+w*.6);g.quadraticCurveTo((x0+x1)/2,(y0+y1)/2-w*2,x1,y1+w*.6);g.stroke();g.lineWidth=w;g.strokeStyle="rgba(225,232,236,.55)";g.beginPath();g.moveTo(x0,y0);g.quadraticCurveTo((x0+x1)/2,(y0+y1)/2-w*2,x1,y1);g.stroke()};
 const sw=Math.max(1,L*.005);scar(L*.12,-h*.55,L*.02,-h*.3,sw);scar(L*.08,-h*.5,-L*.01,-h*.28,sw*.8);scar(-L*.12,-h*.45,-L*.24,-h*.32,sw*.9);scar(L*.32,-h*.42,L*.27,-h*.2,sw*.7);
 g.lineWidth=sw;g.strokeStyle="rgba(225,232,236,.4)";for(let i=0;i<5;i++){g.beginPath();g.arc(-L*.02,-h*.05,L*(.035+i*.006),-2.4,-1.2);g.stroke()}g.lineCap="butt";
 // light from above (surface), shadow towards tail and underside
 q=g.createLinearGradient(0,-h*1.2,0,h*.7);q.addColorStop(0,"rgba(190,220,240,.22)");q.addColorStop(.35,"rgba(190,220,240,0)");q.addColorStop(.8,"rgba(0,10,25,0)");q.addColorStop(1,"rgba(0,10,25,.4)");g.fillStyle=q;g.fillRect(-L,-h*3,L*2,h*6);
 q=g.createLinearGradient(L*.5,0,-L*.65,0);q.addColorStop(0,"rgba(0,8,18,0)");q.addColorStop(.6,"rgba(0,8,18,.12)");q.addColorStop(1,"rgba(0,8,18,.5)");g.fillStyle=q;g.fillRect(-L,-h*3,L*2,h*6);
 // rounded-body rim shading (dark top edge, soft reflected light lower)
 g.save();g.translate(0,-h*.1);g.lineWidth=h*.16;g.strokeStyle="rgba(8,16,24,.3)";P();g.stroke();g.restore();
 g.save();g.translate(0,h*.08);g.lineWidth=h*.08;g.strokeStyle="rgba(170,200,220,.22)";P();g.stroke();g.restore();
 // snout: lighter conical tip, ampullae pores
 q=g.createRadialGradient(L*.47,-h*.05,0,L*.47,-h*.05,L*.08);q.addColorStop(0,"rgba(170,185,195,.35)");q.addColorStop(1,"rgba(170,185,195,0)");g.fillStyle=q;g.fillRect(L*.3,-h,L*.3,h*1.5);
 g.fillStyle="rgba(10,18,26,.4)";for(let i=0;i<22;i++){g.beginPath();g.arc(L*(.4+rnd()*.09),-h*(rnd()*.35-.05),Math.max(.5,L*.0028),0,7);g.fill()}
 g.restore();
 // five gill slits: dark deep groove with a pale lower lip, slightly curved
 for(let i=0;i<5;i++){const x=L*(.27-i*.028),t=h*(.0+i*.01);g.lineCap="round";g.lineWidth=Math.max(1,L*.0075);g.strokeStyle="rgba(8,14,20,.65)";g.beginPath();g.moveTo(x,-h*.3+t);g.quadraticCurveTo(x-L*.014,h*.04,x-L*.004,h*.32-t);g.stroke();g.lineWidth=Math.max(.6,L*.003);g.strokeStyle="rgba(230,236,240,.28)";g.beginPath();g.moveTo(x+L*.006,-h*.26+t);g.quadraticCurveTo(x-L*.007,h*.05,x+L*.002,h*.3-t);g.stroke();g.lineCap="butt"}
 // fins: soft gradient, darker trailing edge, pale-tipped underside of pectoral
 fin([.17,.32,.13,.9,.0,1.5,.07,.85,.05,.4],"#56697a","#2a3946","#141d25");
 g.strokeStyle="rgba(0,0,0,.25)";g.lineWidth=Math.max(1,L*.004);g.beginPath();g.moveTo(L*.0,h*1.5);g.quadraticCurveTo(L*.07,h*.85,L*.05,h*.4);g.stroke();
 fin([-.25,.42,-.28,.7,-.32,.8,-.31,.55,-.32,.38],"#6b7b88","#2c3a46");fin([-.33,-.3,-.35,-.5,-.37,-.55,-.37,-.4,-.39,-.24],"#3a4a58","#1a242d");
 // eye: small, black, round, no cartoon highlight, slight socket
 const ex=L*.37,ey=-h*.26;q=g.createRadialGradient(ex,ey,0,ex,ey,L*.028);q.addColorStop(0,"rgba(10,16,22,.5)");q.addColorStop(1,"rgba(10,16,22,0)");g.fillStyle=q;g.beginPath();g.arc(ex,ey,L*.028,0,7);g.fill();
 g.fillStyle="#030507";g.beginPath();g.ellipse(ex,ey,L*.011,L*.0095,0,0,7);g.fill();g.fillStyle="rgba(150,180,200,.35)";g.beginPath();g.arc(ex+L*.003,ey-L*.003,Math.max(.6,L*.0025),0,7);g.fill();
 if(open){// pink gums, dark throat, ivory serrated triangular teeth (no gore)
  g.save();P();g.clip();{const mg=g.createLinearGradient(L*.46,0,L*.26,0);mg.addColorStop(0,"#4a1a1e");mg.addColorStop(.35,"#24090c");mg.addColorStop(1,"#0a0304");g.fillStyle=mg}g.beginPath();g.moveTo(L*.41,h*.44);g.lineTo(L*.26,h*.2);g.lineTo(L*.47,h*.13);g.closePath();g.fill();/* v10 item 12: dark realistic mouth: deep throat, dark gums */g.strokeStyle="rgba(90,30,34,.8)";g.lineWidth=Math.max(1,h*.04);g.beginPath();g.moveTo(L*.47,h*.14);g.lineTo(L*.29,h*.2);g.moveTo(L*.41,h*.44);g.lineTo(L*.28,h*.24);g.stroke();g.restore();
  g.fillStyle="#c9c0a8";for(let i=0;i<7;i++){const u=i/7,x=L*(.46-u*.18),y=h*(.14+u*.06);g.beginPath();g.moveTo(x,y);g.lineTo(x-L*.009,y+h*.12*(1-u*.4));g.lineTo(x-L*.02,y+u*h*.01);g.closePath();g.fill()}
  for(let i=0;i<6;i++){const u=i/6,x=L*(.4-u*.12),y=h*(.43-u*.2);g.beginPath();g.moveTo(x,y);g.lineTo(x-L*.008,y-h*.09);g.lineTo(x-L*.017,y-h*.01);g.closePath();g.fill()}}
 else{g.strokeStyle="rgba(5,10,16,.55)";g.lineWidth=Math.max(1,L*.006);g.beginPath();g.moveTo(L*.46,h*.28);g.quadraticCurveTo(L*.38,h*.4,L*.29,h*.36);g.stroke();
  g.fillStyle="rgba(235,230,215,.7)";for(let i=0;i<4;i++){const x=L*(.43-i*.03);g.beginPath();g.moveTo(x,h*(.31+i*.02));g.lineTo(x-L*.005,h*(.36+i*.02));g.lineTo(x-L*.01,h*(.32+i*.02));g.closePath();g.fill()}}
 P();g.lineWidth=Math.max(1,L*.004);g.strokeStyle="rgba(4,10,18,.4)";g.stroke();
 c.L=L;return c}
function render3DShark(L,open,T){T=T||TYPES.white;if(T.name==="Great White"&&!/[?&]oldgw/.test(location.search))return renderGW(L,open,T);const h=L*.2,pad=L*.12,c=mk(L*1.3+pad*2,h*4.6+pad*2),g=c.getContext("2d");g.translate(c.width/2+L*.05,c.height*.56);g.lineJoin="round";
 const fin=(pts,c0,c1)=>{g.beginPath();g.moveTo(L*pts[0],h*pts[1]);g.quadraticCurveTo(L*pts[2],h*pts[3],L*pts[4],h*pts[5]);g.quadraticCurveTo(L*pts[6],h*pts[7],L*pts[8],h*pts[9]);g.closePath();const fg=g.createLinearGradient(L*pts[0],h*pts[1],L*pts[4],h*pts[5]);fg.addColorStop(0,c0);fg.addColorStop(1,c1);g.fillStyle=fg;g.fill()};
 fin([.24,.3,.2,.9,.13,1.3,.15,.8,.12,.4],T.ext,"#0c1218");// far pectoral (behind body)
 sideSharkPath(g,L,open,T);const gr=g.createLinearGradient(0,-h*.8,0,h*.68);gr.addColorStop(0,T.ext);gr.addColorStop(.22,T.body);gr.addColorStop(.47,T.hi);gr.addColorStop(.53,T.belly);gr.addColorStop(.8,T.belly);gr.addColorStop(1,"#7f8b96");g.fillStyle=gr;g.fill();
 g.save();sideSharkPath(g,L,open,T);g.clip();
 if(T.stripe){g.fillStyle=T.stripe;for(let i=0;i<14;i++){const x=-L*.5+i*L*.06;g.globalAlpha=(T.barA||.5)*(.4+.6*i/14);g.beginPath();g.ellipse(x,-h*.3,L*.01,h*.34,.12,0,7);g.fill();g.beginPath();g.ellipse(x+L*.03,-h*.05,L*.007,h*.16,.12,0,7);g.fill()}g.globalAlpha=1}
 let q=g.createLinearGradient(L*.5,0,-L*.65,0);q.addColorStop(0,"rgba(0,8,16,0)");q.addColorStop(.55,"rgba(0,8,16,.1)");q.addColorStop(1,"rgba(0,8,16,.5)");g.fillStyle=q;g.fillRect(-L,-h*3,L*2,h*6);
 q=g.createRadialGradient(L*.16,-h*.45,0,L*.16,-h*.45,L*.38);q.addColorStop(0,"rgba(210,235,255,.16)");q.addColorStop(.45,"rgba(255,255,255,.1)");q.addColorStop(1,"rgba(255,255,255,0)");g.fillStyle=q;g.fillRect(-L,-h*3,L*2,h*6);
 g.strokeStyle="rgba(200,240,255,.16)";g.lineWidth=Math.max(1,L*.006);for(let i=0;i<5;i++){const y=-h*(.75-i*.12);g.beginPath();g.moveTo(-L*.45,y);for(let x=-.45;x<.5;x+=.06)g.lineTo(L*x,y+Math.sin(x*40+i*2)*h*.05);g.stroke()}
 g.save();g.translate(0,h*.07);g.lineWidth=h*.09;g.strokeStyle="rgba(200,238,255,.42)";sideSharkPath(g,L,open,T);g.stroke();g.restore();
 g.save();g.translate(0,-h*.09);g.lineWidth=h*.14;g.strokeStyle="rgba(10,20,30,.28)";sideSharkPath(g,L,open,T);g.stroke();g.restore();
 g.fillStyle="rgba(255,255,255,.3)";g.beginPath();g.ellipse(L*.17,-h*.5,L*.15,h*.045,-.08,0,7);g.fill();
 // countershading: a crisp, slightly ragged line between the dark back and the white belly (great white's hallmark)
 g.fillStyle=T.belly;g.beginPath();g.moveTo(L*.52,h*.1);for(let x=.5;x>=-.66;x-=.02)g.lineTo(L*x,h*(.12+(x<-.2?(-.2-x)*.5:0)+Math.sin(x*55)*.035+Math.sin(x*17)*.03));g.lineTo(-L*.7,h*2);g.lineTo(L*.6,h*2);g.closePath();g.globalAlpha=T.stripe?.55:.92;g.fill();g.globalAlpha=1;
 q=g.createLinearGradient(0,h*.1,0,h*.7);q.addColorStop(0,"rgba(0,0,0,0)");q.addColorStop(1,"rgba(60,80,100,.3)");g.fillStyle=q;g.fillRect(-L,h*.1,L*2,h);
 // sun dappling (caustic net) on the back, baked once
 g.strokeStyle="rgba(220,245,255,.2)";g.lineWidth=Math.max(1,L*.004);for(let i=0;i<14;i++){const x0=L*(.35-i*.06);g.beginPath();g.moveTo(x0,-h*.85);g.quadraticCurveTo(x0-L*.03,-h*.4,x0+L*.01,h*.05);g.stroke()}
 g.restore();
 if(T.hammer){// cephalofoil: the flat T-head seen side-on as a thin blade sweeping up-forward, eye at its tip
  const hd=()=>{g.beginPath();g.moveTo(L*.36,-h*.6);g.quadraticCurveTo(L*.5,-h*1.05,L*.555,-h*1.0);g.quadraticCurveTo(L*.58,-h*.85,L*.55,-h*.7);g.quadraticCurveTo(L*.52,-h*.45,L*.5,-h*.05);g.closePath()};hd();const hg=g.createLinearGradient(L*.4,-h*1.05,L*.5,0);hg.addColorStop(0,T.ext);hg.addColorStop(.6,T.body);hg.addColorStop(1,T.hi);g.fillStyle=hg;g.fill();g.strokeStyle="rgba(4,12,22,.55)";g.lineWidth=Math.max(1,L*.006);g.stroke();
  g.fillStyle="#05080b";g.beginPath();g.arc(L*.548,-h*.86,L*.012,0,7);g.fill();g.fillStyle="rgba(255,255,255,.8)";g.beginPath();g.arc(L*.551,-h*.88,L*.004,0,7);g.fill()}
 for(let i=0;i<5;i++){const x=L*(.25-i*.027);g.lineWidth=Math.max(1,L*.006);g.strokeStyle="rgba(5,12,20,.5)";g.beginPath();g.moveTo(x,-h*.22);g.quadraticCurveTo(x-L*.012,h*.04,x-L*.004,h*.3);g.stroke();g.strokeStyle="rgba(255,255,255,.14)";g.beginPath();g.moveTo(x+L*.005,-h*.2);g.quadraticCurveTo(x-L*.007,h*.04,x+L*.001,h*.28);g.stroke()}
 fin(T.hammer?[.17,.32,.12,1.1,-.06,1.9,.06,.95,.05,.4]:[.17,.32,.13,.9,.0,1.5,.07,.85,.05,.4],T.body,T.ext);fin([-.25,.42,-.28,.7,-.32,.8,-.31,.55,-.32,.38],T.body,T.ext);fin([-.33,-.3,-.35,-.5,-.37,-.55,-.37,-.4,-.39,-.24],T.body,T.ext);
 const ex=L*.37,ey=-h*.26;if(!T.hammer){g.fillStyle="#05080b";g.beginPath();g.ellipse(ex,ey,L*.017,L*.014,0,0,7);g.fill();g.fillStyle="rgba(255,255,255,.85)";g.beginPath();g.arc(ex+L*.005,ey-L*.005,L*.0055,0,7);g.fill();}
 if(open){g.fillStyle="#1a080a";g.beginPath();g.moveTo(L*.47,h*.14);g.lineTo(L*.27,h*.21);g.lineTo(L*.42,h*.42);g.closePath();g.fill();g.fillStyle="#c9c0a8";for(let i=0;i<6;i++){const u=i/6,x=L*(.45-u*.17),y=h*(.15+u*.06);g.beginPath();g.moveTo(x,y);g.lineTo(x-L*.012,y+h*.13);g.lineTo(x-L*.024,y+u*h*.01);g.closePath();g.fill()}}
 else{g.strokeStyle="rgba(5,12,20,.45)";g.lineWidth=Math.max(1,L*.006);g.beginPath();g.moveTo(L*.45,h*.3);g.quadraticCurveTo(L*.38,h*.4,L*.29,h*.36);g.stroke()}
 sideSharkPath(g,L,open,T);g.lineWidth=Math.max(1,L*.006);g.strokeStyle="rgba(4,12,22,.55)";g.stroke();
 c.L=L;return c}
function render3DTitle(w){const fs=Math.floor(w*.17),c=mk(w,fs*2.7),g=c.getContext("2d");g.textAlign="center";g.textBaseline="middle";g.font=`900 ${fs}px system-ui,"Arial Black",sans-serif`;g.lineJoin="round";
 const lines=[["SHARK",fs*.85],["ATTACK",fs*1.95]];
 for(const [t,y] of lines){g.fillStyle="rgba(0,20,40,.3)";g.fillText(t,w/2+fs*.12,y+fs*.16);
  for(let i=8;i>0;i--){g.fillStyle=i>1?"#a3271f":P.ink;g.fillText(t,w/2+i*fs*.012,y+i*fs*.012)}
  g.lineWidth=fs*.09;g.strokeStyle=P.ink;g.strokeText(t,w/2,y);
  const gr=g.createLinearGradient(0,y-fs*.5,0,y+fs*.5);gr.addColorStop(0,"#fff27a");gr.addColorStop(.5,"#ffcc33");gr.addColorStop(.51,"#ff9f1c");gr.addColorStop(1,"#f06a12");g.fillStyle=gr;g.fillText(t,w/2,y);
  g.save();g.globalCompositeOperation="source-atop";g.fillStyle="rgba(255,255,255,.35)";g.fillRect(0,y-fs*.45,w,fs*.18);g.restore()}
 return c}
// head-on shark for the intro: mouth WIDE open toward the viewer (open) or snapped shut (closed). Pre-rendered once.
/* b51: head-on shark redrawn in the shaded style of the side-view shark: dark grey back fading to a white belly, conical snout, black eyes,
   uneven serrated teeth (no outlines), shaded throat, no gills. Our own drawing in code. Sprite box: x ±320k, y -215k..233k (k=S/400). */
function renderFrontShark(S,open){const k=S/400,c=mk(S*1.6,S*1.12),g=c.getContext("2d");g.translate(c.width/2,215*k);g.transform(.95,.035,-.07,1,0,0);/* b53 t1365u: 3/4 foreshortened head (near side = viewer right) */g.lineJoin="round";g.lineCap="round";
 let sd=7;const rnd=()=>{sd=(sd*16807)%2147483647;return sd/2147483647};
 /* b54 (QA cce8e18 "half-cartoon", Skeptic, Jeremy via Eve): realistic great-white head, own art drawn in code. Narrow conical snout, straighter flanks (no bell),
    small crescent mouth well below the snout, uneven teeth in rows with gaps, rough skin texture + scars, ragged countershading, triangular dorsal fin with a curved trailing edge. */
 const head=()=>{g.beginPath();g.moveTo(0,-214*k);g.quadraticCurveTo(12*k,-213*k,22*k,-202*k);g.bezierCurveTo(60*k,-160*k,128*k,-100*k,176*k,-52*k);g.bezierCurveTo(204*k,-22*k,214*k,40*k,206*k,104*k);g.bezierCurveTo(196*k,150*k,150*k,192*k,0,204*k);g.bezierCurveTo(-150*k,192*k,-196*k,150*k,-206*k,104*k);g.bezierCurveTo(-214*k,40*k,-204*k,-22*k,-176*k,-52*k);g.bezierCurveTo(-128*k,-100*k,-60*k,-160*k,-22*k,-202*k);g.quadraticCurveTo(-12*k,-213*k,0,-214*k);g.closePath()};
 // dorsal fin behind the head: straight leading edge, sharp apex, concave (curved) trailing edge
 {const dg=g.createLinearGradient(60*k,-200*k,190*k,-110*k);dg.addColorStop(0,"#222c34");dg.addColorStop(1,"#3a4650");g.fillStyle=dg;g.beginPath();g.moveTo(36*k,-176*k);g.lineTo(128*k,-214*k);g.quadraticCurveTo(116*k,-168*k,176*k,-118*k);g.closePath();g.fill();
  g.strokeStyle="rgba(200,212,220,.18)";g.lineWidth=1.5*k;g.beginPath();g.moveTo(40*k,-177*k);g.lineTo(126*k,-212*k);g.stroke()}
 // pectoral fins behind the head
 for(const s of[-1,1]){const fg=g.createLinearGradient(s*150*k,90*k,s*318*k,232*k);fg.addColorStop(0,"#3a4651");fg.addColorStop(.7,"#27313a");fg.addColorStop(1,"#1a222a");g.fillStyle=fg;g.beginPath();g.moveTo(s*150*k,60*k);g.bezierCurveTo(s*236*k,92*k,s*290*k,150*k,s*318*k,232*k);g.bezierCurveTo(s*268*k,200*k,s*206*k,162*k,s*136*k,120*k);g.closePath();g.fill();
  g.fillStyle="rgba(225,232,236,.28)";g.beginPath();g.moveTo(s*160*k,132*k);g.bezierCurveTo(s*214*k,166*k,s*262*k,198*k,s*312*k,228*k);g.bezierCurveTo(s*252*k,214*k,s*198*k,190*k,s*138*k,150*k);g.closePath();g.fill()}
 // body: matte grey back, ragged line to an off-white belly (countershading)
 head();let gr=g.createLinearGradient(0,-200*k,0,60*k);gr.addColorStop(0,"#2a343d");gr.addColorStop(.55,"#46525d");gr.addColorStop(1,"#56626c");g.fillStyle=gr;g.fill();
 g.save();head();g.clip();
 {gr=g.createLinearGradient(0,10*k,0,206*k);gr.addColorStop(0,"#d9dddd");gr.addColorStop(.6,"#e6e8e6");gr.addColorStop(1,"#aab2b8");g.fillStyle=gr;g.beginPath();g.moveTo(-250*k,40*k);for(let i=0;i<=40;i++){const x=-240*k+i*12*k,ax=Math.abs(x)/(240*k);g.lineTo(x,(-2+ax*ax*58+(rnd()-.5)*4+Math.sin(i*.9)*3)*k)}g.lineTo(250*k,240*k);g.lineTo(-250*k,240*k);g.closePath();g.fill()}
 // skin texture: fine mottling (dark + light flecks), no gloss
 for(let i=0;i<900;i++){const x=(rnd()-.5)*430*k,y=(rnd()*430-215)*k,r=(.6+rnd()*1.8)*k;g.fillStyle=rnd()<.55?"rgba(8,14,20,"+(.06+rnd()*.12)+")":"rgba(230,236,240,"+(.04+rnd()*.08)+")";g.fillRect(x,y,r*1.6,r)}
 for(let i=0;i<40;i++){const x=(rnd()-.5)*400*k,y=(rnd()*230-200)*k;g.fillStyle="rgba(10,16,22,"+(.03+rnd()*.04)+")";g.beginPath();g.ellipse(x,y,(4+rnd()*9)*k,(2+rnd()*4)*k,rnd()*3,0,7);g.fill()}
 // scars: thin pale scratches with a dark edge (old bite marks)
 for(const [x0,y0,x1,y1] of [[60,-120,104,-84],[70,-112,110,-80],[-120,-40,-84,-6],[118,10,150,44],[-40,-170,-18,-150]]){g.strokeStyle="rgba(5,10,14,.35)";g.lineWidth=2.6*k;g.beginPath();g.moveTo(x0*k,y0*k);g.quadraticCurveTo((x0+x1)/2*k+4*k,(y0+y1)/2*k-4*k,x1*k,y1*k);g.stroke();g.strokeStyle="rgba(214,222,226,.55)";g.lineWidth=1.2*k;g.beginPath();g.moveTo(x0*k,y0*k-1*k);g.quadraticCurveTo((x0+x1)/2*k+4*k,(y0+y1)/2*k-5*k,x1*k,y1*k-1*k);g.stroke()}
 // form shading: rounded sides fall into shadow, soft light from above on the snout (matte, not a gloss spot)
 gr=g.createRadialGradient(0,-40*k,70*k,0,-10*k,240*k);gr.addColorStop(0,"rgba(0,0,0,0)");gr.addColorStop(.6,"rgba(4,12,20,.2)");gr.addColorStop(1,"rgba(4,12,20,.7)");g.fillStyle=gr;g.fillRect(-220*k,-220*k,440*k,440*k);
 gr=g.createLinearGradient(0,-214*k,0,-60*k);gr.addColorStop(0,"rgba(150,170,185,.22)");gr.addColorStop(1,"rgba(150,170,185,0)");g.fillStyle=gr;g.fillRect(-220*k,-214*k,440*k,160*k);
 g.restore();
 g.save();head();g.clip();gr=g.createLinearGradient(-230*k,0,40*k,0);gr.addColorStop(0,"rgba(2,8,14,.45)");gr.addColorStop(1,"rgba(2,8,14,0)");g.fillStyle=gr;g.fillRect(-240*k,-220*k,280*k,440*k);g.restore();/* far side darker */
 // gill slits on the sides
 g.save();head();g.clip();for(const s of[-1,1])for(let i=0;i<5;i++){const a=s>0?1:.6,gx=s*(150+i*11)*k,gy=(4+i*6)*k;g.strokeStyle="rgba(140,156,168,"+(.45*a)+")";g.lineWidth=5*k;g.beginPath();g.moveTo(gx+s*2*k,gy);g.quadraticCurveTo(gx+s*10*k,gy+30*k,gx+s*5*k,gy+58*k);g.stroke();g.strokeStyle="rgba(4,8,12,"+(.8*a)+")";g.lineWidth=2.6*k;g.beginPath();g.moveTo(gx,gy);g.quadraticCurveTo(gx+s*8*k,gy+30*k,gx+s*3*k,gy+56*k);g.stroke()}g.restore();
 // nostrils + ampullae pores on the snout
 for(const s of[-1,1]){g.fillStyle="rgba(8,12,18,.6)";g.beginPath();g.ellipse(s*30*k,-150*k,9*k,2.6*k,-s*.8,0,7);g.fill();for(let i=0;i<14;i++){g.fillStyle="rgba(6,10,14,.35)";g.beginPath();g.arc(s*(12+rnd()*70)*k,(-190+rnd()*90)*k,(.8+rnd()*.8)*k,0,7);g.fill()}}
 // eyes: small, black, set far back on the sides, no cartoon shine
 for(const s of[-1,1]){const ex=s*152*k,ey=-60*k;gr=g.createRadialGradient(ex,ey,3*k,ex,ey,20*k);gr.addColorStop(0,"rgba(0,0,0,.4)");gr.addColorStop(1,"rgba(0,0,0,0)");g.fillStyle=gr;g.beginPath();g.arc(ex,ey,20*k,0,7);g.fill();
  g.fillStyle="#030506";g.beginPath();g.ellipse(ex,ey,(s>0?9:6.5)*k,8.5*k,s*.6,0,7);g.fill();g.fillStyle="rgba(170,190,205,.35)";g.beginPath();g.ellipse(ex-s*3*k,ey-4*k,1.6*k,1.1*k,-.5,0,7);g.fill()}
 // tooth: narrow serrated triangle, ivory, no outline
 const tooth=(x,y,len,w,ang,up,dim)=>{g.save();g.translate(x,y);g.rotate(ang);const d=up?-1:1,n=6;g.beginPath();g.moveTo(-w/2,0);
  for(let i=1;i<=n;i++){const f=i/n,px=-w/2*(1-f)+(i%2?-.5*k:.5*k)*(1-f),py=d*len*f;g.lineTo(px,py)}
  for(let i=n-1;i>=0;i--){const f=i/n,px=w/2*(1-f)+(i%2?.5*k:-.5*k)*(1-f),py=d*len*f;g.lineTo(px,py)}g.closePath();
  const tg=g.createLinearGradient(0,0,0,d*len);tg.addColorStop(0,dim?"#7d725f":"#b3a68a");tg.addColorStop(.4,dim?"#bdb4a0":"#e4dccb");tg.addColorStop(1,dim?"#d2cab8":"#f7f2e6");g.fillStyle=tg;g.fill();
  g.fillStyle="rgba(70,50,35,.3)";g.beginPath();g.moveTo(0,0);g.lineTo(w/2,0);g.lineTo(0,d*len);g.closePath();g.fill();g.restore()};
 // mouth: a wide, low crescent (much wider than tall), well under the snout
 const mouth=(t,b,w)=>{g.beginPath();g.moveTo(-w,t+30*k);g.bezierCurveTo(-w*.75,t-2*k,-w*.3,t,0,t);g.bezierCurveTo(w*.3,t,w*.75,t-2*k,w,t+30*k);g.bezierCurveTo(w*.9,b*.8,w*.45,b,0,b);g.bezierCurveTo(-w*.45,b,-w*.9,b*.8,-w,t+30*k);g.closePath()};
 if(open){const mw=158*k,mt=20*k,mb=146*k,topY=x=>mt+Math.pow(Math.abs(x)/mw,2)*28*k,botY=x=>mb-Math.pow(Math.abs(x)/mw,1.6)*(mb-mt-34*k);
  g.save();g.shadowColor="rgba(0,0,0,.6)";g.shadowBlur=10*k;mouth(mt-5*k,mb+6*k,mw+6*k);g.fillStyle="#9c6e70";/* dull gums */g.fill();g.restore();
  mouth(mt,mb,mw);gr=g.createRadialGradient(0,84*k,4*k,0,86*k,120*k);gr.addColorStop(0,"#010000");gr.addColorStop(.45,"#120306");gr.addColorStop(.75,"#3c1014");gr.addColorStop(1,"#8a5558");g.fillStyle=gr;g.fill();
  g.save();mouth(mt,mb,mw);g.clip();
   for(let i=0;i<12;i++){if(rnd()<.2)continue;const x=-mw*.7+i/11*mw*1.4+(rnd()-.5)*8*k;tooth(x,topY(x)+22*k,(9+rnd()*14)*k,(6+rnd()*5)*k,(rnd()-.5)*.5,false,true)}
   for(let i=0;i<10;i++){if(rnd()<.25)continue;const x=-mw*.6+i/9*mw*1.2+(rnd()-.5)*8*k;tooth(x,botY(x)-16*k,(5+rnd()*9)*k,(5+rnd()*4)*k,(rnd()-.5)*.5,true,true)}
  g.restore();
  // front rows: uneven sizes, tilted, with gaps where teeth were shed
  for(let i=0;i<17;i++){const r=rnd();if(r<.15)continue;const u=i/16,x=-mw*.88+u*mw*1.76+(rnd()-.5)*7*k,mid=1-Math.abs(u-.5)*1.5,sz=.5+rnd()*rnd()*1.2,len=(16+mid*26)*k*sz+6*k,w=(9+mid*7)*k*(.7+rnd()*.5);tooth(x,topY(x)+2*k,len,w,(u-.5)*.45+(rnd()-.5)*.35,false,false)}
  for(let i=0;i<14;i++){if(rnd()<.2)continue;const u=i/13,x=-mw*.74+u*mw*1.48+(rnd()-.5)*7*k,mid=1-Math.abs(u-.5)*1.4,sz=.5+rnd()*rnd()*1,len=(14+mid*18)*k*sz+5*k,w=(6+mid*4)*k*(.7+rnd()*.5);tooth(x,botY(x)-2*k,len,w,-(u-.5)*.5+(rnd()-.5)*.3,true,false)}
  g.strokeStyle="rgba(255,200,200,.12)";g.lineWidth=3*k;g.beginPath();g.moveTo(-mw*.6,mt+8*k);g.quadraticCurveTo(0,mt-1*k,mw*.6,mt+8*k);g.stroke()}
 else{/* closed (also the head-on turn frame): small arched mouth line, corners turned DOWN (no smile), a few uneven tooth tips */const w=96*k,yc=52*k,ye=74*k;
  g.strokeStyle="rgba(10,6,8,.85)";g.lineWidth=4*k;g.beginPath();g.moveTo(-w,ye);g.bezierCurveTo(-w*.5,yc,w*.5,yc,w,ye);g.stroke();
  g.strokeStyle="rgba(220,226,228,.25)";g.lineWidth=2*k;g.beginPath();g.moveTo(-w*.9,ye+6*k);g.bezierCurveTo(-w*.45,yc+7*k,w*.45,yc+7*k,w*.9,ye+6*k);g.stroke();
  for(let i=0;i<9;i++){if(rnd()<.35)continue;const u=i/8,x=-w*.7+u*w*1.4,y=yc+5*k+Math.pow(Math.abs(u-.5)*2,2)*(ye-yc-6*k)+1*k;tooth(x,y,(3+rnd()*6)*k,(4+rnd()*3)*k,(u-.5)*.5,false,false)}}
 c.cy=215/448;return c}

// ---------- world ----------
const shark={stun:0,safe:0,x:0,y:0,ang:0,spd:0,lvl:0,L:70,Lt:70,wag:0,chomp:0,meter:0,run:0,air:false,vx:0,vy:0,h:0,sq:0,cool:0,perfect:false,face:1};
const fish=[],surf=[],parts=[],pops=[];
let mode=MODES.includes(LS.getItem(MODE_KEY))?LS.getItem(MODE_KEY):"timed";
let surfersCaught=0;
for(let i=0;i<CREATURES.N;i++)fish.push({x:0,y:0,vx:0,vy:0,ph:Math.random()*6,tier:0,s:16,kind:"fish",pal:0,danger:false,bump:0,chase:0,rest:0,st:""});
for(let i=0;i<N_SURF;i++)surf.push({x:0,vx:0,ph:Math.random()*6,k:i===0?1:0,zip:0});
for(let i=0;i<MAX_PARTS;i++)parts.push({x:0,y:0,vx:0,vy:0,t:0});
for(let i=0;i<6;i++)pops.push({x:0,y:0,t:0,txt:""});
const waves=[];for(let i=0;i<10;i++)waves.push({x:Math.random(),y:Math.random(),w:20+Math.random()*30,sp:.006+Math.random()*.01});
let score=0,timeLeft=ROUND_SECONDS,best=+(LS.getItem(BEST_KEY)||0),elapsed=0,endReason="",shake=0,hintT=0;
let calm=LS.getItem(CALM_KEY)==="1"||matchMedia("(prefers-reduced-motion: reduce)").matches;
const touch={on:false,x:0,y:0,dx:0,dy:0,drive:0};
let bg=null,sprC=null,sprO=null,sprB=null,sprK=null,sprF=null,fishSpr=[],surfSpr=[],title=null,tFront=null,tFrontC=null;
const need=l=>GROW.NEED_BASE*Math.pow(GROW.NEED_RATIO,l);/* b53: bar move per fish = gain / need(lvl) */
const ptsOf=f=>f.kind==="plankton"?1:Math.max(1,Math.round(1+3*f.s/bite()))*(f.kind==="fish"?1:f.kind==="angler"?4:2),growOf=f=>GROW.REL*f.s/bite();
let specSpr=[],camX=0,gradSpr=null,sunSpr=null,decoSpr=null,tiles=[],tileC={x:1e9,y:1e9},plankSpr=[],anglerSpr=null,octoSpr=[],starSpr=[],lureSpr=null,spawnStats={n:0,wrong:0,byKind:{}},depthHintT=0;
let haloSpr=[],worldK=1/GROW.START,sizeK=1,camY=0,WORLD_H=4000,gradW=null,raysSpr=null,fogSpr=null,skySpr=null,floorSpr=null,ventSpr=null,vigSpr=null,gradeSpr=null,bgSpr=null,busy=false,sharkSpr=[],glowSpr=[],deco=[],snow=[],murk=[],fsRot=false;
const depthOf=y=>Math.max(0,Math.min(1,(y-SURF)/(BED-SURF)));
const depthRaw=y=>(y-SURF)/(BED-SURF);
function goneAt(y){if(state!=="play")return false;const d=depthRaw(y),V=VANISH;for(let i=0;i<V.EDGES.length;i++)if(d<V.EDGES[i])return shark.lvl>=V.LVL[i];return false}
const layerOf=y=>{const d=depthRaw(y);return d<LAYERS.TOP?0:d<LAYERS.MID?1:2};
function bandOf(L){const y=d=>SURF+d*(BED-SURF);return L===0?[SURF+6,y(LAYERS.TOP)-2]:L===1?[y(LAYERS.TOP)+2,y(LAYERS.MID)-2]:[y(LAYERS.MID)+2,Infinity]}
// v9: the DRAWN shark grows ×DRAW.STEP per stage up to DRAW.CAP (start 0.2×screen height, cap 1.75× = 0.35×height, so the screen stays playable
// without a camera zoom); the world shrinks only by the rest of the true growth (wK), so relative sizes are unchanged.
const DEEP={GROW:1.2,RAMP:.35,FADE_LVL:6,MAX_W:.45,BIG_W:.35,BIG_N:2,GIANT_P:.07,GIANT_MIN:3.8,GIANT_MAX:5.5,GIANT_MAXW:.6};// v9: deep creatures grow with depth (×1+GROW below the mid layer); rare giants up to ~half the screen for a minnow
const EAT={RATIO:1.3,GRACE:1.5};// v9: a creature this much bigger than your bite EATS you on contact; .87-1.3 = same size (push); smaller = food
const DRAW={BASE:.2,STEP:1,CAP:1,/* b48 (Jeremy): the shark stays the SAME size on screen; growth is shown only by the world shrinking (wK = 1/true size) */EASE:5,POP_S:.4};const drawK=l=>Math.min(DRAW.CAP,Math.pow(DRAW.STEP,l)),wK=l=>drawK(l)/trueGrow(l);
const sharkL=l=>Math.min(W,H)*DRAW.BASE*drawK(l)*trait("size");
const bite=()=>shark.L*.4;
function setWorldK(k){const r=k/worldK;if(r!==1)for(const f of fish)f.s*=r;worldK=k}
const surfK=()=>Math.max(SURFACE.MINK,Math.min(1.8,worldK));
/* b53 (Skeptic B9, late game empty): everything still shrinks as the shark grows, but what you can chase stays readable.
   LATE ramps in from size FROM+1 to FULL+1. Sail boats / cargo ships never draw shorter than SAIL_L / CARGO_L x the shark's length (hit box = drawn size);
   surfers keep shrinking with no floor and stop spawning once they would be under SURF_GONE_PX tall (boats take their place);
   small fish never draw under FISH_PX; the deep water is lifted (LIFT added to the colour) and the deep vignette cut by DARK_CUT so fish show at size 19+. */
const LATE={FROM:5,FULL:9,LIFT:"rgb(20,44,62)",DARK_CUT:.75,FISH_PX:18,SAIL_L:.55,CARGO_L:.85,TANK_L:.95,SURF_GONE_PX:12,N_EARLY:3};/* b53: FROM/FULL are internal levels: the late-game ramp runs from HUD SIZE 6 to HUD SIZE 10 (the cap). b57: TANK_L is the oil tanker's surface floor */
const lateK=()=>Math.max(0,Math.min(1,(shark.lvl-LATE.FROM)/(LATE.FULL-LATE.FROM)));
/* b57: deepest depth reached this round. Sail size, surfer/cargo edibility and tanker spawns follow diveD() = max(this, where you are now),
   so a dive shrinks sails immediately and the zone rules are still in force when you come back up to bite. Lighting uses the current depth only. */
let depthMark=0,lightProbe=false;/* lightProbe: the brightness test reads water, fog and vignette, not a fish or a silhouette sitting on the sample pixel */
function noteDepth(){const d=Math.max(0,depthRaw(shark.y));if(d>depthMark)depthMark=d}
function diveD(){return Math.max(depthMark,BED>SURF?Math.max(0,depthRaw(shark.y)):0)}
function sailDepthK(d){if(d==null)d=diveD();return 1/(1+Math.max(0,d)*SAIL_SHRINK)}/* 1 at the surface, SURFER_SPAN/SAIL_SPAN at ZONE.SURF, keeps falling after that */
function pastSurf(){return diveD()>=ZONE.SURF-1e-6}
function pastCargo(){return diveD()>=ZONE.CARGO-1e-6}
function surfDrawK(s){const k=surfK();if(s.k<2)return k;const SD=SURFERS[s.k],floor=(s.k===4?LATE.TANK_L:s.k===3?LATE.CARGO_L:LATE.SAIL_L)*shark.L/(2*(SD.hw||1));let draw=Math.max(k,floor);if(s.k===2)draw*=sailDepthK();return Math.max(SURFACE.MINK,draw)}/* sail floor is the surface size; depth shrinks it with no new floor */
function fpx(f){const v=f.s*lk(f);if(f.kind==="plankton"||lateK()<=0)return v;if(f.kind==="shark")return rel(f)<0?Math.max(v,LATE.FISH_PX*.4*lateK()):v;/* small food sharks are drawn 2.5x their size: floor 0.4 x 18 -> 18 px long */return Math.max(v,LATE.FISH_PX*lateK())}/* b52: surfers keep shrinking with the world. b57 deep growth scales this same sprite (a blit); chase cap and MAX_BIG still limit how many big ones exist */
// v9c (Jeremy: "the shark the same size but everything else bigger"): every creature except plankton is DRAWN (and touches) LOOK.K x its
// true size f.s; eat/bump/danger is still judged from f.s vs bite() (rel, EAT.RATIO unchanged), so relative sizes keep the same proportions.
// LOOK.MIN: no non-plankton creature spawns smaller than MIN x bite (no tiny fish sitting by the fin). RINGS: no rings around shark/fish.
const LOOK={K:1.25,MIN:.4,SHRINK_FROM:10,SHRINK:.95,FLOOR:.15},lookMin=()=>shark.lvl<=LOOK.SHRINK_FROM?LOOK.MIN:Math.max(LOOK.FLOOR,LOOK.MIN*Math.pow(LOOK.SHRINK,shark.lvl-LOOK.SHRINK_FROM)),RINGS=false;const lk=f=>f.kind==="plankton"?1:LOOK.K;
function fleeK(f){const C=CREATURES,d=Math.max(0,Math.min(1,depthOf(f.y))),lo=C.FLEE_SHALLOW[0]+(C.FLEE_DEEP[0]-C.FLEE_SHALLOW[0])*d,hi=C.FLEE_SHALLOW[1]+(C.FLEE_DEEP[1]-C.FLEE_SHALLOW[1])*d;let k=Math.min(C.FLEE_CAP,lo+(hi-lo)*(f.fu==null?.5:f.fu)+C.FLEE_LVL*shark.lvl);if(f.s/bite()>C.FLEE_NEAR_R)k*=C.FLEE_NEAR_K;return k}// always < 1 = slower than your top speed
function rel(f){if(f.kind==="plankton")return -1;const r=f.s/bite();return r<.87?-1:r>1.15?1:0}// -1 food, 0 same size (bump), 1 danger
const sharkMax=l=>Math.min(W,H)*.75*(1+.04*Math.min(l,SPEED_LVL_CAP))*trait("speed");const SPEED_LVL_CAP=MAX_LEVEL;/* b53 (QA S52-5): top speed rises +4% per size exactly as in b51, all the way to the HUD SIZE 10 cap (1.36x the start, same as b51 at SIZE 10); b52 stopped at SIZE 11. Boost stays 2.2x on top. */
const FISH_PAL=["#ffd23f","#7be04a","#ff7a9c","#5fd0ff","#ff9f1c","#c48bff"],DEEP_PAL=["#6c7fa8","#8a6fb0","#5e8c8a"],GLOW_PAL=["#3dfcff","#ff4fd8","#b6ff3d"];
const SHARK_PALS_OLD=[{body:"#55606e",hi:"#7f8b99",belly:"#cfd6dc",ext:"#1f262e",stripe:null,hammer:false},{body:"#3d4a5c",hi:"#5d6b80",belly:"#b9c2cc",ext:"#141a22",stripe:null,hammer:true},{body:"#2a2f3a",hi:"#4a5162",belly:"#8f97a3",ext:"#0b0e13",stripe:"#5b2a1a",hammer:false}];
function tierOf(sz){return sz<22?0:sz<36?1:sz<54?2:3}
// v10 item 12 (Graphics Lead plan): shared baked textures, made once, applied with source-atop so they stay inside each sprite
let _grain=null,_scale=null;function texGrain(){if(!_grain){_grain=mk(64,64);const g=_grain.getContext("2d"),d=g.createImageData(64,64);let z=1234567;for(let i=0;i<d.data.length;i+=4){z=(z*1103515245+12345)&0x7fffffff;const v=z%2?255:0;d.data[i]=d.data[i+1]=d.data[i+2]=v;d.data[i+3]=((z>>8)%160)+40}g.putImageData(d,0,0)}return _grain}
function texScale(){if(!_scale){_scale=mk(12,8);const g=_scale.getContext("2d");g.strokeStyle="rgba(0,0,0,.9)";g.lineWidth=1;for(const [x,y] of[[0,0],[6,4],[12,0],[0,8],[12,8]]){g.beginPath();g.arc(x,y,4.5,0,Math.PI);g.stroke()}g.strokeStyle="rgba(255,255,255,.5)";for(const [x,y] of[[0,-1],[6,3],[12,-1],[0,7],[12,7]]){g.beginPath();g.arc(x,y,4.5,.3,Math.PI-.3);g.stroke()}}return _scale}
function sharkSkin(c,L){if(!c||!c.getContext)return c;const g=c.getContext("2d"),h=L*.2,ox=c.width/2+L*.05,oy=c.height*.56;g.save();g.setTransform(1,0,0,1,0,0);g.globalCompositeOperation="source-atop";
 let gr=g.createLinearGradient(0,oy-h*.9,0,oy+h*.7);gr.addColorStop(0,"rgba(8,14,20,.5)");gr.addColorStop(.35,"rgba(10,18,26,.32)");gr.addColorStop(.55,"rgba(20,30,38,.12)");gr.addColorStop(1,"rgba(30,40,48,.22)");g.fillStyle=gr;g.fillRect(0,0,c.width,c.height);// baked countershade: dark back, muted belly, less clean light
 gr=g.createLinearGradient(0,oy-h*.95,0,oy-h*.55);gr.addColorStop(0,"rgba(150,180,200,.14)");gr.addColorStop(1,"rgba(150,180,200,0)");g.fillStyle=gr;g.fillRect(0,0,c.width,oy-h*.5);// only light: thin rim from above
 g.globalAlpha=.06;g.fillStyle=g.createPattern(texGrain(),"repeat");g.fillRect(0,0,c.width,c.height);g.globalAlpha=1;// skin grain 6%
 let z=L|0;const r=()=>(z=(z*16807+7)%2147483647)/2147483647;g.strokeStyle="#20282E";g.lineCap="round";for(let i=0;i<26;i++){const x=ox+L*(-.5+r()*.95),y=oy+h*(-.6+r()*.9),a=r()*.8-.4,l=L*(.01+r()*.03);g.globalAlpha=.25+r()*.3;g.lineWidth=Math.max(.6,L*.0025);g.beginPath();g.moveTo(x,y);g.lineTo(x+Math.cos(a)*l,y+Math.sin(a)*l);g.stroke()}// 20-30 small scars
 g.globalAlpha=.55;g.strokeStyle="#0e151b";g.lineWidth=Math.max(1,L*.005);for(let i=0;i<5;i++){const x=ox+L*(.25-i*.027);g.beginPath();g.moveTo(x,oy-h*.2);g.quadraticCurveTo(x-L*.012,oy+h*.04,x-L*.004,oy+h*.28);g.stroke()}// gill slits, darker inner edge
 g.restore();return c}
function rivalDark(c,L){const g=c.getContext("2d"),h=L*.2,oy=c.height*.56;g.save();g.setTransform(1,0,0,1,0,0);g.globalCompositeOperation="source-atop";/* v10 item 12: rival sharks sit in the murk: darker overall, stronger countershade, no pale clean light */
 const gr=g.createLinearGradient(0,oy-h,0,oy+h*.7);gr.addColorStop(0,"rgba(6,12,18,.7)");gr.addColorStop(.5,"rgba(10,18,26,.55)");gr.addColorStop(.62,"rgba(16,26,34,.48)");gr.addColorStop(1,"rgba(16,26,34,.52)");g.fillStyle=gr;g.fillRect(0,0,c.width,c.height);g.restore();return c}
function fishSkin(c,a){if(!c||!c.getContext)return;const g=c.getContext("2d"),H2=c.height;g.save();g.setTransform(1,0,0,1,0,0);g.globalCompositeOperation="source-atop";
 g.globalAlpha=.3*a;g.fillStyle="#5f6a70";g.fillRect(0,0,c.width,H2);// desaturate: pull bold colours toward murk grey (patterns ~50% contrast)
 g.globalAlpha=.15;g.fillStyle=g.createPattern(texScale(),"repeat");g.fillRect(0,0,c.width,H2);// shared scale tile at 15%
 g.globalAlpha=1;const gr=g.createLinearGradient(0,0,0,H2);gr.addColorStop(0,"rgba(6,14,22,"+(.45*a)+")");gr.addColorStop(.5,"rgba(20,32,42,"+(.15*a)+")");gr.addColorStop(1,"rgba(60,70,80,"+(.05*a)+")");g.fillStyle=gr;g.fillRect(0,0,c.width,H2);// darker back, lighter belly
 g.globalAlpha=.05;g.fillStyle=g.createPattern(texGrain(),"repeat");g.fillRect(0,0,c.width,H2);g.restore()}
function buildSprites(){
 SURF=Math.round(H*WORLD.SKY);WORLD_H=Math.round(H*WORLD.SCREENS);BED=Math.round(WORLD_H-H*WORLD.FLOOR*.62);
 // whole-world water gradient (drawn each frame through the camera transform: 1 fill)
 // COLOR-SHIFT FAKE DEPTH: one baked 1px-wide gradient (light at the surface -> dark cap), drawn each frame as ONE stretched fill
 fogSpr=mk(1,512);{const g=fogSpr.getContext("2d"),gr=g.createLinearGradient(0,0,0,512);for(const s of LIGHT.FOG)gr.addColorStop(Math.max(0,Math.min(1,s[0]/ZONE.CARGO)),s[1]);/* b57: fog stops are depthRaw/ZONE.CARGO, so the surfer zone stays lightly fogged */g.fillStyle=gr;g.fillRect(0,0,1,512)}
 gradSpr=mk(1,512);{const g=gradSpr.getContext("2d"),gr=g.createLinearGradient(0,0,0,512);for(const s of LIGHT.STOPS)gr.addColorStop(Math.max(0,Math.min(1,s[0]/ZONE.CARGO)),s[1]);/* b57: hues spread from the surface to the cargo edge; black is the last stop */g.fillStyle=gr;g.fillRect(0,0,1,512)}
 skySpr=mk(W*DPR,SURF*DPR);{const g=skySpr.getContext("2d");g.scale(DPR,DPR);let gr=g.createLinearGradient(0,0,0,SURF);gr.addColorStop(0,"#3f7fa8");gr.addColorStop(.7,"#8fb8cf");gr.addColorStop(1,"#c9dde6");g.fillStyle=gr;g.fillRect(0,0,W,SURF);
  gr=g.createRadialGradient(W*.84,SURF*.38,4,W*.84,SURF*.38,SURF*.5);gr.addColorStop(0,"rgba(255,248,220,.8)");gr.addColorStop(.2,"rgba(255,236,190,.45)");gr.addColorStop(1,"rgba(255,236,190,0)");g.fillStyle=gr;g.fillRect(0,0,W,SURF);
  for(const [x,y,r] of[[.12,.35,14],[.17,.3,20],[.23,.36,13],[.5,.22,10],[.55,.2,15],[.6,.24,11]]){const cg=g.createLinearGradient(0,SURF*y-r,0,SURF*y+r);cg.addColorStop(0,"#fff");cg.addColorStop(1,"#d6ecf7");g.fillStyle=cg;g.beginPath();g.arc(W*x,SURF*y,r,0,7);g.fill()}
  g.fillStyle="#3c7da6";g.beginPath();g.moveTo(0,SURF);for(let x=0;x<=W*.3;x+=W*.05)g.lineTo(x,SURF-6-Math.sin(x*.03)*5-(x<W*.15?10:0));g.lineTo(W*.3,SURF);g.fill()}// distant island
 raysSpr=mk(W*.5,H*.7);{const g=raysSpr.getContext("2d"),w=raysSpr.width,h=raysSpr.height;/* v10 gfx step 2: soft baked god rays (blurred once, no hard edges) */try{g.filter="blur("+Math.round(w*.025)+"px)"}catch(_){}
  for(let i=0;i<6;i++){const x=w*(i/6+.05+Math.random()*.04),wd=w*(.03+Math.random()*.05),gr=g.createLinearGradient(0,0,0,h);gr.addColorStop(0,"rgba(215,242,255,.30)");gr.addColorStop(.55,"rgba(190,230,255,.10)");gr.addColorStop(1,"rgba(190,230,255,0)");g.fillStyle=gr;g.beginPath();g.moveTo(x,0);g.lineTo(x+wd,0);g.lineTo(x+wd*1.6+w*.06,h);g.lineTo(x-wd*.6-w*.04,h);g.closePath();g.fill()}g.filter="none"}
 sunSpr=mk(W*DPR,H*.9*DPR);{const g=sunSpr.getContext("2d");g.scale(DPR,DPR);for(let i=0;i<2;i++)g.drawImage(raysSpr,i*W*.5,0,W*.5,H*.7);/* b54 (Jeremy via Eve, Skeptic: realistic water): caustics, the wobbly web of light just under the surface. Baked ONCE into the sun sprite (no per-frame cost), wraps horizontally, fades with depth */{let sd=11;const r=()=>{sd=(sd*16807)%2147483647;return sd/2147483647};g.save();g.globalCompositeOperation="lighter";g.lineJoin="round";const Hc=H*.34;for(let i=0;i<Math.round(W*Hc/1100);i++){const cx=r()*W,cy=Math.pow(r(),1.4)*Hc,rad=10+r()*18,a=.075*(1-cy/Hc)*(1-cy/Hc),ph=r()*6.283,ph2=r()*6.283;g.strokeStyle="rgba(210,245,255,"+a.toFixed(3)+")";g.lineWidth=.8+r()*1.4;for(const ox of [0,-W,W]){g.beginPath();const n=16;for(let j=0;j<=n;j++){const an=j/n*6.283,rr=rad*(1+.22*Math.sin(an*3+ph)+.12*Math.sin(an*5+ph2)),x=cx+ox+Math.cos(an)*rr,y=cy+Math.sin(an)*rr*.55;j?g.lineTo(x,y):g.moveTo(x,y)}g.closePath();g.stroke()}}g.restore()}
  /* caustics: soft net of light just under the surface, baked once, fades with depth (no swoosh marks) */const cg=mk(W,H*.22),c=cg.getContext("2d");c.strokeStyle="rgba(200,240,255,.10)";c.lineWidth=1.6;
  for(let r=0;r<5;r++)for(let i=0;i<Math.round(W/34);i++){const x=i*34+rnd(-10,10),y=r*H*.045+rnd(0,12);c.beginPath();c.moveTo(x,y);c.bezierCurveTo(x+12,y-8,x+22,y+9,x+36,y+rnd(-4,4));c.stroke()}
  const fm=g.createLinearGradient(0,0,0,H*.22);fm.addColorStop(0,"rgba(0,0,0,1)");fm.addColorStop(1,"rgba(0,0,0,0)");c.globalCompositeOperation="destination-in";c.fillStyle=fm;c.fillRect(0,0,W,H*.22);g.globalAlpha=.9;try{g.filter="blur(1.2px)"}catch(_){}g.drawImage(cg,0,2);g.filter="none";g.globalAlpha=1}
 /* v10 gfx step 4: baked edge vignette + cool colour grade, one drawImage per frame */gradeSpr=mk(256,144);{const g=gradeSpr.getContext("2d"),gr=g.createRadialGradient(128,72,30,128,72,150);gr.addColorStop(0,"rgba(0,18,36,.06)");gr.addColorStop(.55,"rgba(0,12,28,.16)");gr.addColorStop(1,"rgba(0,4,12,.55)");g.fillStyle=gr;g.fillRect(0,0,256,144)}
 vigSpr=mk(512,512);{const g=vigSpr.getContext("2d"),gr=g.createRadialGradient(256,256,20,256,256,128);gr.addColorStop(0,"rgba(0,0,8,0)");gr.addColorStop(.45,"rgba(0,0,8,.25)");gr.addColorStop(1,"rgba(0,0,8,.97)");g.fillStyle=gr;g.fillRect(0,0,512,512)}
 /* b48 (Jeremy: endless world): no volcanic floor sprite any more. */
 puffSpr=mk(128,128);{const g=puffSpr.getContext("2d"),gr=g.createRadialGradient(56,56,4,64,64,64);gr.addColorStop(0,"rgba(235,60,60,.95)");gr.addColorStop(.55,"rgba(200,30,40,.6)");gr.addColorStop(1,"rgba(170,20,30,0)");g.fillStyle=gr;g.fillRect(0,0,128,128)}
 // background scenery (parallax silhouettes) by depth: kelp/rocks in the sunlit zone, jellies in twilight, giant squid-ish shapes + rock spires deep
 decoSpr={};const bake=(k,w,h,ox,oy,fn)=>{const c=mk(w*DPR,h*DPR),g=c.getContext("2d");g.scale(DPR,DPR);g.translate(ox,oy);fn(g);c.w=w;c.h=h;c.ox=ox;c.oy=oy;decoSpr[k]=c};
 bake("kelp",60,170,30,100,g=>{g.strokeStyle="rgba(10,80,70,.55)";g.lineWidth=7;g.lineCap="round";g.beginPath();g.moveTo(0,60);for(let i=0;i<6;i++)g.lineTo(Math.sin(1+i*.7)*10,60-i*30);g.stroke()});
 bake("rock",140,110,65,55,g=>{const P=[[-62,52],[-55,10],[-38,-22],[-14,-42],[8,-50],[30,-30],[48,-4],[62,24],[72,52]];const gr=g.createLinearGradient(0,-50,0,52);gr.addColorStop(0,"rgba(40,70,88,.55)");gr.addColorStop(.5,"rgba(14,38,56,.6)");gr.addColorStop(1,"rgba(4,14,24,.7)");g.fillStyle=gr;g.beginPath();g.moveTo(P[0][0],P[0][1]);for(let i=1;i<P.length;i++){const a=P[i-1],b=P[i];g.quadraticCurveTo(a[0]+(b[0]-a[0])*.2,b[1]-6,b[0],b[1])}g.closePath();g.fill();/* v10 gfx: soft facets */g.fillStyle="rgba(0,8,16,.25)";g.beginPath();g.moveTo(8,-50);g.quadraticCurveTo(40,-10,72,52);g.lineTo(20,52);g.quadraticCurveTo(14,0,8,-50);g.fill();g.fillStyle="rgba(120,160,180,.08)";g.beginPath();g.ellipse(-12,-30,22,8,-.4,0,7);g.fill()});
 bake("jelly",56,80,28,26,g=>{g.fillStyle="rgba(150,200,255,.18)";g.beginPath();g.arc(0,0,22,Math.PI,0);g.closePath();g.fill();g.strokeStyle="rgba(150,200,255,.18)";g.lineWidth=2;g.beginPath();for(let i=-2;i<=2;i++){g.moveTo(i*8,0);g.quadraticCurveTo(i*8+3,25,i*8,45)}g.stroke()});
 bake("spire",96,370,44,165,g=>{g.fillStyle="rgba(8,22,38,.5)";g.beginPath();g.moveTo(-40,200);g.lineTo(-14,-120);g.lineTo(4,-160);g.lineTo(20,-90);g.lineTo(44,200);g.closePath();g.fill()});/* b57: a soft blue silhouette. The old near-black spire (rgba 2,6,16 at .75) punched a dark hole in water that is still light blue */
 if(!tiles.length||tiles.W!==W||tiles.H!==H){initTiles();tiles.W=W;tiles.H=H}// a render-scale change keeps the world as is
 snow=[];for(let i=0;i<80;i++)snow.push({x:Math.random(),y:Math.random(),r:rnd(.6,1.8),sp:rnd(4,12)});/* 80 pooled: 46 shallow/mid, up to 80 deep */murk=[];for(let i=0;i<50;i++)murk.push({x:Math.random(),y:Math.random(),r:rnd(.5,1),sp:rnd(1.5,5),l:i%2});/* v10 item 12 step 4: pooled dark drifting particles, 2 parallax layers */
 buildShark();
 const FB=48;fishSpr=[0,1,2,3].map(ti=>FISH_PAL.concat(DEEP_PAL).map(col=>{const s=FB,pad=4,c=mk((s*1.8+pad*2)*DPR,(s*1.05+pad*2)*DPR),q=c.getContext("2d");q.scale(DPR,DPR);q.translate(s*.88+pad,s*.52+pad);drawFish(q,s,col,ti,false);c.base=FB;return c}));
 glowSpr=GLOW_PAL.map(col=>{const s=FB,pad=26,c=mk((s*1.8+pad*2)*DPR,(s*1.05+pad*2)*DPR),q=c.getContext("2d");q.scale(DPR,DPR);q.translate(s*.88+pad,s*.52+pad);drawFish(q,s,"#26323c",2,false);/* v10 item 12: dark body, glow only on small spots */
  q.fillStyle=col;q.globalAlpha=.55;for(let i=0;i<4;i++){q.beginPath();q.arc(-s*.3+i*s*.15,s*.12,1.5,0,7);q.fill()}q.globalAlpha=1;q.strokeStyle="#3a4650";q.lineWidth=1.5;q.beginPath();q.moveTo(s*.3,-s*.3);q.quadraticCurveTo(s*.6,-s*.8,s*.75,-s*.5);q.stroke();q.fillStyle=col;q.shadowColor=col;q.shadowBlur=5;q.globalAlpha=.8;q.beginPath();q.arc(s*.75,-s*.5,3,0,7);q.fill();q.globalAlpha=1;q.shadowBlur=0;c.base=FB;return c});
 const crit=(fn,pad,glow)=>{const s=FB,c=mk((s*1.8+pad*2)*DPR,(s*1.4+pad*2)*DPR),q=c.getContext("2d");q.scale(DPR,DPR);q.translate(s*.9+pad,s*.7+pad);fn(q,s);c.base=FB;return c};
 haloSpr=GLOW_PAL.map(col=>{const c=mk(64,64),g=c.getContext("2d"),gr=g.createRadialGradient(32,32,2,32,32,32);gr.addColorStop(0,col);gr.addColorStop(.4,col+"88");gr.addColorStop(1,col+"00");g.fillStyle=gr;g.fillRect(0,0,64,64);return c});
 plankSpr=PLANK_SP.map(p=>spSprite(p,FB));// plankton now drawn as tiny real-looking fry
 specSpr=SPECIES.map(p=>spSprite(p,FB));
 anglerSpr=crit(q=>drawAngler(q,FB),22);lureSpr=mk(64,64);{const g=lureSpr.getContext("2d"),gr=g.createRadialGradient(32,32,1,32,32,32);gr.addColorStop(0,"rgba(255,250,190,1)");gr.addColorStop(.3,"rgba(255,230,120,.55)");gr.addColorStop(1,"rgba(255,220,90,0)");g.fillStyle=gr;g.fillRect(0,0,64,64)}
 octoSpr=["#5A2F36","#4a3040"].map(col=>crit(q=>drawOcto(q,FB,col),8));
 starSpr=["#ff8a3d","#ff5f8f","#ffc23d"].map(col=>crit(q=>drawStar(q,FB,col),6));
 sharkSpr=SHARK_PALS.map(T=>{const L=170,c=rivalDark(sharkSkin(render3DShark(L*DPR,false,T),L*DPR),L*DPR);c.L=L;c.o=rivalDark(sharkSkin(render3DShark(L*DPR,true,T),L*DPR),L*DPR);return c});
 surfSpr=[0,1].map(k=>{const s=60,c=mk(s*1.5*DPR,s*1.1*DPR),q=c.getContext("2d");q.scale(DPR,DPR);q.translate(s*.75,s*.98);drawSurfer(q,s,k);c.wl=.89;return c});
 {const c=mk(240*DPR,290*DPR),q=c.getContext("2d");q.scale(DPR,DPR);q.translate(120,262);drawSailBoat(q);c.wl=262/290;surfSpr[2]=c}
 {const c=mk(700*DPR,160*DPR),q=c.getContext("2d");q.scale(DPR,DPR);q.translate(350,134);drawCargoShip(q);c.wl=134/160;surfSpr[3]=c}
 {const c=mk(780*DPR,200*DPR),q=c.getContext("2d");q.scale(DPR,DPR);q.translate(390,160);drawOilTanker(q);c.wl=160/200;surfSpr[4]=c}/* b57: one baked tanker, drawn with the same surface loop */
 {/* v10 gfx step 3: darker, natural painted look baked into creature + surfer sprites */const nat=(c,a,col)=>{if(!c||!c.getContext)return;const g=c.getContext("2d");g.save();g.setTransform(1,0,0,1,0,0);g.globalCompositeOperation="source-atop";g.globalAlpha=a;g.fillStyle=col||"#0a1a2a";g.fillRect(0,0,c.width,c.height);g.restore()};
  fishSpr.forEach(r=>r.forEach(c=>nat(c,.34)));specSpr.forEach(c=>nat(c,.3));plankSpr.forEach(c=>nat(c,.25));fishSpr.forEach(r=>r.forEach(c=>fishSkin(c,1)));specSpr.forEach(c=>fishSkin(c,.9));plankSpr.forEach(c=>fishSkin(c,.6));/* v10 item 12 step 2 */glowSpr.forEach(c=>fishSkin(c,.8));fishSkin(anglerSpr,1.6);octoSpr.forEach(c=>fishSkin(c,1.2));/* step 3: dark textured deep bodies (lure/halo stay separate small sprites) */nat(anglerSpr,.3);octoSpr.forEach(c=>nat(c,.42));starSpr.forEach(c=>nat(c,.5,"#141a22"));glowSpr.forEach(c=>nat(c,.32,"#06121e"));surfSpr.forEach(c=>nat(c,.14,"#20303a"))}
 const tw=titleW();title=render3DTitle(tw*DPR);title.dw=tw;const L=Math.min(H*.9,420);buildTitleShark();warmSprites()}
// v9: crop + mip every creature sprite up front (the bigger drawn world hit lazy getImageData crops mid-play = first-encounter stutter)
function warmSprites(){const all=[].concat(...fishSpr,glowSpr,specSpr,plankSpr,octoSpr,starSpr,[anglerSpr],sharkSpr,sharkSpr.map(c=>c.o));for(const c of all)if(c&&c.width)mip(trim(c),.02)}
function titleW(){return Math.min(W*.56,H*1.15,560)}
function buildShark(keep){const L=sharkL(shark.lvl);shark.Lt=L;if(!keep||!(shark.L>0))shark.L=L;const TT=Object.assign({},TYPES[sType],{barA:Math.max(.18,.62-shark.lvl*.045)});sprC=sharkSkin(render3DShark(L*DPR,false,TT),L*DPR);sprO=sharkSkin(render3DShark(L*DPR,true,TT),L*DPR);{const b=mk(sprC.width,sprC.height),q=b.getContext("2d");q.drawImage(sprC,0,0);q.globalCompositeOperation="source-atop";const gr=q.createLinearGradient(0,0,0,b.height);gr.addColorStop(0,"rgba(214,226,234,.55)");gr.addColorStop(.45,"rgba(235,242,246,.25)");gr.addColorStop(1,"rgba(250,252,253,.7)");q.fillStyle=gr;q.fillRect(0,0,b.width,b.height);b.L=sprC.L;sprB=b}{const b=mk(sprC.width,sprC.height),q=b.getContext("2d");q.drawImage(sprC,0,0);q.globalCompositeOperation="source-atop";q.fillStyle="rgba(4,10,16,1)";q.fillRect(0,0,b.width,b.height);b.L=sprC.L;sprK=b}/* b53: shadow copy for the far side in the 3D turn */sprF=renderFrontShark(L*.5*DPR,false);/* b52: belly-lit and head-on sprites for the 3D turn */// tiger bars fade with growth
sprC.L=sprO.L=L}
let _st=-1;function safeTop(){if(_st<0){const d=document.createElement("div");d.style.cssText="position:fixed;top:env(safe-area-inset-top);";document.body.appendChild(d);_st=d.getBoundingClientRect().top||0;d.remove()}return _st}
function resize(keep){DPR=Math.max(.5,Math.min(DPR_CAP,window.devicePixelRatio||1)*RS0*RSK);W=innerWidth;H=innerHeight;C.width=Math.round(W*DPR);C.height=Math.round(H*DPR);if(!keep)buildSprites();if(state!=="play")placeAll()}
function spSprite(p,s){const L=p.lng||1,pad=8,w=(s*(.5*L+.85)+pad)*2,c=mk(w*DPR,(s*1.6+pad*2)*DPR),q=c.getContext("2d");q.scale(DPR,DPR);q.translate(w/2,s*.8+pad);drawSpecies(q,s,p);
 const lp=spLure(p,s);if(lp){q.shadowColor=p.c2;q.shadowBlur=10;q.fillStyle=p.c2;q.beginPath();q.arc(lp[0],lp[1],s*.04,0,7);q.fill();q.fillStyle="#fff";q.beginPath();q.arc(lp[0],lp[1],s*.015,0,7);q.fill();q.shadowBlur=0}// baked lure light
 if(p.z===3&&!lp){q.fillStyle="rgba(120,220,255,.9)";for(let i=0;i<5;i++){q.beginPath();q.arc(s*(.3-i*.15),s*p.h*.75,s*.018,0,7);q.fill()}}// photophore dots
 c.base=s;c.sp=p.n;return c}
function rnd(a,b){return a+Math.random()*(b-a)}
function setCreature(f,sz,kind){f.off=false;f.fade=0;f.tiny=false;/* b55 */f.retry=0;f.fu=Math.random();f.fk=CREATURES.FLEE_MIN+f.fu*(CREATURES.FLEE_MAX-CREATURES.FLEE_MIN);if(!f.band)f.band=[SURF+6,Infinity];f.s=sz;f.kind=kind;f.tier=tierOf(sz);f.chase=0;f.rest=0;f.bump=0;f.st="";f.dg=0;f.dt=0;f.dcd=0;f.dn=0;f.pal=kind==="shark"?Math.min(2,Math.floor(rnd(0,3))):kind==="glow"?Math.floor(rnd(0,GLOW_PAL.length)):0;if(kind==="fish"||kind==="shark"||kind==="glow")f.band=[SURF+6,Infinity]}
// ---- SLIDING TILE POOL: 9 tiles (3x3, one screen each) around the camera. When the camera crosses a tile edge, tiles that fall
// out of the window are recycled to the new edge with fresh scenery, and the creatures they own get fresh spawns. Only these
// tiles' creatures exist (update + draw); anything that leaves the window is respawned into its home tile.
function initTiles(){tiles=[];for(let i=0;i<9;i++)tiles.push({tx:1e9,ty:1e9,deco:[],i});tileC.x=tileC.y=1e9;fish.forEach((f,i)=>f.tile=tiles[i%9])}
function seedTile(T,tx,ty){T.tx=tx;T.ty=ty;T.deco.length=0;const x0=tx*W,y0=ty*H;
 for(let i=0;i<4;i++){const x=x0+rnd(0,W),y=y0+rnd(0,H);if(y<SURF+50)continue;const L=layerOf(y),d=depthRaw(y);if(L===2&&y>BED-60)continue;if(d<ZONE.SURF&&i%2)continue;/* b57: the light-blue surfer zone (down to depth 1.6) keeps kelp and jellies only. Black spires start with the sail zone, or they read as a hole in water that is still bright */T.deco.push({x,y,k:d<LAYERS.TOP?"kelp":d<ZONE.SURF?"jelly":"spire",s:rnd(.7,1.3)})}}
function updTiles(force,noSpawn){const cx=Math.floor((camX+W/2)/W),cy=Math.floor((camY+H/2)/H);if(!force&&cx===tileC.x&&cy===tileC.y)return false;tileC.x=cx;tileC.y=cy;
 const want=[];for(let j=-1;j<=1;j++)for(let i=-1;i<=1;i++)want.push([cx+i,cy+j]);
 const used=new Array(9).fill(false),free=[];for(const T of tiles){const w=want.findIndex(q=>q[0]===T.tx&&q[1]===T.ty);if(w>=0&&!used[w])used[w]=true;else free.push(T)}
 for(let w=0;w<9;w++)if(!used[w]){const T=free.pop();seedTile(T,want[w][0],want[w][1]);T.fresh=true}
 if(!noSpawn)for(const f of fish)if(!f.off&&f.tile&&f.tile.fresh)spawnFish(f,true,f.tile);
 for(const T of tiles)T.fresh=false;return true}
function inWindow(x,y,m){const cx=camX+W/2,cy=camY+H/2;return Math.abs(x-cx)<W*(1.5+(m||0))&&Math.abs(y-cy)<H*(1.5+(m||0))}
function pickKind(L,y,T){const tb=SPAWN[L];let tot=0;for(const e of tb)tot+=e[1]+(e[0]==="plankton"&&shark.lvl<2?.25:0);let r=Math.random()*tot;
 for(const e of tb){r-=e[1]+(e[0]==="plankton"&&shark.lvl<2?.25:0);if(r<=0){if(e[0]==="angler"&&depthRaw(y)<ANGLER_D)return "glow";return e[0]}}return tb[0][0]}
function spawnFish(f,edge,T){const P0=state==="play",C=CREATURES;f.off=false;f.fade=0;f.retry=0;
 if(!T&&P0&&f.tile&&(Math.abs(f.tile.ty*H+H/2-shark.y)>H*2.2||Math.abs(f.tile.tx*W+W/2-shark.x)>W*2.2)){camX=shark.x-W/2;camY=shark.y-H/2;updTiles(true,true)}// teleport (tests/respawn): snap pool to the shark
 if(!T){if(f.tile)T=f.tile;else{const ry=P0?shark.y:camY+H/2;T={tx:Math.floor((camX+W/2)/W)+Math.floor(rnd(-1,2)),ty:Math.floor(ry/H)}}}
 let y0=Math.max(SURF+8,T.ty*H),y1=T.ty*H+H;if(y1<SURF+40){y0=SURF+8;y1=SURF+H*.5}
 const vx0=camX-50,vx1=camX+W+50,vy0=camY-50,vy1=camY+H+50;
 for(let k=0;k<12;k++){f.x=T.tx*W+rnd(0,W);f.y=rnd(y0,y1);
  if(edge&&f.x>vx0&&f.x<vx1&&f.y>vy0&&f.y<vy1){// tile overlaps the view: push the spawn just outside the nearest side edge
   f.x=f.x<camX+W/2?vx0-rnd(0,W*.4):vx1+rnd(0,W*.4)}
  let crowd=false;if(k<9)for(const q of fish)if(q!==f&&!q.off&&Math.abs(q.x-f.x)<C.SPREAD_PX&&Math.abs(q.y-f.y)<C.SPREAD_PX*.6){crowd=true;break}
  if(!crowd&&(!P0||Math.hypot(f.x-shark.x,f.y-shark.y)>Math.min(W,H)*(elapsed<SAFE_SPAWN_S?.7:.45)))break}
 const L=layerOf(f.y),d=depthOf(f.y);let kind=pickKind(L,f.y,T);
 // starfish: only on the seabed strip (deep layer), when this tile contains it
 /* b48: no seabed, so no starfish strip */
 let sz;
 if(kind==="plankton")sz=bite()*rnd(.3,.55)*GROW.START*worldK;
 else if(kind==="star")sz=rnd(14,28)*sizeK*worldK;
 else if(kind==="octo")sz=rnd(30,70)*sizeK*worldK;
 else if(kind==="angler")sz=rnd(55,90)*sizeK*worldK;
 else{const mn=L===0?C.SIZE_MIN:L===1?24:30,mx=L===0?C.SIZE_SHALLOW:L===1?62:C.SIZE_DEEP;sz=(mn+(mx-mn)*Math.pow(Math.random(),1.5))*sizeK;if(kind==="shark")sz=Math.max(sz,22+30*d)*rnd(1,1.25);sz*=worldK}
 // food share: keep enough edible prey; capped prey stays inside its own layer's table
 if(P0&&kind!=="plankton"&&kind!=="star"&&kind!=="angler"&&!(kind==="shark"&&d>.3&&shark.lvl>=GROW.FOOD_LVL)&&Math.random()<C.FOOD_SHARE+Math.max(0,GROW.FOOD_LVL-shark.lvl)*.03){sz=Math.min(sz,bite()*rnd(.4,.84));if(kind==="shark"&&(sz<20*worldK||d>.3))kind=L===2?"glow":"fish"}
 if(kind==="shark"&&P0){let n=0;for(const q of fish)if(q!==f&&!q.off&&q.kind==="shark"&&Math.abs(q.y-f.y)<H*.8&&Math.abs(q.x-f.x)<W*1.6)n++;if(n<C.MAX_BIG&&Math.abs(f.y-shark.y)<H*.8){n=0;for(const q of fish)if(q!==f&&!q.off&&q.kind==="shark"&&Math.abs(q.y-shark.y)<H*.8)n++}if(n>=C.MAX_BIG)kind=L===2?"glow":"fish"}// cap near the spawn AND near you
 if(kind==="glow"&&P0)sz=Math.min(sz,bite()*C.GLOW_MAX);
 if(P0&&L===2&&kind!=="glow"&&kind!=="star"&&kind!=="plankton"){const g=Math.min(1,Math.max(0,(d-LAYERS.MID)/DEEP.RAMP));if(sz>bite()*.9)sz*=1+DEEP.GROW*g*Math.max(0,1-shark.lvl/DEEP.FADE_LVL);{const ln=kind==="shark"?2.5:1.6;sz=Math.min(sz,W*DEEP.MAX_W/ln);/* v9c: deep width caps stay on true size (deep > mid in the same proportion); giants keep their old drawn size */if(sz*ln>W*DEEP.BIG_W&&fish.filter(q=>q!==f&&!q.off&&!q.giant&&q.s*(q.kind==="shark"?2.5:1.6)>W*DEEP.BIG_W).length>=DEEP.BIG_N)sz=W*DEEP.BIG_W/ln}/* at most BIG_N very big ones around (perf, and so giants stay special) *//* deeper = bigger for a small player (fades out as you grow: perf + you are the big one by then) *//* deeper = bigger (not the prey share) */
  if((kind==="shark"||kind==="octo")&&Math.random()<DEEP.GIANT_P*(.4+g)*Math.max(0,1-shark.lvl/DEEP.FADE_LVL)&&!fish.some(q=>q!==f&&!q.off&&q.giant)){/* one giant at a time */const vl=Math.min(W*DEEP.GIANT_MAXW,shark.L*rnd(DEEP.GIANT_MIN,DEEP.GIANT_MAX));sz=vl/(kind==="shark"?2.5:1.6)/LOOK.K;f.giant=true}else f.giant=false}else f.giant=false
 if(kind==="shark"||(L===2&&kind!=="plankton"&&kind!=="star"&&kind!=="glow")){const dg=1+C.DEPTH_K*Math.max(0,depthRaw(f.y)-LAYERS.MID);if(dg>1){if(sz>=bite()*.87)sz*=dg;else sz=Math.min(bite()*.84,sz*Math.min(dg,1.5))}}/* b57: below the mid layer, bigger-than-you creatures keep growing with depth (no ceiling). Edible ones grow at most 1.5x and stay under 0.84× bite */
 if(P0&&chaseCapped(f,kind,sz)){sz=bite()*rnd(.4,.84);f.giant=false;if(kind==="shark"||kind==="angler"||kind==="octo")kind=L===2?"glow":"fish"}/* b55 ramp cap (after deep growth + giants) */
 setCreature(f,Math.max(kind==="plankton"?2:Math.max(C.SIZE_MIN*worldK,P0?bite()*lookMin():0),sz),kind);
 f.pal=kind==="fish"?Math.floor(rnd(0,L===1?FISH_PAL.length+3:FISH_PAL.length)):kind==="plankton"?Math.floor(rnd(0,2)):kind==="octo"?Math.floor(rnd(0,2)):kind==="star"?Math.floor(rnd(0,3)):f.pal;
 f.sp=-1;if(kind==="fish"){const z=L===0?0:(sz>bite()*.9||depthOf(f.y)>(LAYERS.TOP+LAYERS.MID)/2)?2:1,lst=SP_Z[z];f.sp=lst[Math.floor(Math.random()*lst.length)]}
 else if(kind==="glow"&&Math.random()<.6){const lst=SP_Z[3].filter(i=>SPECIES[i].n!=="Pelican eel"||(sz>bite()*.7&&Math.random()<.3));f.sp=lst[Math.floor(Math.random()*lst.length)]}
 f.L=L;f.band=kind==="star"?[BED-14,BED]:bandOf(L);
 spawnStats.n++;spawnStats.byKind[kind]=(spawnStats.byKind[kind]||0)+1;if(!ALLOWED[kind].includes(layerOf(f.y)))spawnStats.wrong++;
 const dir=Math.random()<.5?1:-1,sp=kind==="star"?rnd(3,7):kind==="plankton"?rnd(8,16):kind==="octo"?rnd(15,25):rnd(25,45);f.vx=dir*sp*(f.s>40?.7:1);f.vy=0;f.tiny=false;if(P0&&goneAt(f.y))makeTiny(f)}
/* b55 (Jeremy t1627u: "way too many larger things that chase ... getting passed level 5 impossible"): from the size where the top band is outgrown
   (VANISH.LVL[0], HUD 5) a new creature that could eat you is turned into food when CHASE.CAP eaters already swim within CHASE.NEAR screens of you. */
/* b56 (Jeremy t1637u "reduce the number of larger sharks a little more, and the same when maxed out"): CAP 2 -> 1 from HUD MAX_FROM+1 (HUD 9-10 / endless max),
   and fewer deep sharks overall (CREATURES.SHARK_P_DEEP .45 -> .38, MAX_BIG 3 -> 2). */
const CHASE={CAP:2,NEAR:.7,CAP_MAX:1,MAX_FROM:8};const chaseCap=()=>shark.lvl>=CHASE.MAX_FROM?CHASE.CAP_MAX:CHASE.CAP;
function chaseCapped(f,kind,sz){if(state!=="play"||shark.lvl<VANISH.LVL[0]||kind==="plankton"||kind==="star"||sz/bite()<EAT.RATIO)return false;let n=0;for(const q of fish)if(q!==f&&!q.off&&!q.tiny&&q.kind!=="plankton"&&q.kind!=="star"&&q.s/bite()>=EAT.RATIO&&Math.abs(q.x-shark.x)<W*CHASE.NEAR&&Math.abs(q.y-shark.y)<H*CHASE.NEAR)n++;return n>=chaseCap()}
function makeTiny(f){f.tiny=true;f.fade=0;f.danger=false;f.chase=0;f.giant=false;f.s=Math.min(f.s,bite()*VANISH.TINY);spawnStats.tiny=(spawnStats.tiny||0)+1}
function pickSurfK(){const l=shark.lvl,r=Math.random(),sf=()=>l>=SURFACE.SAIL_LVL&&surfK()*60<LATE.SURF_GONE_PX?2:Math.random()<.35?1:0;
 if(pastSurf()){const cargo=l>=SURFACE.CARGO_LVL&&!pastCargo();if(r<.40)return 4;if(r<.70)return 2;if(cargo&&r<.88)return 3;return sf()}/* b57: tankers start at the same depth sails shrink to surfer size; tiny sails stay in the mix */
 return l>=SURFACE.CARGO_LVL?(r<.5?3:r<.85?2:sf()):l>=SURFACE.SAIL_LVL?(r<.6?2:sf()):sf()}
function rollSurf(s){s.k=pickSurfK();s.vx=(Math.random()<.5?-1:1)*(s.k===4?rnd(8,14):s.k===3?rnd(12,20):s.k===2?rnd(20,34):rnd(25,45))}
function spawnSurf(s,edge){s.zip=0;rollSurf(s);const m=50+(SURFERS[s.k].hw||0)*surfDrawK(s);s.x=camX+(edge?(Math.random()<.5?-m:W+m):rnd(50,W-50))}
function placeAll(){for(const T of tiles)T.tx=1e9;updTiles(true,true);for(const f of fish)spawnFish(f,false);for(const s of surf)spawnSurf(s,false)}

// ---------- audio (one AudioContext, synthesized SFX, capped voices) ----------
const FAST_SFX={AT:.7,COOL:1.5};// bubbles when speed rises past 70% of max (upward crossing only), at most once per 1.5 s
const MAX_VOICES=8;
let AC=null,soundOn=LS.getItem(SND_KEY)!=="0",songsOn=(k=>k===null?soundOn:k!=="0")(LS.getItem(SONGS_KEY)),fxOn=(k=>k===null?soundOn:k!=="0")(LS.getItem(SFX_KEY)),/* v10 item 13: separate saved switches; an old save with no switch keys copies the old Sound setting (old off = both off) */sfx=null,noiseBuf=null,voices=0,music={title:null,game:null,cur:null},chip={buf:null,src:null,bus:null,t0:0,failed:false,want:false},placeholder=null,phT0=0;
const sfxCount={chomp:0,bubbles:0,gulp:0,played:0};// test hooks: requested count per sound; "played" = actually sounded (unmuted)
function initAudio(){if(!AC){try{AC=new (window.AudioContext||window.webkitAudioContext)();sfx=AC.createGain();sfx.gain.value=.3;/* v10 item 11: SFX bus .45 -> .3 so music sits above */sfx.connect(AC.destination);
  noiseBuf=AC.createBuffer(1,Math.floor(AC.sampleRate*.12),AC.sampleRate);const d=noiseBuf.getChannelData(0);for(let i=0;i<d.length;i++)d[i]=(Math.random()*2-1)*(1-i/d.length)}catch(e){AC=null}
 music.title=new Audio("audio/intro-scary.ogg");music.title.loop=false;/* v10 item 10: 40 s intro plays once (file fades out), then stops */music.title.preload="auto";music.title.volume=0;
 loadChip()}
 if(AC&&AC.state==="suspended")AC.resume().catch(()=>{})}
// Gameplay music: Slopcore's 8-bit "Reflets dans l'eau" v2, played as a WebAudio buffer loop (sample-accurate, no gap at the loop point).
// If it fails to load or decode, the original placeholder loop below is the fallback.
const CHIP_URL="audio/play-swim-piano.ogg",MUSIC_VOL={title:.5,game:.32};/* v10: both files -16 LUFS, peaks -1.3/-1.9 dBFS; .5 sits above the .3 SFX bus */// game track is ~9 dB louder than the title file, so it plays lower to sit under the SFX
function loadChip(){if(!AC||chip.buf||chip.loading)return;chip.loading=true;fetch(CHIP_URL).then(r=>{if(!r.ok)throw new Error("chip "+r.status);return r.arrayBuffer()})
 .then(b=>new Promise((ok,no)=>AC.decodeAudioData(b,ok,no))).then(buf=>{chip.buf=buf;if(chip.want&&placeholder){phStop();chipStart()}}).catch(()=>{chip.failed=true})}
function chipStart(){if(!AC||!chip.buf||chip.src)return;const bus=AC.createGain(),t=AC.currentTime;bus.gain.setValueAtTime(0,t);bus.gain.linearRampToValueAtTime(musOn()?MUSIC_VOL.game:0,t+.6);bus.connect(AC.destination);
 const src=AC.createBufferSource();src.buffer=chip.buf;src.loop=true;src.connect(bus);src.start(t);chip.src=src;chip.bus=bus;chip.t0=t}
function chipStop(){if(!chip.src)return;const s=chip.src,b=chip.bus;try{b.gain.setTargetAtTime(0,AC.currentTime,.15);s.stop(AC.currentTime+.8);setTimeout(()=>b.disconnect(),1000)}catch(e){}chip.src=null;chip.bus=null}
function voice(dur){if(!AC||!soundOn||!fxOn||voices>=MAX_VOICES)return false;voices++;setTimeout(()=>voices--,dur*1000+60);sfxCount.played++;return true}
function blip(f0,f1,dur,type,vol,delay){if(!voice(dur+(delay||0)))return;const t=AC.currentTime+(delay||0),o=AC.createOscillator(),g=AC.createGain();o.type=type||"square";o.frequency.setValueAtTime(f0,t);o.frequency.exponentialRampToValueAtTime(Math.max(30,f1),t+dur);
 g.gain.setValueAtTime(0.0001,t);g.gain.linearRampToValueAtTime(vol||.3,t+.005);g.gain.exponentialRampToValueAtTime(.001,t+dur);o.connect(g);g.connect(sfx);o.start(t);o.stop(t+dur+.02)}
function noise(dur,vol,freq){if(!voice(dur))return;const t=AC.currentTime,s=AC.createBufferSource(),f=AC.createBiquadFilter(),g=AC.createGain();s.buffer=noiseBuf;f.type="bandpass";f.frequency.value=freq||1800;f.Q.value=.8;
 g.gain.setValueAtTime(vol,t);g.gain.exponentialRampToValueAtTime(.001,t+dur);s.connect(f);f.connect(g);g.connect(sfx);s.start(t);s.stop(t+dur)}
const SFX={
 chomp(){sfxCount.chomp++;noise(.07,.35,2200);blip(160,55,.11,"sine",.45)},// short noise burst + low thump
 bubbles(){sfxCount.bubbles++;const n=2+(Math.random()<.5?1:0);for(let i=0;i<n;i++){const f=rnd(380,620);blip(f,f*rnd(2.2,3),.06+Math.random()*.03,"sine",.22,i*rnd(.07,.11))}},// rising sine blips
 gulp(){sfxCount.gulp++;blip(260,110,.16,"sine",.4);blip(180,70,.22,"sine",.4,.17);blip(500,900,.07,"sine",.15,.42)},// cartoon "gul-ulp" + tiny pop
 pop(){blip(500,1200,.09,"triangle",.3);blip(900,1600,.08,"triangle",.22,.07)},
 grow(){[523,659,784,1047].forEach((f,i)=>blip(f,f,.12,"square",.16,i*.09))},
 /* v10 item 11: wave/water sounds (splash, surface ripple) removed (Jeremy) */launch(){blip(180,520,.18,"triangle",.25)},bump(){blip(220,180,.06,"triangle",.18)},
 
 perfect(){blip(1047,1568,.12,"square",.15)},end(){[784,659,523,392].forEach((f,i)=>blip(f,f*.98,.2,"triangle",.25,i*.16))}};
// FALLBACK only (used if the chiptune file fails to load/decode): tiny ORIGINAL 8-bit loop (not Debussy, not the real track) at BEAT.PLACEHOLDER_BPM, cheap look-ahead scheduler.
const PH_NOTES=[63,70,75,79, 61,68,73,77, 60,67,72,75, 58,65,70,74];const PH_BASS=[39,37,36,34];
function phStart(){if(!AC||placeholder)return;const bus=AC.createGain();bus.gain.value=musOn()?.1:0;bus.connect(AC.destination);let step=0,next=AC.currentTime+.05;phT0=next;const st=30/BEAT.PLACEHOLDER_BPM;
 const tick=()=>{while(next<AC.currentTime+.25){const m=440*Math.pow(2,(PH_NOTES[step%16]-69)/12),o=AC.createOscillator(),g=AC.createGain();o.type="square";o.frequency.value=m;g.gain.setValueAtTime(.5,next);g.gain.exponentialRampToValueAtTime(.01,next+st*.8);o.connect(g);g.connect(bus);o.start(next);o.stop(next+st*.85);
   if(step%4===0){const b=AC.createOscillator(),g2=AC.createGain();b.type="triangle";b.frequency.value=440*Math.pow(2,(PH_BASS[(step>>2)%4]-69)/12);g2.gain.setValueAtTime(.9,next);g2.gain.linearRampToValueAtTime(0,next+st*3.8);b.connect(g2);g2.connect(bus);b.start(next);b.stop(next+st*3.9)}
   step++;next+=st}};placeholder={bus,id:setInterval(tick,100)};tick()}
function phStop(){if(!placeholder)return;clearInterval(placeholder.id);const b=placeholder.bus;try{b.gain.setTargetAtTime(0,AC.currentTime,.2);setTimeout(()=>b.disconnect(),800)}catch(e){}placeholder=null}
let fadeId=0;
function playMusic(which){const id=++fadeId,from=music.cur,to=which==="title"?music.title:null;chip.want=which==="game";
 if(which==="game"){if(chip.buf)chipStart();else phStart()}else{phStop();chipStop()}music.cur=to;if(to&&musOn())to.play().catch(()=>{});
 let k=0;const step=()=>{if(id!==fadeId)return;k+=.1;if(from&&from!==to)from.volume=Math.max(0,from.volume-.1);if(to)to.volume=musOn()?Math.min(MUSIC_VOL.title,k*MUSIC_VOL.title):0;if(k<1)setTimeout(step,60);else if(from&&from!==to)from.pause()};step()}
function musOn(){return soundOn&&songsOn}
setTimeout(()=>{try{sndHint()}catch(e){}},0);setSound=(o=>function(v){o(v);try{sndHint()}catch(e){}})(setSound);/* b45: keep the "Sound is off" hint in step */
function setSound(on){soundOn=on;LS.setItem(SND_KEY,on?"1":"0");$("snd").textContent=on?"🔊 Sound on":"🔈 Sound off";
 if($("songs"))$("songs").textContent=musOn()?"🎵 Songs on":"🎵 Songs off";if($("fx"))$("fx").textContent=soundOn&&fxOn?"🔔 Effects on":"🔕 Effects off";
 const m=musOn();if(placeholder)placeholder.bus.gain.value=m?.1:0;if(chip.bus){chip.bus.gain.cancelScheduledValues(AC.currentTime);chip.bus.gain.value=m?MUSIC_VOL.game:0}
 for(const a of[music.title])if(a){if(m&&a===music.cur){a.volume=MUSIC_VOL.title;a.play().catch(()=>{})}else a.volume=0}}

// ---------- title ----------
// Intro (v10): the shark swims past the words, turns and swims back around the title (over the top), then dives away.
// b47: after two laps it BITES a tooth-edged scoop out of the title letters (one chomp sound, no shake, no blood). Then Jeremy's title picture fades in (0.7 s) and stays.
// The picture is preloaded once and baked to a screen-sized layer on resize; if it fails to load the 3D title stays.
const T={t:0,bitten:false,torn:false,done:false,k:0,sr:null,art:0,pose:false,rel:null,relT:0};const TITLE_TOP_PAD=6,TITLE_ART_FADE=.7;
/* b50 (Jeremy): the whole SHARK ATTACK title always stays whole (nothing is ever cut out of it). The shark swims in BEHIND the words, turns to face the camera,
   grows into a head-on pose with its open jaws around the title, snaps once, then HOLDS that pose until the player taps any title button. Then it glides to the swim line and cruises.
   Calm / reduced motion: no laps, no snap motion; the head-on shark just fades in gently, holds, and releases the same way. Drawn in code (our own renderers), no picture files. */
const TITLE_ENTER=.9,TITLE_ACROSS=1.2,TITLE_TURN=.8,TITLE_SNAP=.35,TITLE_CALM_IN=1.6,TITLE_GLIDE=.7,TITLE_SWIM=TITLE_ENTER+TITLE_ACROSS+TITLE_TURN+TITLE_SNAP;
let tSideO=null,tSideC=null,tHeadO=null,tHeadC=null;
/* b46: title-only WIDE open jaw painted over the open sprite: dropped lower jaw, dark throat, two rows of shaded serrated teeth (no blood, no bite). */
function wideJaw(c,L){const g=c.getContext("2d"),h=L*.2;g.save();g.setTransform(1,0,0,1,0,0);g.globalAlpha=1;g.globalCompositeOperation="source-over";g.shadowBlur=0;g.filter="none";g.translate(c.width/2+L*.05,c.height*.56);g.lineJoin="round";
 const U0=[L*.485,h*.1],K=[L*.25,h*.27],D=[L*.44,h*.9];
 let gr=g.createLinearGradient(L*.48,0,L*.25,0);gr.addColorStop(0,"#3d1416");gr.addColorStop(.4,"#1a0607");gr.addColorStop(1,"#050102");g.fillStyle=gr;
 g.beginPath();g.moveTo(U0[0],U0[1]);g.lineTo(L*.5,h*.2);g.lineTo(L*.47,h*.5);g.lineTo(D[0]+L*.01,D[1]);g.lineTo(K[0],K[1]);g.closePath();g.fill();
 // lower jaw: pale belly skin, shaded underneath
 gr=g.createLinearGradient(0,h*.3,0,h*1.1);gr.addColorStop(0,"#aeb8bf");gr.addColorStop(.45,"#d5dadd");gr.addColorStop(1,"#66727d");g.fillStyle=gr;
 g.beginPath();g.moveTo(K[0]-L*.01,K[1]);g.lineTo(D[0],D[1]);g.quadraticCurveTo(D[0]+L*.012,D[1]+h*.1,D[0]-L*.02,D[1]+h*.16);g.quadraticCurveTo(L*.3,h*.95,L*.16,h*.6);g.closePath();g.fill();
 g.strokeStyle="rgba(4,10,18,.45)";g.lineWidth=Math.max(1,L*.004);g.stroke();
 // gums
 g.strokeStyle="#5e2428";g.lineWidth=Math.max(1,h*.07);g.lineCap="round";g.beginPath();g.moveTo(U0[0]-L*.005,U0[1]+h*.04);g.lineTo(K[0]+L*.01,K[1]);g.moveTo(D[0]-L*.005,D[1]-h*.03);g.lineTo(K[0]+L*.01,K[1]+h*.03);g.stroke();
 const tooth=(x,y,len,w,dn)=>{const tip=y+(dn?len:-len);const tg=g.createLinearGradient(0,y,0,tip);tg.addColorStop(0,"#a99c7e");tg.addColorStop(.35,"#e9e2cc");tg.addColorStop(1,"#fbf8ee");g.fillStyle=tg;
  g.beginPath();g.moveTo(x-w/2,y);g.quadraticCurveTo(x-w*.18,(y+tip)/2,x+w*.06,tip);g.quadraticCurveTo(x+w*.2,(y+tip)/2,x+w/2,y);g.closePath();g.fill();g.strokeStyle="rgba(50,35,25,.55)";g.lineWidth=Math.max(.6,L*.0025);g.stroke();
  g.strokeStyle="rgba(255,255,255,.5)";g.lineWidth=Math.max(.5,L*.0015);g.beginPath();g.moveTo(x-w*.2,y+(dn?1:-1)*len*.15);g.lineTo(x,tip-(dn?1:-1)*len*.15);g.stroke()};
 for(let i=0;i<8;i++){const u=i/7.5,x=U0[0]-L*.008+(K[0]-U0[0])*u,y=U0[1]+h*.05+(K[1]-U0[1])*u;tooth(x,y,h*(.26-u*.13),L*(.03-u*.01),true)}
 for(let i=0;i<7;i++){const u=i/6.5,x=D[0]-L*.012+(K[0]-D[0])*u,y=D[1]-h*.04+(K[1]-D[1])*u;tooth(x,y,h*(.24-u*.12),L*(.028-u*.01),false)}
 g.restore();return c}
function frontSize(){return titleLayout().S}
function buildTitleShark(){const L=Math.min(titleW()*.62,H*.55,330);tSideO=wideJaw(render3DShark(L*DPR,true,TYPES[sType]),L*DPR);tSideC=render3DShark(L*DPR,false,TYPES[sType]);tSideO.L=tSideC.L=L;
 const S=frontSize();tHeadO=renderFrontShark(S*DPR,true);tHeadC=renderFrontShark(S*DPR,false);tHeadO.S=tHeadC.S=S}/* b50: head-on shark pre-rendered once per title (no per-frame drawing work) */
function startTitle(){state="title";camY=0;camX=0;T.t=0;T.bitten=false;T.bite=null;T.frags=[];window.__saBite=null;T.torn=false;T.done=false;T.sr=null;T.art=0;T.pose=false;T.rel=null;T.relT=0;T.log=window.__saTitleLog?[]:null;window.__saTitleDone=false;window.__saPose=null;T.lim=0;T.snapped=0;const tw=titleW();title=render3DTitle(tw*DPR);title.dw=tw;show("titleUi");buildTitleShark()}
/* b51: one layout for the title screen. The head-on shark (whole sprite, fins included) fits in the band between the top edge and the Start button;
   the title sits on the open mouth. The Install hint line has space kept for it, so tapping Install never moves anything. */
function titleLayout(){const top=safeTop()+6,ui=$("titleUi");
 if(ui&&!ui.classList.contains("hide")){const b=$("start").getBoundingClientRect();if(b.height>0)T.lim=b.top-10}
 const bot=T.lim||H*.6,S=Math.max(60,Math.min((bot-top)/1.13,W*.6,600)),cx=W/2,cy=top+S*215/400+S*.004;
 let tw=Math.min(title.dw,S*.86),th=title.height*(tw/title.width);const my=cy+S*72/400;
 return {S,cx,cy,box:{x:cx-S*.8,y:cy-S*215/400,w:S*1.6,h:S*1.12},head:{x:cx-S*.6,y:cy-S*.485,w:S*1.2,h:S*1.0},title:{x:cx-tw/2,y:my-th/2,w:tw,h:th}}}
function titleRect(){return titleLayout().title}
function poseIn(){return calm?TITLE_CALM_IN:TITLE_SWIM}
function updTitle(dt){T.t+=dt;if(T.rel!=null)T.relT+=dt;
 if(!T.done&&T.rel==null&&T.t>=poseIn()){T.done=true;T.pose=true;window.__saTitleDone=true;window.__saPose={held:true,since:+T.t.toFixed(2),released:false};if(T.log)T.log.push([+T.t.toFixed(2),"pose",0,true])}}
/* b50: any title button releases the pose (the button still does its own job right away; Start is never delayed). */
function releasePose(){if(T.rel!=null||state==="tap")return;T.rel=T.t;T.relT=0;T.done=true;T.pose=false;window.__saTitleDone=true;window.__saPose={held:false,since:window.__saPose?window.__saPose.since:null,released:true,at:+T.t.toFixed(2)};if(T.log)T.log.push([+T.t.toFixed(2),"release",0,true])}
function frontAnchor(){const l=titleLayout();return {x:l.cx,y:l.cy}}/* b51: head centre from the shared layout; the title sits on the mouth */
function titleShark(){const r=titleRect(),L=tSideO.L,t=T.t,yw=r.y+r.h*.78,xr=Math.min(W-L*.62,r.x+r.w+L*.1),xl=Math.max(L*.62,r.x-L*.1),cxm=r.x+r.w/2,cym=r.y+r.h*.5;
 const W0=.45,U0=Math.asin(.25)/W0,cx=u=>xl+(xr-xl)*(1-Math.cos(u*W0))/2,A=frontAnchor();
 if(T.rel!=null){const g=T.relT;
  if(g<TITLE_GLIDE){const p=g/TITLE_GLIDE,e=p*p*(3-2*p);return {x:cxm+(cx(U0)-cxm)*e,y:cym+(yw-cym)*e,dir:-1,open:true,layer:"behind",lap:3,front:{a:1-Math.min(1,p*1.6),s:1-.25*e,open:true,x:A.x,y:A.y},a:Math.min(1,p*1.6)}}
  const u=U0+(g-TITLE_GLIDE)*(calm?.6:1);return {x:cx(u),y:yw+Math.sin(u*1.3)*(calm?3:6),dir:Math.max(-1,Math.min(1,Math.sin(u*W0)*4)),open:true,layer:"behind",lap:3}/* b51: cruises behind the words so "ATTACK" stays readable */}
 if(calm){const p=Math.min(1,t/TITLE_CALM_IN),e=p*p*(3-2*p);return {hide:true,layer:"behind",lap:0,front:{a:e,s:.94+.06*e,open:true,x:A.x,y:A.y}}}
 const t1=TITLE_ENTER,t2=t1+TITLE_ACROSS,t3=t2+TITLE_TURN;
 if(t<t1){const p=t/t1,e=p*(2-p),x0=W+L*.7,x1=r.x+r.w*.85;return {x:x0+(x1-x0)*e,y:cym,dir:-1,open:true,layer:"behind",lap:0}}
 if(t<t2){const p=(t-t1)/TITLE_ACROSS,e=p*p*(3-2*p),x1=r.x+r.w*.85;return {x:x1+(cxm-x1)*e,y:cym+Math.sin(p*Math.PI)*r.h*.12,dir:-1,open:true,layer:"behind",lap:1}}
 if(t<t3){const p=(t-t2)/TITLE_TURN,e=p*p*(3-2*p);return {x:cxm,y:cym,dir:-(1-e),open:true,layer:"behind",lap:2,a:1-Math.min(1,e*1.4),front:{a:Math.min(1,e*1.3),s:.35+.65*e,open:true,x:A.x,y:A.y}}}
 const sn=t-t3,shut=sn<TITLE_SNAP&&sn>.05&&sn<.22;if(shut&&!T.snapped){T.snapped=1;if(T.log)T.log.push([+t.toFixed(2),"snap",2,false]);try{SFX.chomp()}catch(e){}}
 const br=T.pose&&!calm?1+Math.sin(t*1.6)*.006:1;return {hide:true,layer:"behind",lap:2,front:{a:1,s:br,open:!shut,x:A.x,y:A.y}}}
function titleInk(){const g=title.getContext("2d"),d=g.getImageData(0,0,title.width,title.height).data;let n=0;for(let i=3;i<d.length;i+=16)if(d[i]>128)n++;return n}
function drawFront(f){if(!f||f.a<=0)return;const s=f.open?tHeadO:tHeadC,z=titleLayout().S/s.S*f.s,dw=s.width/DPR*z,dh=s.height/DPR*z;X.save();X.globalAlpha=Math.max(0,Math.min(1,f.a));X.drawImage(s,f.x-dw/2,f.y-dh*s.cy,dw,dh);X.restore()}
function drawTitleShark(q){if(!q.hide){const s=q.open?tSideO:tSideC,dw=s.width/DPR,dh=s.height/DPR,L=s.L,back=q.layer==="behind",k=back?.86:1;X.save();X.globalAlpha=q.a==null?1:Math.max(0,q.a);X.translate(q.x,q.y);if(q.tilt)X.rotate(q.tilt*Math.sign(q.dir||1));X.scale((Math.abs(q.dir)<.08?.08*Math.sign(q.dir||1):q.dir)*k,k);
X.drawImage(s,-dw/2-L*.05,-dh/2,dw,dh);X.restore()}
 const L=tSideO.L,f=q.front;T.sr=q.hide?{x:f.x,y:f.y,head:f.x,headY:f.y,L,dir:0,open:!!f.open,layer:q.layer,lap:q.lap,front:true,pose:T.pose,s:f.s,a:f.a}:{x:q.x,y:q.y,head:q.x+q.dir*L*.5,headY:q.y,L,dir:q.dir,open:!!q.open,layer:q.layer,lap:q.lap,front:!!f,pose:false};if(T.log)T.log.push([+T.t.toFixed(2),q.layer,q.lap,!!(q.hide?f.open:q.open)])}
function drawTitle(t){const r=titleRect(),bob=(T.rel==null||calm)?0:Math.sin(t*1.5)*3,q=titleShark(),f=q.front;
 if(f)drawFront(f);if(q.layer==="behind")drawTitleShark(q);// shark first, words drawn over it
 /* b50: the title is never cut. Over the shark it gets a soft dark halo so every letter stays readable. */
 const halo=f?Math.max(0,Math.min(1,f.a)):0;if(halo>0){X.save();X.globalAlpha=halo;X.shadowColor="rgba(0,4,10,.6)";X.shadowBlur=6;X.shadowOffsetY=2;X.drawImage(title,r.x,r.y+bob,r.w,r.h);X.restore()}/* b51: subtle soft shadow only (no heavy dark halo) */
 X.drawImage(title,r.x,r.y+bob,r.w,r.h);
 if(q.layer!=="behind")drawTitleShark(q)}

// ---------- play ----------
let lastBub=-9,wasFast=false;
function startGame(){hideAll();state="play";$("boost").classList.remove("hide");score=0;elapsed=0;endReason="";roundLen=window.__saRound||ROUND_SECONDS;timeLeft=roundLen;
 shark.lvl=0;shark.meter=0;shark.dead=false;dead.t=0;worldK=wK(0);shark.pop=0;buildShark();shark.Lt=shark.L;shark.x=W/2;shark.y=SURF+H*.45;camX=0;depthMark=0;sizeK=Math.min(1.25,Math.max(.75,bite()/CREATURES.REF_BITE));camY=Math.max(0,shark.y-H*.5);shark.ang=0;shark.spd=sharkMax(0)*.25;shark.run=0;shark.air=false;shark.h=0;shark.cool=0;shark.sq=0;
 touch.on=false;touch.drive=0;boost.t=0;boost.cd=0;boost.n=0;shake=0;shark.stun=0;shark.safe=0;surfersCaught=0;surfEaten.fill(0);shark.yaw=shark.yawT=shark.yawTgt=0;shark.yawDir=1;wasFast=false;lastBub=-9;for(const p of parts)p.t=0;for(const p of pops)p.t=0;placeAll();playMusic("game");
 hintT=LS.getItem(HINT_KEY)?0:6;LS.setItem(HINT_KEY,"1")}
function spark(x,y,big){for(const p of parts)if(p.t<=0){const a=Math.random()*6.28,v=rnd(40,140)*(big?1.4:1);p.x=x;p.y=y;p.vx=Math.cos(a)*v;p.vy=Math.sin(a)*v-(big?60:0);p.t=.5;return}}
function addPop(x,y,txt,big){let o=pops[0];for(const p of pops)if(p.t<o.t)o=p;o.x=Math.max(camX+(big?110:50),Math.min(camX+W-(big?110:50),x));o.y=big?Math.max(y,camY+safeTop()+130):y;o.t=big?1.4:1;/* b52: big pop clear of the HUD */o.txt=txt;o.big=!!big;popFit(o)}
/* b53 (QA S52-7): no two live pops overlap. A new big (bonus) pop replaces every other live pop it would touch (one at a time, no half-faded text under it); a new small pop steps up above any live pop it would touch. */
const popW=p=>p.txt.length*(p.big?21:15)+16,popH=p=>p.big?40:30,popHit=(a,b)=>Math.abs(a.x-b.x)*2<popW(a)+popW(b)&&Math.abs(a.y-b.y)*2<popH(a)+popH(b);
function popFit(o){for(let k=0;k<6;k++){let moved=false;for(const q of pops)if(q!==o&&q.t>0&&popHit(o,q)){if(o.big){q.t=0}else{o.y=q.y-(popH(o)+popH(q))/2-2;moved=true}}if(!moved)break}if(!o.big)for(const q of pops)if(q!==o&&q.t>0&&popHit(o,q))q.t=0}
const boatTxt=()=>(surfEaten[2]?` · Sail boats: ${surfEaten[2]}`:"")+(surfEaten[3]?` · Cargo ships: ${surfEaten[3]}`:"")+(surfEaten[4]?` · Oil tankers: ${surfEaten[4]}`:"");
function addScore(n){score+=n}
function feedSurfer(){feed(GROW.SURFER)}
function feed(g){if(shark.lvl>=MAX_LEVEL){shark.meter=need(shark.lvl);return}shark.meter+=g*trait("grow");
 while(shark.meter>=need(shark.lvl)&&shark.lvl<MAX_LEVEL){shark.meter-=need(shark.lvl);shark.lvl++;SFX.grow();addPop(shark.x,shark.y-shark.L*.6,"BIGGER!");buildShark(true);shark.pop=DRAW.POP_S;if(RINGS)for(let i=0;i<10;i++)spark(shark.x,shark.y,1)}}
function beatLen(){return 60/(chip.src?BEAT.CHIPTUNE_BPM:BEAT.PLACEHOLDER_BPM)}
function beatNow(){if(chip.src)return (AC.currentTime-chip.t0)%chip.buf.duration;if(placeholder&&AC)return AC.currentTime-phT0;return elapsed}
// v9c (Jeremy: "small fish by its fin" not eaten): food also gets eaten when it overlaps the drawn BODY, not only the mouth.
// Capsule along the body line from the mouth (+0.48 L) back to the tail fin (-0.55 L), radius = body half-height (0.12 L) + 0.3 x fish size.
const BODY={HEAD:.48,TAIL:.55,R:.12,FR:.3};
function onBody(f){const c=Math.cos(shark.ang),sn=Math.sin(shark.ang),L=shark.L,dx=f.x-shark.x,dy=f.y-shark.y;let u=dx*c+dy*sn;const v=-dx*sn+dy*c;
 u=Math.max(-L*BODY.TAIL,Math.min(L*BODY.HEAD,u));const px=dx-u*c,py=dy-u*sn,r=L*BODY.R+fpx(f)*BODY.FR;return px*px+py*py<r*r}
/* b56 (Jeremy t1637u "only the mouth of a larger fish can kill you"): the kill zone is a small circle at the eater's jaw
   (it faces the way it swims: f.vx sign, as drawn). Jaw placement measured on the drawn sprite (a shark is drawn 2.5 x fpx(f) long, jaw MOUTH.SHARK[0]
   of that ahead of its centre, [1] below, radius [2]; other creatures fpx(f) long), but laid out on TRUE size f.s like every danger contact (v9c, LOOK.K):
   the kill point sits a little behind the drawn jaw, in the head. It only counts while the b55 body contact also holds, so the kill reach is never longer than in b55.
   It kills when it touches your body (spine capsule, radius MOUTH.YOU x your length). Anywhere else on its body = bump (shove). */
const MOUTH={SHARK:[.44,.06,.06],OTHER:[.52,.03,.15],YOU:.14};
function mouthPt(f){const sh=f.kind==="shark",m=sh?MOUTH.SHARK:MOUTH.OTHER,len=f.s*(sh?2.5:1),dir=f.vx<0?-1:1;return [f.x+dir*len*m[0],f.y+len*m[1],len*m[2]]}
function mouthHit(f){const [px,py,r]=mouthPt(f),c=Math.cos(shark.ang),sn=Math.sin(shark.ang),L=shark.L,dx=px-shark.x,dy=py-shark.y;let u=dx*c+dy*sn;u=Math.max(-L*BODY.TAIL,Math.min(L*BODY.HEAD,u));const qx=dx-u*c,qy=dy-u*sn,R=r+L*MOUTH.YOU;return qx*qx+qy*qy<R*R}
function mouth(){const k=shark.L*.48;return [shark.x+Math.cos(shark.ang)*k,shark.y+Math.sin(shark.ang)*k]}
// v10 item 6: per-fish dodge state machine. f.dg 0 none / 1 wiggle / 2 sideways snap; f.da = turn from the flee line (rad); f.dcd cooldown; f.dn dodges this chase
function dodge(f,dt,sprint,dist,L,tvx,tvy,v){const D=DODGE;if(!D.ON||(!sprint&&!D.TIRED)){f.dg=0;return}
 const q=f.s/bite(),near=q>D.NEAR_Q,dd=Math.max(0,Math.min(1,depthOf(f.y)));
 if(f.dg===0){if(f.dcd>0||dist>(sprint?D.R:D.R_TIRED)*L||(near&&f.dn>0))return;f.dg=1;f.dt=0;f.dn++;D.n=(D.n||0)+1;
  const C=q<D.SMALL_Q?D.SMALL:near?D.NEAR:D.MID,base=D.ANG_SHALLOW+(D.ANG_DEEP-D.ANG_SHALLOW)*dd;
  const ang=near?C.ang:Math.min(90,C.ang+(base-D.ANG_SHALLOW)*.5);/* size sets the angle, depth adds up to +10 deg */
  f.ddur=near?D.DUR:C.dur;f.dzig=dd>.5&&Math.random()<D.ZIG_P;
  const cd=near?C.cdS:(D.CD_SHALLOW+(D.CD_DEEP-D.CD_SHALLOW)*dd)*C.cd;f.dcd=Math.max(D.CD_MIN,cd-D.CD_LVL*shark.lvl)+D.WIG+f.ddur;
  const ts=touch.on?Math.sign(angDiff(shark.ang,touch.dir)):0;let side=ts?-ts:(Math.random()<.5?-1:1);/* away from the side the shark turns to */
  const fa=Math.atan2(tvy,tvx),ny=a=>Math.sin(fa+a),b0=Math.max(SURF+f.s*.6,f.band[0]),b1=f.band[1],m=L*1.2;
  const bad=a=>(ny(a)<-.2&&f.y-b0<m)||(ny(a)>.2&&b1-f.y<m);let a=side*ang*Math.PI/180;if(bad(a)){a=-a;if(bad(a))a=0}f.da=a;return}
 f.dt+=dt;if(f.dg===1){f.ph+=dt*40;if(f.dt>=D.WIG){f.dg=2;f.dt=0}return}
 if(f.dzig&&f.dt>=D.ZIG_AT){f.dzig=false;f.da=-f.da}if(f.dt>=f.ddur){f.dg=0}}
function angDiff(a,b){let d=b-a;while(d>Math.PI)d-=6.2832;while(d<-Math.PI)d+=6.2832;return d}
function power(){const max=sharkMax(shark.lvl);return Math.min(1,LAUNCH.K*(shark.spd/max)*(shark.run/H))}
function canLaunch(){return shark.spd>=sharkMax(shark.lvl)*LAUNCH.MIN_SPEED&&power()>=LAUNCH.MIN_POWER}
function launch(){const p=power(),g0=LAUNCH.G*H,hm=LAUNCH.H_MAX*H*p*trait("leap"),vy0=Math.sqrt(2*g0*hm);let T=2*vy0/g0,g=g0,assisted=false;
 if(BEAT.on){const bl=beatLen(),tl=beatNow()+T,d=Math.round(tl/bl)*bl-tl;if(Math.abs(d)*1000<=BEAT.ASSIST_MS){T+=d;g=2*vy0/T;assisted=true}}// time-stretch the arc so it lands on the beat
 shark.air=true;shark.g=g;shark.vy=-vy0;shark.vx=Math.cos(shark.ang)*shark.spd*.85;shark.perfect=assisted;shark.sq=.12;shark.run=0;shark.peak=vy0*vy0/(2*g);
 window.__saLastLaunch={power:p,height:shark.peak,air:T,base:2*vy0/g0,assisted};SFX.launch();for(let i=0;i<8;i++)spark(shark.x,SURF,1);addPop(shark.x,SURF-20,p>.7?"BIG AIR!":"WHOOSH!")}
function fmtT(t){t=Math.floor(t);return Math.floor(t/60)+":"+String(t%60).padStart(2,"0")}
function bestKey(){return mode==="endless"?BEST_KEY+"_endless":BEST_KEY}
function setMode(m){mode=m;LS.setItem(MODE_KEY,m);for(const k of MODES){const b=$("mode_"+k);if(b){b.classList.toggle("sel",k===m);b.setAttribute("aria-pressed",k===m)}}}
let godMode=false;// test hook only: never set by the game
const DEATH_S=1.5,dead={t:0,puffs:[]};let puffSpr=null;
function gameOver(why){if(godMode&&why==="eaten")return;endReason=why;if(why==="eaten"&&state==="play"){state="dead";shark.dead=true;shark.air=false;shark.stun=0;dead.t=0;dead.puffs=[];for(let i=0;i<6;i++)dead.puffs.push({a:rnd(0,6.28),d:rnd(.05,.3),k:rnd(.6,1.1),dl:i*.08});return}endRound()}
function updDead(dt){dead.t+=dt;shark.y+=dt*22;camX+=(shark.x-W/2-camX)*Math.min(1,dt*WORLD.CAM_EASE);if(shake>0)shake-=dt;{const tc=Math.max(0,shark.y-H*.5);camY+=(tc-camY)*Math.min(1,dt*WORLD.CAM_EASE)}if(dead.t>=DEATH_S)endRound()}
function surferCaught(){surfersCaught++}
const surfEaten=[0,0,0,0,0];
/* b57: surfer cutoff is the sail-shrink depth (pastSurf). It does not apply to sailboats. Cargo stops at the black depth (pastCargo). Tankers turn on with pastSurf and stay edible in the black zone. */
function canEatSurf(s){const k=s.k|0;if(k<2)return shark.lvl>=GROW.SURF_LVL&&!pastSurf();if(k===2)return shark.lvl>=SURFACE.SAIL_LVL||pastSurf();if(k===3)return shark.lvl>=SURFACE.CARGO_LVL&&!pastCargo();if(k===4)return pastSurf();return false}
function eatSurf(s,cx,cy){const SD=SURFERS[s.k],pts=SD.pts;addScore(pts);if(s.k<2)feedSurfer();else feed(SD.grow);SFX.pop();if(s.k>=2)SFX.chomp();shark.chomp=.25;addPop(cx,cy-20-(s.k>=2?30:0),"+"+pts+" "+SD.label,true);const n=s.k===4?22:s.k===3?18:s.k===2?12:8;for(let i=0;i<n;i++)spark(cx+(s.k>=2?rnd(-1,1)*(SD.hw||0)*surfDrawK(s)*.6:0),SURF,1);surfEaten[s.k]++;s.zip=s.k>=2?2.4:1.6;if(s.k<2)surferCaught();window.__saLastSurfEat={k:s.k,pts,t:elapsed}}
function updPlay(dt){elapsed+=dt;noteDepth();if(mode==="timed")timeLeft-=dt;if(hintT>0)hintT-=dt;if(mode==="timed"&&timeLeft<=0){timeLeft=0;gameOver("time");return}
 {if(shark.L!==shark.Lt){shark.L+=(shark.Lt-shark.L)*Math.min(1,dt*DRAW.EASE);if(Math.abs(shark.L-shark.Lt)<.05)shark.L=shark.Lt}if(shark.pop>0)shark.pop-=dt;const wt=wK(shark.lvl);if(worldK!==wt){let nk=worldK+(wt-worldK)*Math.min(1,dt*GROW.EASE);if(Math.abs(nk-wt)<1e-4)nk=wt;setWorldK(nk)}}if(shake>0)shake-=dt;if(shark.cool>0)shark.cool-=dt;if(shark.sq>0)shark.sq-=dt;shark.wag+=dt*(4+shark.spd/40);if(shark.chomp>0)shark.chomp-=dt;
 const max=sharkMax(shark.lvl),L=shark.L;
 if(shark.air){// ballistic arc: safe from fish, can grab surfers
  shark.vy+=shark.g*dt;shark.x+=shark.vx*dt;shark.y+=shark.vy*dt;shark.ang=Math.atan2(shark.vy,shark.vx);shark.h=Math.max(0,SURF-shark.y);
  if(shark.y>=SURF&&shark.vy>0){shark.air=false;shark.h=0;shark.y=SURF+2;shark.spd=Math.min(max,Math.hypot(shark.vx,shark.vy)*.6);shark.cool=LAUNCH.COOL;if(!calm)shake=.22;shark.sq=.12;
   for(let i=0;i<12;i++)spark(shark.x,SURF,1);const bl=beatLen(),off=Math.abs(((beatNow()+bl/2)%bl)-bl/2)*1000;window.__saLastLand={offMs:off};
   if(BEAT.on&&off<=BEAT.PERFECT_MS){addScore(BEAT.PERFECT_BONUS);SFX.perfect();addPop(shark.x,SURF-30,"PERFECT! +"+BEAT.PERFECT_BONUS)}}}
 else{
  if(touch.on){const ad=angDiff(shark.ang,touch.dir),pv=Math.abs(Math.sin(touch.dir)-Math.sin(shark.ang))/2,hv=Math.abs(Math.cos(touch.dir)-Math.cos(shark.ang))/2,pk=pv>hv?STEER.PITCH_TURN:1;shark.ang+=ad*Math.min(1,dt*STEER.TURN*trait("turn")*pk)}
  else touch.drive=Math.max(0,touch.drive-dt*STEER.DRIVE_DECAY*2);
  if(boost.t>0)boost.t=Math.max(0,boost.t-dt);if(boost.cd>0)boost.cd=Math.max(0,boost.cd-dt);const bst=boost.t>0&&shark.stun<=0;
  const tgt=shark.stun>0?0:bst?max*BOOST.MUL:max*(touch.on?STEER.MIN+(1-STEER.MIN)*touch.drive:STEER.MIN);/* boost multiplies the speed you are already asking for */
  shark.spd+=(tgt-shark.spd)*Math.min(1,dt*(tgt>shark.spd?STEER.ACC*trait("acc")*(bst?BOOST.ACC:1):STEER.DEC*(shark.spd>max?3:1)));boostUi();// eased = weighty
  shark.x+=Math.cos(shark.ang)*shark.spd*dt;{const sy=Math.sin(shark.ang);shark.y+=sy*shark.spd*dt*(sy>0?diveK(shark.lvl):1)}
  if(shark.spd>max*.45)shark.run+=shark.spd*dt*(shark.spd/max);else shark.run*=Math.exp(-dt*2);shark.run=Math.min(shark.run,H*1.2);
  const fr=shark.spd/max;if(fr>=FAST_SFX.AT&&!wasFast&&elapsed-lastBub>=FAST_SFX.COOL){SFX.bubbles();lastBub=elapsed;for(let i=0;i<3;i++)spark(shark.x-Math.cos(shark.ang)*L*.5,shark.y,0)}wasFast=fr>=FAST_SFX.AT;
  // surface: launch if fast with enough run-up, else bump back down with a ripple
  if(shark.y-L*.08<=SURF){if(Math.sin(shark.ang)<LAUNCH.UP&&shark.cool<=0&&canLaunch())launch();
   else{shark.y=SURF+L*.08;const sn=Math.sin(shark.ang);if(sn<-.5){shark.ang=-shark.ang;shark.spd*=.75;shark.run*=.5;addPop(shark.x,SURF+10,"splish");spark(shark.x,SURF,0)}else if(sn<0)shark.ang=Math.cos(shark.ang)>=0?0:Math.PI}}// steep: bump down; shallow: glide along the surface without losing speed
  }
 if(depthHintT>0)depthHintT-=dt;
 {const k=Math.min(1,dt*WORLD.CAM_EASE),tc=Math.max(0,shark.y-H*.5);if(Math.abs(tc-camY)>H*1.2||Math.abs(shark.x-W/2-camX)>W*1.2){camY=tc;camX=shark.x-W/2}else{camY+=(tc-camY)*k;camX+=(shark.x-W/2-camX)*k}}updTiles();// big jump (teleport) = snap
 const [mx,my]=mouth(),er=L*.2;
 const CR=CREATURES,smax=max,sense=Math.max(H*CR.SENSE,L*CR.SENSE_L);/* v9: notice range also scales with the drawn shark */
 {const c=Math.cos(shark.ang);if(Math.abs(c)>TURN3D.DEAD)shark.yawTgt=c<0?Math.PI:0;const d=(shark.yawTgt||0)-(shark.yaw||0),st=Math.PI/TURN3D.SEC*dt;if(Math.abs(d)>1e-4)shark.yawDir=d>0?1:-1;shark.yaw=(shark.yaw||0)+Math.max(-st,Math.min(st,d));shark.yawT=(shark.yawT||0)+(shark.yaw-(shark.yawT||0))*Math.min(1,dt*TURN3D.TAIL);const H_=window.__saYawHold;if(H_){shark.yaw=H_[0];shark.yawT=H_[1]}}
 for(const f of fish){if(f.off){if(f.retry>0&&(f.retry-=dt)<=0)spawnFish(f,true,f.tile);continue}if(f.fade>0){f.fade-=dt;f.danger=false;if(f.fade<=0){f.off=true;f.retry=rnd(.5,1.1)}continue}if(!f.tiny&&goneAt(f.y))makeTiny(f);/* b55: outgrown band -> fish stay, too small to eat */f.ph+=dt*3;const dx=f.x-shark.x,dy=f.y-shark.y,d2=dx*dx+dy*dy,r=rel(f),dist=Math.sqrt(d2)||1;const eater=!f.tiny&&f.kind!=="plankton"&&f.kind!=="star"&&f.s/bite()>=EAT.RATIO;f.danger=eater;if(f.rest>0)f.rest-=dt;
  let tvx=f.vx>=0?Math.max(20,Math.abs(f.vx)):-Math.max(20,Math.abs(f.vx)),tvy=0;f.st="";
  const food=r<0&&!f.tiny;// v9b (Jeremy): a Size 1 shark eats any fish clearly smaller than its bite (before: plankton only, which left tiny fish next to it uneatable)
  if(!shark.air&&dist<sense){if(food&&f.kind!=="star"){if(f.chase===0)f.dn=0;f.chase+=dt;if(f.chase>CR.FLEE_BURST_S+CR.FLEE_TIRED_S)f.chase=0;const sprint=f.chase<CR.FLEE_BURST_S,v=smax*(f.kind==="plankton"?.15:sprint?fleeK(f):CR.FLEE_TIRED);/* sprint, then tire briefly */tvx=dx/dist*v;tvy=dy/dist*v;f.st="flee";
    if(f.kind!=="plankton")dodge(f,dt,sprint,dist,L,tvx,tvy,v);if(f.dg===2){const a=Math.atan2(tvy,tvx)+f.da;tvx=Math.cos(a)*v;tvy=Math.sin(a)*v}}
   else if(eater&&f.rest<=0&&depthOf(f.y)>=CR.CHASE_MIN_D){const dd=depthOf(f.y),v=smax*(CR.CHASE_SHALLOW+(CR.CHASE_DEEP-CR.CHASE_SHALLOW)*dd);tvx=-dx/dist*v;tvy=-dy/dist*v;f.st="chase";f.chase+=dt;if(f.chase>=CR.GIVEUP_S){f.chase=0;f.rest=CR.REST_S}}}
  else if(f.chase>0)f.chase=Math.max(0,f.chase-dt);
  if(f.dcd>0)f.dcd-=dt;if(f.st!=="flee"&&f.dg){f.dg=0}if(f.st){const k=Math.min(1,dt*(f.dg===2?DODGE.GAIN:2.2));f.vx+=(tvx-f.vx)*k;f.vy+=(tvy-f.vy)*k}else{f.vy*=.97;if(Math.abs(f.vx)<20)f.vx=(f.vx<0?-1:1)*30}
  f.x+=f.vx*dt;f.y+=(f.vy+(f.kind==="star"?0:Math.sin(f.ph)*8))*dt;{const b0=Math.max(SURF+f.s*.6,f.band[0]),b1=f.band[1];if(f.y<b0){f.y=b0;f.vy=Math.abs(f.vy)}else if(f.y>b1){f.y=b1;f.vy=-Math.abs(f.vy)}}// layer-locked
  if(!inWindow(f.x,f.y)){spawnFish(f,true,f.tile);continue}if(f.bump>0)f.bump-=dt;
  if(shark.air||f.tiny)continue;/* b55: tiny fish are harmless and cannot be eaten */
  if(food){const ex=f.x-mx,ey=f.y-my,rr=er+fpx(f)*.4;if(ex*ex+ey*ey<rr*rr||onBody(f)){const pts=ptsOf(f);addScore(pts);feed(growOf(f));SFX.chomp();shark.chomp=.2;addPop(f.x,f.y,"+"+pts);if(RINGS)for(let i=0;i<4;i++)spark(f.x,f.y,0);/* v9c: no bubble circles around the shark */spawnFish(f,true,f.tile)}}
  else{const rr=L*.32+f.s*(f.kind==="shark"?.9:.4);/* v9c: danger/bump contact stays on true size (drawn 1.25x bigger would mean unfair early deaths) */if(d2<rr*rr){if(eater&&!godMode&&elapsed>EAT.GRACE&&mouthHit(f)){gameOver("eaten");return}/* b56 (Jeremy t1637u): in contact, only its MOUTH eats you (kill reach never longer than the b55 contact); its top/body/tail = harmless bump (shove) */
    f.vy+=dy/dist*80;shark.x-=dx/dist*6;shark.y-=dy/dist*6;if(f.bump<=0){SFX.bump();f.bump=.4}}}}
 for(const s of surf){s.ph+=dt*2;if(shark.lvl<SURFACE.SAIL_LVL&&surf.indexOf(s)>=LATE.N_EARLY){s.zip=Math.max(s.zip,.4);continue}if(s.zip>0){s.zip-=dt;if(s.zip<=0)spawnSurf(s,true);continue}
  s.x+=s.vx*dt;const sk=surfDrawK(s),SD=SURFERS[s.k],hw=(SD.hw||18)*sk,mg=60+hw;if(s.x<camX-mg){s.x+=W+2*mg;rollSurf(s)}else if(s.x>camX+W+mg){s.x-=W+2*mg;rollSurf(s)}/* b52: re-rolled off screen, so boats replace surfers as you grow */const boat=s.k>=2,hy=SURFERS[s.k].hy*sk,cx=s.x,cy=SURF-hy;
  if(shark.air){const ex=cx-mx,ey=cy-my,rr=(L*.22+(boat?hw*.8:18*sk))*trait("catchR");
    if(ex*ex+ey*ey<rr*rr){if(canEatSurf(s))eatSurf(s,cx,cy);else if(!(s.bump>0)){s.bump=.8;SFX.bump()}}}
  else if(boat&&Math.abs(cx-mx)<hw+L*.2&&my<SURF+L*.35){if(canEatSurf(s))eatSurf(s,cx,cy);else if(!(s.bump>0)){s.bump=.8;SFX.bump()}}/* b52: boats can also be bitten from below at the surface. b57: cargo refuses once the black zone has been reached; tiny sails do not */
  else if(!boat&&Math.abs(cx-mx)<L*.4&&my<SURF+L*.3&&!(s.bump>0)){s.bump=.6;s.vx=(cx>shark.x?1:-1)*60;SFX.bump();addPop(cx,cy-20,"boing")}
  if(s.bump>0)s.bump-=dt}
 for(const p of parts)if(p.t>0){p.t-=dt;p.x+=p.vx*dt;p.y+=p.vy*dt;p.vx*=.94;p.vy=p.vy*.94+140*dt}}
// MIP LEVELS: sprites are baked large; drawing them shrunk 4-10x is costly (the filter samples the big source every frame).
// mip(s,k) returns a cached half/quarter/... copy close to the drawn scale k (dest px per source px). Same dest rect, so art is unchanged.
// TRIM: crop a baked sprite to its visible pixels once (sprites carry wide transparent padding for glow/shadow);
// fewer blended pixels per draw. ox/oy = where the crop sits inside the original.
function trim(s){if(s._t)return s._t;let t=s;try{const w=s.width,h=s.height,d=s.getContext("2d").getImageData(0,0,w,h).data;let x0=w,y0=h,x1=-1,y1=-1;
 for(let y=0;y<h;y++)for(let x=0;x<w;x++)if(d[(y*w+x)*4+3]>3){if(x<x0)x0=x;if(x>x1)x1=x;if(y<y0)y0=y;if(y>y1)y1=y}
 if(x1>=x0&&(x1-x0+1)*(y1-y0+1)<w*h*.9){t=mk(x1-x0+1,y1-y0+1);t.getContext("2d").drawImage(s,-x0,-y0);t.ox=x0;t.oy=y0}}catch(e){}if(t===s){t.ox=0;t.oy=0}s._t=t;return t}
function mip(s,k){if(k>=.55||!s.width)return s;if(!s._m)s._m=[s];let n=Math.min(5,Math.floor(Math.log2(.55/k))+1),m=s._m;
 while(m.length<=n){const a=m[m.length-1],w=Math.max(1,Math.round(a.width/2)),h=Math.max(1,Math.round(a.height/2));if(a.width<=2||a.height<=2)break;const c=mk(w,h),g=c.getContext("2d");g.imageSmoothingQuality="high";g.drawImage(a,0,0,w,h);m.push(c)}
 return m[Math.min(n,m.length-1)]}
function wT(){X.setTransform(DPR,0,0,DPR,-camX*DPR,-camY*DPR)}// world -> screen
function edgeArrow(wx,wy,col){const sx=wx-camX,sy=wy-camY;if(sx>-10&&sx<W+10&&sy>-10&&sy<H+10)return;const ex=Math.max(18,Math.min(W-18,sx)),ey=Math.max(70,Math.min(H-18,sy)),a=Math.atan2(sy-ey,sx-ex);
 X.save();X.translate(ex,ey);X.rotate(a);X.fillStyle=col;X.strokeStyle=P.ink;X.lineWidth=3;X.beginPath();X.moveTo(13,0);X.lineTo(-9,-12);X.lineTo(-9,12);X.closePath();X.fill();X.stroke();X.restore()}
// DARKNESS: shallow-ish (dk<DIM_AT) = one full-screen vignette over everything. Deeper, the water behind is already ~black, so
// the same falloff is applied per object (creatures, scenery, seabed strips) as alpha instead: same look, no full-screen pass.
const DIM_AT=.6;function nhMax(){return FX>=3?40:FX===2?(busy?8:14):FX===1?5:0}// at most 14 glow halos per frame (perf)
const DK={dk:0,ga:0,R:1,per:false};
function darkSetup(){const d=Math.max(0,depthRaw(shark.y)),dk=d<=ZONE.SURF?0:Math.max(0,Math.min(1,(d-ZONE.SURF)/(ZONE.CARGO-ZONE.SURF)));/* b57: vignette was depthOf .34 → full at .86. Now it stays off through the light surfer zone and reaches full black at the cargo edge */DK.dk=dk;DK.ga=Math.min(.88,dk*.85)*(1-LATE.DARK_CUT*lateK());DK.R=Math.max(W,H)*(1.6-dk*.75);DK.per=dk>=DIM_AT||FX===0}
function vigA(x,y){const u=Math.hypot(x-shark.x,y-shark.y)/DK.R;const a=u<.156?0:u<.536?(u-.156)/.38*.25:u<1?.25+(u-.536)/.464*.72:.97;return a*DK.ga}
const FAR_FOG=.4;/* v10 item 12 step 5: far creatures fade toward the murk (contrast -40% at the screen edge, none near the shark) */function farFog(x,y){const u=(Math.hypot(x-shark.x,y-shark.y)/(.5*Math.hypot(W,H))-.35)/.5;return 1-FAR_FOG*(1-.6*lateK())*Math.max(0,Math.min(1,u))}/* b53: less far fog late in the game */
function dimAt(x,y){return DK.per?1-vigA(x,y):1}
function drawPlay(t){
 if(lightProbe){for(const f of fish){f.off=true;f.retry=0}}
 X.font="900 22px system-ui,sans-serif";X.textAlign="center";X.textBaseline="middle";X.lineWidth=5;X.strokeStyle=P.ink;const top=camY-120,bot=camY+H+120;
 let onScr=0;for(const f of fish){if(f.off||f.y<top||f.y>bot||f.x<camX-f.s*3||f.x>camX+W+f.s*3)continue;onScr++;let s,sc;const flip=f.vx<0?-1:1;X.globalAlpha=dimAt(f.x,f.y)*farFog(f.x,f.y)*(f.fade>0?f.fade/VANISH.FADE:1);
  if(f.kind==="shark"){const sp=sharkSpr[f.pal];s=f.st==="chase"&&Math.sin(t*8+f.ph)>0?sp.o:sp;sc=(fpx(f)*2.5)/sp.L;X.setTransform(DPR*flip*sc,0,0,DPR*sc,(f.x-camX)*DPR,(f.y-camY)*DPR);X.rotate(Math.max(-.5,Math.min(.5,f.vy/(Math.abs(f.vx)+40)))*flip);const dw=s.width/DPR,dh=s.height/DPR,T=trim(s);X.drawImage(mip(T,sc),-dw/2-sp.L*.05+T.ox/DPR,-dh/2+T.oy/DPR,T.width/DPR,T.height/DPR)}
  else{s=f.sp>=0&&(f.kind==="fish"||f.kind==="glow")?specSpr[f.sp]:f.kind==="glow"?glowSpr[f.pal]:f.kind==="plankton"?plankSpr[f.pal]:f.kind==="angler"?anglerSpr:f.kind==="octo"?octoSpr[f.pal]:f.kind==="star"?starSpr[f.pal]:fishSpr[f.tier][f.pal];sc=fpx(f)/s.base;
   const wob=f.kind==="octo"?1+Math.sin(t*3+f.ph)*.06:1;X.setTransform(DPR*flip*sc,0,0,DPR*sc*wob,(f.x-camX)*DPR,(f.y-camY)*DPR);if(f.dg===1)X.rotate(Math.sin(f.dt*70)*.22);/* v10: readable dodge wiggle */if(f.kind==="star")X.rotate(f.ph*.05);const dw=s.width/DPR,dh=s.height/DPR,T=trim(s);X.drawImage(mip(T,sc),-dw/2+T.ox/DPR,-dh/2+T.oy/DPR,T.width/DPR,T.height/DPR);{const lz=lateK();if(lz>0&&f.kind!=="plankton"&&rel(f)<0){/* b53: late game, food fish lit a little so they read against the deep water */const ga=X.globalAlpha;X.globalCompositeOperation="lighter";X.globalAlpha=ga*.45*lz;X.drawImage(mip(T,sc),-dw/2+T.ox/DPR,-dh/2+T.oy/DPR,T.width/DPR,T.height/DPR);X.globalCompositeOperation="source-over";X.globalAlpha=ga}}}}
 X.globalAlpha=1;busy=onScr>14||SURF>camY&&SURF<camY+H;/* b53 (QA S52-6): with the waterline on screen the full-screen fog and colour-grade passes are skipped (2 full-screen upscaled draws; ~2.5x cost at 4x CPU). b51 was fast there only because divers set busy at the surface; b52 removed divers and so drew both every surface frame. */
 wT();
 for(const s of surf){if(s.zip>0||SURF>bot)continue;const sp=surfSpr[s.k],dw=sp.width/DPR,dh=sp.height/DPR,y=SURF+Math.sin(s.ph)*2;{const k=surfDrawK(s);X.setTransform((s.vx<0?-DPR:DPR)*k,0,0,DPR*k,(s.x-camX)*DPR,(y-camY)*DPR)}X.drawImage(sp,-dw/2,-dh*(sp.wl||.89),dw,dh)}
 wT();const L=shark.L,ks=L/sprC.L,max=sharkMax(shark.lvl),sr=shark.spd/max;
 if(shark.air){const k=Math.max(.25,1-shark.h/(H*.35));X.fillStyle="rgba(4,30,50,.35)";X.beginPath();X.ellipse(shark.x,SURF+4,L*.4*k,6*k,0,0,7);X.fill()}
 else{if(sr>.35){const c=Math.cos(shark.ang),sn=Math.sin(shark.ang),bx=shark.x-c*L*.55,by=shark.y-sn*L*.55,len=L*(.3+Math.min(sr,1.6)*.9);X.strokeStyle="rgba(235,252,255,"+(.2+Math.min(sr,1)*.4)+")";X.lineWidth=3;X.beginPath();
   for(const side of[-1,1]){X.moveTo(bx-sn*side*L*.08,by+c*side*L*.08);X.lineTo(bx-c*len-sn*side*len*.25,by-sn*len+c*side*len*.25)}X.stroke()}
  if(boost.t>0&&!calm){/* b52 boost wake: a pale V of churned water behind the tail */const c=Math.cos(shark.ang),sn=Math.sin(shark.ang),bx=shark.x-c*L*.6,by=shark.y-sn*L*.6,a=Math.min(1,boost.t/.3),wl=L*(1.1+Math.min(sr,2.2)*.5);for(const side of[-1,1]){const ex=bx-c*wl-sn*side*wl*.32,ey=by-sn*wl+c*side*wl*.32,gw=X.createLinearGradient(bx,by,ex,ey);gw.addColorStop(0,"rgba(240,252,255,"+(.55*a)+")");gw.addColorStop(1,"rgba(240,252,255,0)");X.strokeStyle=gw;X.lineWidth=5;X.beginPath();X.moveTo(bx,by);X.quadraticCurveTo(bx-c*wl*.5-sn*side*wl*.08,by-sn*wl*.5+c*side*wl*.08,ex,ey);X.stroke()}
   X.fillStyle="rgba(240,252,255,"+(.35*a)+")";for(let i=0;i<6;i++){const k=((t*3+i/6)%1),r=L*(.02+.03*k);X.beginPath();X.arc(bx-c*wl*k+Math.sin(i*7.3+t*9)*L*.06,by-sn*wl*k+Math.cos(i*5.1+t*8)*L*.06,r,0,7);X.fill()}}
  const pw=power(),ok=canLaunch();if(RINGS&&pw>.03){X.lineWidth=ok?5:3;X.strokeStyle=ok?"rgba(255,210,63,.95)":"rgba(235,252,255,.6)";X.beginPath();X.arc(shark.x,shark.y,L*.62,-Math.PI/2,-Math.PI/2+pw*6.283);X.stroke()}}
 const sq=shark.sq>0?Math.sin(shark.sq/.12*Math.PI):0,wob=shark.dead?0:Math.sin(shark.wag)*.04*(shark.air?0:1);
 X.setTransform(DPR,0,0,DPR,(shark.x-camX)*DPR,(shark.y-camY)*DPR);const gp=shark.pop>0?Math.sin((1-shark.pop/DRAW.POP_S)*Math.PI)*.22:0,sxk=ks*(1+sq*.15+gp),syk=ks*(1-sq*.18+gp);
 const s=shark.chomp>0?sprO:sprC,dw=s.width/DPR,dh=s.height/DPR,ox=-dw/2-sprC.L*.05;
 if(shark.dead){const flip=(Math.cos(shark.ang)<0?-1:1)*Math.cos(Math.PI*Math.min(1,dead.t/.7));X.rotate(shark.ang);X.scale(sxk,syk*flip);X.drawImage(s,ox,-dh/2,dw,dh)}
 else{/* b52 3D turn: no instant mirror. Front and tail halves are squashed by cos(yaw) (tail lags), pitch fades mid-turn, belly light and a head-on view show at the midpoint */
  const yw=shark.yaw||0,cF=Math.cos(yw),cT=Math.cos(shark.yawT||0),sw=Math.sin(yw),p=Math.atan2(Math.sin(shark.ang),Math.abs(Math.cos(shark.ang))),th=p*cF*(TURN3D.PITCH_MIN+(1-TURN3D.PITCH_MIN)*Math.abs(cF))+TURN3D.BANK*sw*(shark.yawDir||1)+wob;
  X.rotate(th);const split=Math.abs(cF-cT)>.01||Math.abs(sw)>.01,bl=Math.abs(sw)*.7,hd=Math.max(0,1-Math.abs(cF)/TURN3D.HEAD);window.__saTurn={cF,cT,head:hd,split};
  if(!split){X.save();X.scale(cF,1);X.scale(sxk,syk);X.drawImage(s,ox,-dh/2,dw,dh);X.restore()}
  else{/* b53 3D turn: spine slices tail->head; yaw goes from the tail's (lagging) yaw to the head's; positions integrate along the spine from mid-body */
   const N=TURN3D.N,yH=yw,yT=shark.yawT||0,sl=dw/N,P=TURN3D.PERSP*dw,sg=shark.yawDir||1,arc=-Math.abs(sw)*L*TURN3D.ARC;const S=[];let px=0,pz=0;const yawAt=i=>{const t=(i+.5)/N;return yT+(yH-yT)*t*t*(3-2*t)};
   const pos=new Array(N);{const m=N>>1;px=0;pz=0;for(let i=m;i<N;i++){const a=yawAt(i);pos[i]=[px+Math.cos(a)*sl/2,pz+Math.sin(a)*sl/2];px+=Math.cos(a)*sl;pz+=Math.sin(a)*sl}px=0;pz=0;for(let i=m-1;i>=0;i--){const a=yawAt(i);px-=Math.cos(a)*sl;pz-=Math.sin(a)*sl;pos[i]=[px+Math.cos(a)*sl/2,pz+Math.sin(a)*sl/2]}}
   const cx0=ox+dw/2;for(let i=0;i<N;i++){const a=yawAt(i),[x,z]=pos[i],f=P/(P-z);S.push({i,a,x:(cx0+x)*f,z,f,c:Math.cos(a)})}
   S.sort((p,q)=>p.z-q.z);const zmax=dw*.5;X.save();X.scale(sxk,syk);X.translate(0,arc/syk);const SW=s.width/N;
   for(const q of S){const w=q.c*sl*q.f,y=q.z*TURN3D.TILT;if(Math.abs(w)<.05)continue;X.save();X.translate(q.x,y);X.scale(w/sl,q.f);const sx=q.i*SW,ow=q.i<N-1?SW*.35:0;X.drawImage(s,sx,0,SW+ow,s.height,-sl/2,-dh/2,sl+ow/DPR,dh);
    const bA=bl*Math.max(0,Math.sin(q.a))*.9;if(bA>.02&&sprB&&s===sprC){X.globalAlpha=bA;X.drawImage(sprB,sx,0,SW,s.height,-sl/2,-dh/2,sl,dh);X.globalAlpha=1}
    const dA=TURN3D.FAR_DARK*Math.max(0,-q.z/zmax);if(dA>.02&&sprK){X.globalAlpha=Math.min(.6,dA);X.drawImage(sprK,sx,0,SW,s.height,-sl/2,-dh/2,sl,dh);X.globalAlpha=1}X.restore()}
   X.restore();window.__saTurn.slices=N;
   const hq=S.find(q=>q.i===N-3)||S[S.length-1];if(hd>0&&sprF){const fw=L*.5*hq.f,fh=fw*sprF.height/sprF.width,ha=Math.min(1,hd*2.4);X.save();X.globalAlpha=ha*ha*(3-2*ha);X.drawImage(sprF,hq.x*sxk-fw/2,hq.z*TURN3D.TILT*syk+arc-fh*.5,fw,fh);X.globalAlpha=1;X.restore()}}}
 wT();
 if(RINGS&&shark.pop>0){const e=1-shark.pop/DRAW.POP_S;X.globalAlpha=1-e;X.strokeStyle="#ffe14d";X.lineWidth=4;X.beginPath();X.arc(shark.x,shark.y,L*(.45+e*.5),0,6.283);X.stroke();X.globalAlpha=1}// grow pop ring
 if(shark.dead){const p=Math.min(1,dead.t/1.3);for(const q of dead.puffs){const e=Math.max(0,Math.min(1,(dead.t-q.dl)/1.2));if(e<=0||e>=1)continue;const r=L*(.18+.42*e)*q.k,x=shark.x+Math.cos(q.a)*L*q.d*(1+e),y=shark.y+Math.sin(q.a)*L*q.d*(1+e)-e*L*.15;X.globalAlpha=(1-e)*.8;X.drawImage(puffSpr,x-r,y-r,r*2,r*2)}X.globalAlpha=1}
 if(FX>=1&&gradeSpr&&!busy){/* v10 item 12: baked vignette in deep water too (off when frames slow) */X.setTransform(1,0,0,1,0,0);X.drawImage(gradeSpr,0,0,X.canvas.width,X.canvas.height)}
 // darkness: the deeper, the smaller the circle of light around you
 const dk=DK.dk;if(dk>0){X.setTransform(1,0,0,1,0,0);const R=DK.R*DPR,sx=(shark.x-camX)*DPR,sy=(shark.y-camY)*DPR;X.globalAlpha=DK.ga;
  X.imageSmoothingEnabled=false;if(!DK.per)X.drawImage(vigSpr,sx-R*2,sy-R*2,R*4,R*4);X.imageSmoothingEnabled=true;// nearest sampling: a smooth 512px gradient magnified ~10x has no visible steps, and skips a costly full-screen filterX.globalAlpha=1;
  // glowing fish shine through the dark
  X.globalCompositeOperation="lighter";let nh=0,ng=0;/* item 12: at most 2 additive glows (halos+lures) on screen */for(const f of fish)if(!f.off&&f.y>top&&f.y<bot&&f.x>camX-f.s*3&&f.x<camX+W+f.s*3){const flip2=f.vx<0?-1:1;
   if(f.kind==="glow"&&!(f.sp>=0)){if(++nh>nhMax()||++ng>2)continue;const r=f.s*.5*lk(f);X.setTransform(DPR,0,0,DPR,0,0);X.globalAlpha=.11+.03*Math.sin(t*3+f.ph);/* v10 gfx: dimmer deep halos (poster murk) */X.drawImage(haloSpr[f.pal],f.x-camX-r*1.2,f.y-camY-r*.8,r*2.4,r*1.6)}// small baked halo (cheap) instead of re-drawing the whole sprite
   else if(f.kind==="angler"){if(++ng>2)continue;const sc=f.s/anglerSpr.base,lx=(f.x+flip2*f.s*.6*(48/anglerSpr.base))-camX,ly=f.y-f.s*.56-camY,r=f.s*(.32+.04*Math.sin(t*4+f.ph));X.setTransform(DPR,0,0,DPR,0,0);X.globalAlpha=.35;X.drawImage(lureSpr,lx-r,ly-r,r*2,r*2)}
   else if(f.kind==="plankton"){if(++nh>nhMax())continue;const g=plankSpr[f.pal],sc=f.s/g.base;X.setTransform(DPR*sc,0,0,DPR*sc,(f.x-camX)*DPR,(f.y-camY)*DPR);X.globalAlpha=.5;X.drawImage(mip(g,sc),-g.width/DPR/2,-g.height/DPR/2,g.width/DPR,g.height/DPR)}}X.globalAlpha=1;X.globalCompositeOperation="source-over";wT()}
 wT()}
function drawHud(){X.setTransform(DPR,0,0,DPR,0,0);const top=safeTop()+8,mw=Math.min(150,W*.36),mx=(W-mw)/2,my=top+12,fr=Math.min(1,shark.meter/need(shark.lvl));
 X.fillStyle=P.ink;X.fillRect(mx-3,my-3,mw+6,22);X.fillStyle="#bfe9ff";X.fillRect(mx,my,mw,16);X.fillStyle="#7be04a";X.fillRect(mx,my,mw*fr,16);
 X.font="900 13px system-ui,sans-serif";X.fillStyle=P.ink;X.textAlign="center";X.textBaseline="top";X.fillText(shark.lvl>=MAX_LEVEL?"MAX SIZE":"SIZE "+(shark.lvl+1),W/2,my+1);
 X.font="900 32px system-ui,sans-serif";X.lineJoin="round";X.lineWidth=7;X.strokeStyle=P.ink;X.textAlign="left";X.strokeText("🐟"+score,12,top);X.fillStyle="#fff";X.fillText("🐟"+score,12,top);
 const tl=Math.ceil(timeLeft),ts=mode==="endless"?"⏱"+fmtT(elapsed):"⏱"+tl;X.textAlign="right";X.strokeText(ts,W-12,top);X.fillStyle=mode==="timed"&&tl<=10?"#ffd23f":"#fff";X.fillText(ts,W-12,top);
 if(hintT>0){X.globalAlpha=Math.min(1,hintT);X.textAlign="center";X.font="800 19px system-ui,sans-serif";X.lineWidth=6;const y=H*.62;X.strokeText("Swim down to build speed,",W/2,y);X.strokeText("then swim up fast to leap!",W/2,y+24);X.fillStyle="#fff";X.fillText("Swim down to build speed,",W/2,y);X.fillText("then swim up fast to leap!",W/2,y+24);X.globalAlpha=1}
 {const dRaw=Math.max(0,depthRaw(shark.y)),d=Math.max(0,Math.min(1,dRaw/ZONE.CARGO)),mx2=W-16,y0=top+80,y1=H-14,hh=y1-y0;X.lineWidth=3;X.strokeStyle=P.ink;for(let i=0;i<ZONES.length;i++){const a=ZONES[i].d,b2=i+1<ZONES.length?ZONES[i+1].d:1;X.fillStyle=ZONES[i].col;X.fillRect(mx2-6,y0+a*hh,12,(b2-a)*hh)}X.strokeRect(mx2-6,y0,12,hh);
  const my2=y0+Math.max(0,Math.min(1,d))*hh;X.fillStyle="#fff";X.beginPath();X.moveTo(mx2-8,my2);X.lineTo(mx2-20,my2-7);X.lineTo(mx2-20,my2+7);X.closePath();X.fill();X.stroke();
  const m=Math.max(0,Math.round((shark.y-SURF)/H*60)),z=ZONES.filter(q=>q.d<=d+1e-9).pop();X.font="800 13px system-ui,sans-serif";X.textAlign="right";X.textBaseline="middle";X.lineWidth=4;const lab=(z?z.name:"")+" "+m+" m";X.strokeText(lab,mx2-24,my2);X.fillStyle="#fff";X.fillText(lab,mx2-24,my2)}
 X.textAlign="left"}
function endRound(){state="over";shark.air=false;shake=0;C.style.transform="";const eaten=endReason==="eaten";$("reason").textContent=eaten?"Gulp!":"Time's up!";$("reason").className=eaten?"gulp":"";
 const bk=bestKey();best=+(LS.getItem(bk)||0);if(score>best){best=score;LS.setItem(bk,String(best))}$("final").textContent=score;$("bestTxt").textContent=(score>=best&&score>0?"🏆 New best! ":"Best: ")+best+(mode==="endless"?" (Endless)":" (Timed)");
 $("stats").textContent=mode==="endless"?`Surfers eaten: ${surfersCaught}${boatTxt()} · Survived ${fmtT(elapsed)}`:`Surfers eaten: ${surfersCaught}${boatTxt()}`;
 $("roundNote").textContent=mode==="endless"?"Endless: ends only when you get eaten.":`Round length: ${roundLen} seconds.`;if(eaten)SFX.gulp();else SFX.end();phStop();chipStop();chip.want=false;show("overUi")}

// ---------- shared draw ----------
function drawWater(t){darkSetup();X.setTransform(1,0,0,1,0,0);const top=camY,bot=camY+H,BLACK=SURF+ZONE.CARGO*(BED-SURF),cw=C.width;/* b57: the gradient ends at the cargo edge (was BED+0.35 screens, depthRaw ~1.08). Below that the same black continues with no floor */
 if(top<SURF){const o=Math.round((((camX*.3)%W)+W)%W*DPR),y=Math.round(-top*DPR);X.drawImage(skySpr,-o,y);X.drawImage(skySpr,skySpr.width-o,y)}
 // color-shift fake depth: ONE stretched fill of the baked gradient for the visible water, flat dark cap below it
 {const w0=Math.max(SURF,top),w1=Math.min(BLACK,bot);if(w1>w0){const k=512/(BLACK-SURF);X.imageSmoothingEnabled=false;X.drawImage(gradSpr,0,(w0-SURF)*k,1,Math.max(.01,(w1-w0)*k),0,Math.floor((w0-top)*DPR),cw,Math.ceil((w1-w0)*DPR)+1);X.imageSmoothingEnabled=true}
  if(bot>BLACK){const y=Math.max(BLACK,top);X.fillStyle=CAP_COL;X.fillRect(0,Math.floor((y-top)*DPR),cw,Math.ceil((bot-y)*DPR)+1)}}
 if(FX>=1&&top<SURF+H*.9&&bot>SURF){const o=Math.round((((camX*.6+t*6)%W)+W)%W*DPR),y=Math.round((SURF-top)*DPR);X.drawImage(sunSpr,-o,y);X.drawImage(sunSpr,sunSpr.width-o,y)}
 // scenery from the tile pool (only nearby tiles exist)
 if(!lightProbe)for(const T of tiles)for(const o of T.deco){const sp=decoSpr[o.k],x=o.x-camX,y=o.y-top;if(x+sp.w*o.s<0||x-sp.w*o.s>W||y+sp.h*o.s<0||y-sp.h*o.s>H)continue;const sc=o.s,d=Math.max(0,depthRaw(o.y));let a=dimAt(o.x,o.y);if(o.k==="spire"){const t=Math.max(0,Math.min(1,(d-ZONE.SURF)/(ZONE.CARGO-ZONE.SURF)));a*=.2+.35*t}/* b57: spires fade in from the sail edge to the black edge, so one silhouette cannot drop the water by a whole lighting step */X.setTransform(sc,0,0,sc,x*DPR,y*DPR);X.globalAlpha=a;const Td=trim(sp);X.drawImage(Td,-sp.ox*DPR+Td.ox,-sp.oy*DPR+Td.oy)}X.globalAlpha=1;
 X.setTransform(1,0,0,1,0,0);if(FX>=1&&!busy&&fogSpr&&bot>SURF){X.imageSmoothingEnabled=false;const w0=Math.max(SURF,top),k=512/(BLACK-SURF),h0=Math.max(.01,Math.min(512,(Math.min(bot,BLACK)-w0)*k));if(h0>.01)X.drawImage(fogSpr,0,Math.min(511,(w0-SURF)*k),1,h0,0,Math.floor((w0-top)*DPR),C.width,Math.ceil(h0/k*DPR)+1);X.imageSmoothingEnabled=true}// v10 gfx step 2 (skipped on a busy screen to stay in the perf budget): depth fog. b57: stretched to the cargo edge, not the old bed
 {const lk2=lateK();if(lk2>0&&bot>SURF){const top=camY,cw=C.width,y0=Math.max(SURF,top);X.globalCompositeOperation="lighter";X.globalAlpha=lk2;X.fillStyle=LATE.LIFT;X.fillRect(0,Math.floor((y0-top)*DPR),cw,Math.ceil((bot-y0)*DPR)+1);X.globalAlpha=1;X.globalCompositeOperation="source-over"}}/* b53: late-game deep-water lift *//* drawn after the depth fog so the whole deep screen is lifted evenly */
 /* b48: no seabed strip, vents or lava sparks: the water just keeps getting darker, down forever. */
 // floating particles (screen space, parallax)
 X.setTransform(DPR,0,0,DPR,0,0);const d0=Math.max(0,depthRaw(camY+H/2)),lit=d0<ZONE.SURF,n=FX===0?0:busy||FX===1?14:lit?46:80;{const m=FX===0?0:busy||FX===1?16:murk.length;for(let L=0;L<2;L++){X.fillStyle=L?"rgba(42,69,88,.4)":"rgba(42,69,88,.25)";const k=L?.8:.35;for(let i=L;i<m;i+=2){const p=murk[i],x=(((p.x*W-camX*k+Math.sin(t*.3+i)*6)%W)+W)%W,y=(((p.y*H-t*p.sp*.4-camY*k)%H)+H)%H,r=p.r*(1+L);if(y+top<SURF)continue;X.fillRect(x-r,y-r,r*2,r*2)}}}X.fillStyle=lit?"rgba(200,225,240,.3)":"rgba(110,130,150,.3)";/* b57: bright specks through the surfer zone (was murky from depthOf .3) */
 for(let i=0;i<n;i++){const p=snow[i],x=(((p.x*W-camX*.5)%W)+W)%W,y=(((p.y*H-t*p.sp*(lit?-1:1)-camY*.5)%H)+H)%H,r=p.r*(lit?1.6:1);if(y+top<SURF)continue;X.fillRect(x-r,y-r,r*2,r*2)}
 if(n&&!busy&&FX>=2){/* v10 gfx step 4: a few rising bubbles */X.strokeStyle="rgba(200,230,255,.35)";X.lineWidth=1;X.beginPath();for(let i=0;i<n;i+=7){const p=snow[i],x=(((p.x*W*1.3-camX*.7+Math.sin(t*2+i)*3)%W)+W)%W,y=(((p.y*H-t*(20+p.sp*2)-camY*.7)%H)+H)%H,r=1+p.r*1.4;if(y+top<SURF+6)continue;X.moveTo(x+r,y);X.arc(x,y,r,0,6.3)}X.stroke()}
 const sy=SURF-top;if(sy>-10&&sy<H+10){X.lineCap="round";/* v10 gfx step 2: white swoosh marks dropped */
  X.strokeStyle="#e8fbff";X.lineWidth=4;X.beginPath();const st=busy?46:24,x0=-(((camX%st)+st)%st);for(let x=x0;x<=W+st;x+=st){const y=sy+Math.sin(t*2+(x+camX)*.05)*2.5;x===x0?X.moveTo(x,y):X.lineTo(x,y)}X.stroke()}}
function drawFx(dt,screen){X.setTransform(DPR,0,0,DPR,screen?0:-camX*DPR,screen?0:-camY*DPR);X.fillStyle="#e8fbff";X.strokeStyle=P.ink;X.lineWidth=1.5;for(const p of parts)if(p.t>0){const r=3+p.t*8;X.beginPath();X.arc(p.x,p.y,r,0,7);X.fill();X.stroke()}
 X.textAlign="center";X.textBaseline="middle";X.lineJoin="round";for(const p of pops)if(p.t>0){p.t-=dt*1.1;p.y-=dt*40;X.globalAlpha=Math.min(1,p.t*2);if(p.big){/* b52: bonus prey pop, bigger and gold */X.font="900 34px system-ui,sans-serif";X.lineWidth=8;X.strokeStyle="#3a2600";X.strokeText(p.txt,p.x,p.y);const gg=X.createLinearGradient(0,p.y-17,0,p.y+17);gg.addColorStop(0,"#fff3b0");gg.addColorStop(.5,"#ffc61a");gg.addColorStop(1,"#c98a00");X.fillStyle=gg;X.fillText(p.txt,p.x,p.y)}else{X.font="900 24px system-ui,sans-serif";X.lineWidth=6;X.strokeStyle=P.ink;X.strokeText(p.txt,p.x,p.y);X.fillStyle=P.yel;X.fillText(p.txt,p.x,p.y)}}X.globalAlpha=1;X.textAlign="left"}

// ---------- loop ----------
let last=0,raf=0,fpsT=0,fpsN=0,fps=0;const perf={frames:0,js:0,dtSum:0,reset(){this.frames=0;this.js=0;this.dtSum=0}};
const PORTRAIT_MQ=matchMedia("(orientation: portrait)"),NO_ROT=/[?&]portrait/.test(location.search);fsRot=PORTRAIT_MQ.matches&&!NO_ROT;PORTRAIT_MQ.addEventListener("change",()=>{fsRot=PORTRAIT_MQ.matches&&!NO_ROT});
function frame(now){raf=requestAnimationFrame(frame);let dt=(now-last)/1000;if(state!=="play"&&state!=="dead"&&dt<1/31)return;// menus: ~30 fps
 last=now;if(dt>.1)dt=.1;const t0=performance.now(),t=now/1000;
 if(state==="play"&&!fsRot)updPlay(dt);else if(state==="dead")updDead(dt);else if(state==="title")updTitle(dt);
 drawWater(t);if(state==="play"||state==="over"||state==="dead"){if(shake>0){C.style.transform=`translate(${(Math.random()-.5)*6}px,${(Math.random()-.5)*6}px)`;C._sh=1}else if(C._sh){C.style.transform="";C._sh=0}drawPlay(t);drawFx(dt);drawHud()}
 else{X.setTransform(DPR,0,0,DPR,0,0);if(state==="title"||state==="credits")drawTitle(t);drawFx(dt,true)}
 if(SHOW_FPS){fpsN++;fpsT+=dt;if(fpsT>.5){fps=Math.round(fpsN/fpsT);fpsN=0;fpsT=0}X.setTransform(DPR,0,0,DPR,0,0);X.font="bold 14px monospace";X.fillStyle="#fff";X.textAlign="left";X.fillText(fps+" fps",8,H-14)}
 perf.frames++;perf.dtSum+=dt;perf.js+=performance.now()-t0;if(state==="play"&&ADAPT_ON)adaptStep(dt)}
function adaptStep(dt){if(dt>=.1)return;adapt.t+=dt;adapt.n++;adapt.sum+=dt;if(adapt.t<ADAPT.WIN_S)return;const ms=adapt.sum/adapt.n*1000;adapt.t=adapt.n=adapt.sum=0;
 if(ms>ADAPT.SLOW_MS){adapt.good=0;if(FX>1)FX=1;else if(RS0*RSK*ADAPT.RS_STEP>=ADAPT.RS_MIN-1e-9&&RSK*ADAPT.RS_STEP>=ADAPT.RS_MIN-1e-9){RSK*=ADAPT.RS_STEP;resize(1)}else if(FX>0)FX=0;else return;adapt.steps++;adapt.log.push({ms:Math.round(ms),fx:FX,rs:+(RS0*RSK).toFixed(3)})}
 else if(ms<ADAPT.FAST_MS&&++adapt.good>=ADAPT.GOOD_WIN){adapt.good=0;if(FX<Math.min(1,FX0))FX++;else if(RSK<1){RSK=Math.min(1,RSK/ADAPT.RS_STEP);resize(1)}else if(FX<FX0)FX++;else return;adapt.log.push({ms:Math.round(ms),fx:FX,rs:+(RS0*RSK).toFixed(3),up:1})}}
function startLoop(){if(!raf){last=performance.now();raf=requestAnimationFrame(frame)}}
function stopLoop(){cancelAnimationFrame(raf);raf=0}
document.addEventListener("visibilitychange",()=>{if(document.hidden){stopLoop();if(music.cur)music.cur.pause();if(AC)AC.suspend()}else{startLoop();if(AC)AC.resume();if(music.cur&&musOn())music.cur.play().catch(()=>{})}});

// ---------- UI ----------
function hideAll(){for(const id of["titleUi","overUi","credUi","pickUi","tap","boost"])$(id).classList.add("hide")}
function show(id){hideAll();$(id).classList.remove("hide")}
// steering (v10 ANALOG, Jeremy): speed = how far the finger is from its FIRST touch point (tiny move = slow, FULL x screen width or more =
// top speed for its size). Direction = where the finger is moving, used at once (no 3 px dead zone, no 55/45 lag; 1.5 px of movement is enough,
// which also stops pixel jitter from twitching it). Item 7 (Jeremy): the start point stays fixed where the finger first touched, so dragging back toward it slows the shark; STEER.FULL (fraction of screen width for full speed) is the one knob.
C.addEventListener("pointerdown",e=>{if(state!=="play")return;e.preventDefault();initAudio();touch.on=true;touch.x=touch.x0=e.clientX;touch.y=touch.y0=e.clientY;touch.ax=0;touch.ay=0;touch.dir=shark.ang;touch.drive=0;touch.lastMove=performance.now();try{C.setPointerCapture(e.pointerId)}catch(_){}});
C.addEventListener("pointermove",e=>{if(!touch.on)return;const mx=e.clientX-touch.x,my=e.clientY-touch.y,md=Math.hypot(mx,my);touch.x=e.clientX;touch.y=e.clientY;if(md<=0)return;
 touch.ax+=mx;touch.ay+=my;const am=Math.hypot(touch.ax,touch.ay);
 if(am>=STEER.DIR_PX){const ux=touch.ax/am,uy0=touch.ay/am,uy=Math.abs(uy0)<STEER.VDEAD?0:uy0*STEER.VK;touch.dir=Math.atan2(uy,ux);touch.ax=touch.ay=0;
  }// v10 item 7: the start point stays FIXED (no leash); dragging back toward it lowers the drive below
 touch.drive=Math.min(1,Math.hypot(e.clientX-touch.x0,e.clientY-touch.y0)/(W*STEER.FULL));touch.lastMove=performance.now()});
const up=()=>{touch.on=false};C.addEventListener("pointerup",up);C.addEventListener("pointercancel",up);
document.addEventListener("touchmove",e=>e.preventDefault(),{passive:false});document.addEventListener("gesturestart",e=>e.preventDefault());document.addEventListener("contextmenu",e=>e.preventDefault());// no long-press menu
document.addEventListener("pointerdown",()=>{if(AC&&AC.state==="suspended")AC.resume().catch(()=>{})},true);
/* b46 boost button (bottom-left, play only). Its own pointer events never reach the canvas, so it never steers; another finger can keep steering. */
let boostP=-1;function boostUi(){const b=$("boost");if(!b)return;const p=boost.t>0?1:boost.cd>0?1-boost.cd/(BOOST.DUR+BOOST.CD):1,q=Math.round(p*50)/50;if(q!==boostP){boostP=q;b.style.setProperty("--p",q*100+"%")}b.classList.toggle("on",boost.t>0);b.classList.toggle("cd",boost.t<=0&&boost.cd>0)}
function doBoost(){if(state!=="play"||boost.t>0||boost.cd>0||shark.stun>0||shark.air)return false;boost.t=BOOST.DUR;boost.cd=BOOST.DUR+BOOST.CD;boost.n++;SFX.bubbles();boostUi();return true}
{const b=$("boost");for(const ev of["pointerdown","pointermove","pointerup","touchstart","touchmove","touchend"])b.addEventListener(ev,e=>{e.stopPropagation();if(ev==="pointerdown"){e.preventDefault();doBoost()}},{passive:false});b.addEventListener("click",e=>{e.stopPropagation();e.preventDefault()})}
document.addEventListener("keydown",e=>{if(state==="play"&&!e.repeat&&(e.key==="Shift"||e.key==="b"||e.key==="B"))doBoost()});
function buildPick(){const box=$("pickList");box.innerHTML="";for(const k of Object.keys(TYPES)){const t=TYPES[k],b=document.createElement("button");b.className="pick"+(k===sType?" sel":"");b.dataset.type=k;
  const cv=render3DShark(110*2,false,t);cv.style.width="110px";cv.className="pv";b.appendChild(cv);
  const info=document.createElement("div");info.className="pinfo";info.innerHTML=`<b>${t.name}</b><span class="pdesc">${t.desc}</span>`+Object.entries(t.bars).map(([n,v])=>`<span class="bar" data-stat="${n}" data-v="${v}"><i>${n}</i><em style="width:${v*20}%"></em></span>`).join("");b.appendChild(info);
  b.onclick=()=>{sType=k;LS.setItem(TYPE_KEY,k);buildSprites();startGame()};box.appendChild(b)}}
/* b45 ghost-click guard: on a phone the Tap-to-start finger-up "click" landed on Start (title UI appears under the finger on pointerdown) and skipped the intro.
   Title-screen clicks count only if their own press started on the title screen after the tap, and never within 600 ms of the tap. Keyboard clicks (detail 0) still work. */
let tapAt=-1e9,titleDown=false;
$("titleUi").addEventListener("pointerdown",()=>{titleDown=true},true);/* b54 (QA #3): any NEW pointerdown after the start tap is a real tap, even 0.1 s later (b52/b53 dropped every click for 600 ms, so Sound on ignored a quick tap) */
$("titleUi").addEventListener("click",e=>{const ghost=!titleDown&&(performance.now()-tapAt<600||e.detail!==0);/* only the click left over from the start tap itself (no pointerdown of its own) is a ghost */if(ghost){e.stopPropagation();e.preventDefault()}},true);
/* b46 (Jeremy: "Shark attack still had no music"): Chrome on Android does not count a finger-DOWN as permission to play sound, so the intro music
   started on pointerdown was blocked and never retried. Every finger-UP / click / key press now wakes the AudioContext and, on the title or pick screen,
   (re)starts the intro music if it was blocked. It never restarts music that is already playing or has finished, and respects the Sound/Songs switches. */
function wakeAudio(){initAudio();if(AC&&AC.state==="suspended")AC.resume().catch(()=>{});
 const a=music.title;if(!a||music.cur!==a||!musOn()||(state!=="title"&&state!=="pick")||!a.paused||a.ended||document.hidden)return;
 a.volume=MUSIC_VOL.title;a.play().catch(()=>{})}
for(const ev of["pointerup","touchend","click","keydown"])document.addEventListener(ev,wakeAudio,true);
function sndHint(){const h=$("sndOff");if(h)h.classList.toggle("hide",musOn())}
/* b48 fix (QA): the first tap used to start the sound on finger DOWN, which Chrome on Android does not count as permission. Now a press on "Tap to start" only arms it;
   the intro, music and sound engine start when the finger comes UP (pointerup) - a cancelled or never-lifted press starts nothing. */
let tapArmed=false;
function tapGo(){if(!tapArmed)return;tapArmed=false;tapAt=performance.now();titleDown=false;initAudio();if(music.title){try{music.title.currentTime=0}catch(e){}}startTitle();playMusic("title")}
$("tap").addEventListener("pointerdown",e=>{e.preventDefault();tapArmed=true});
document.addEventListener("pointerup",()=>{if(state==="tap")tapGo()},true);
document.addEventListener("pointercancel",()=>{tapArmed=false},true);/* b44: intro music always starts from the beginning at launch */
// b44 (Jeremy: "intro every time"): a page restored from the back-forward cache (reopened app) counts as a launch. Outside a game, go back to "Tap to start" so the intro + its music play again.
window.addEventListener("pageshow",e=>{if(!e.persisted||state==="play"||state==="dead")return;++fadeId;if(music.title){music.title.pause();try{music.title.currentTime=0}catch(_){}}music.cur=null;state="tap";show("tap")});
$("start").onclick=()=>{initAudio();state="pick";buildPick();show("pickUi")};
for(const k of MODES)$("mode_"+k).onclick=()=>setMode(k);setMode(mode);
$("pickBack").onclick=()=>{state="title";show("titleUi")};
$("again").onclick=()=>startGame();
$("home").onclick=()=>{buildSprites();startTitle();playMusic("title")};
$("snd").onclick=()=>{if(!soundOn&&!songsOn&&!fxOn){songsOn=fxOn=true;LS.setItem(SONGS_KEY,"1");LS.setItem(SFX_KEY,"1")}setSound(!soundOn)};/* master switch: turning sound on with both sub-switches off turns both back on */
function setSongs(v){songsOn=v;LS.setItem(SONGS_KEY,v?"1":"0");if(v&&!soundOn){soundOn=true;LS.setItem(SND_KEY,"1")}setSound(soundOn)}
function setFx(v){fxOn=v;LS.setItem(SFX_KEY,v?"1":"0");if(v&&!soundOn){soundOn=true;LS.setItem(SND_KEY,"1")}setSound(soundOn)}
$("songs").onclick=()=>setSongs(!musOn());$("fx").onclick=()=>setFx(!(soundOn&&fxOn));
function setCalm(v){calm=v;LS.setItem(CALM_KEY,v?"1":"0");$("calm").textContent=v?"🌙 Calm (no shake)":"🌊 Shake on"}setCalm(calm);$("calm").onclick=()=>setCalm(!calm);
$("cred").onclick=()=>{state="credits";show("credUi")};
$("credBack").onclick=()=>{state="title";show("titleUi")};
/* b50: a real tap on any title button releases the held shark pose (ghost clicks are already stopped by the b45 guard above). */
$("titleUi").addEventListener("click",e=>{if(!e.defaultPrevented&&e.target.closest&&e.target.closest("button"))releasePose()},true);
window.addEventListener("resize",()=>resize());
setSound(soundOn);resize();show("tap");startLoop();
// build id + "Updated!" note (shown once, 2 s, on the first launch of a new build). Update checks are done by the service worker.
const BUILD=(document.querySelector('meta[name="build"]')||{}).content||"",BUILD_KEY="sharkAttack_build";
{const prev=LS.getItem(BUILD_KEY);if(BUILD&&prev&&prev!==BUILD){$("upd").classList.remove("hide");setTimeout(()=>$("upd").classList.add("hide"),2000)}if(BUILD)LS.setItem(BUILD_KEY,BUILD)}
if("serviceWorker" in navigator&&location.protocol!=="file:"){navigator.serviceWorker.register("sw.js").then(()=>navigator.serviceWorker.ready).then(r=>{if(r.active){r.active.postMessage("status");if(navigator.onLine)r.active.postMessage("check")}}).catch(()=>{})}
// v10 b42 UPDATE BUTTON (like Starstruck): title screen only. Normal: "Check for update". When a new build is fully downloaded and waiting: "Update ready - tap to update".
// Tapping it asks the service worker to switch, then reloads. Never shown or used mid-play (the button lives in the title screen). Saves (localStorage) are untouched.
const UPD={pending:null,busy:false};
function updBtn(txt){const b=$("updb");if(!b)return;b.classList.remove("hide");if(UPD.pending){b.textContent="⬆️ Update ready - tap to update";b.classList.add("ready")}else{b.textContent=txt||"🔄 Check for update";b.classList.remove("ready")}}
if("serviceWorker" in navigator&&location.protocol!=="file:"){navigator.serviceWorker.addEventListener("message",e=>{const d=e.data||{};
  if(d.type==="pending"||(d.type==="status"&&d.pending)){UPD.pending=d.pending||d.build;updBtn()}else if(d.type==="status"&&UPD.busy){UPD.busy=false;updBtn(navigator.onLine?"✅ Up to date":"📴 Offline - try later");setTimeout(()=>{if(!UPD.pending)updBtn()},2500)}
  else if(d.type==="applied"){location.reload()}});
 updBtn();$("updb").addEventListener("click",e=>{e.stopPropagation();if(state==="play")return;const c=navigator.serviceWorker.controller;if(!c){updBtn("📴 Not installed yet");return}
  if(UPD.pending){$("updb").textContent="Updating…";c.postMessage("apply");setTimeout(()=>location.reload(),3000)}else if(!UPD.busy){UPD.busy=true;$("updb").textContent="Checking…";c.postMessage("check")}})}
// b45 corner button: "Update ready - tap to reload" once a newer build is fully downloaded (pending). Not on the first install (no pending then),
// hidden during a run, never reloads by itself. The tap switches to the new build now; phones that never tap still switch on the next open.
if($("updr")){setInterval(()=>{$("updr").classList.toggle("hide",!(UPD.pending&&state!=="play"&&state!=="dead"))},500);
 $("updr").addEventListener("click",e=>{e.stopPropagation();if(state==="play")return;const c=navigator.serviceWorker&&navigator.serviceWorker.controller;$("updr").textContent="Updating…";UPD.reloads=(UPD.reloads||0)+1;if(c)c.postMessage("apply");setTimeout(()=>location.reload(),1500)})}
// b45: like Starstruck, look again whenever the app comes back to the front or gets focus, and every 5 minutes; also re-ask "status" a few times
// after launch so a download that finishes during page load is not missed (its "pending" message can race the new page).
if("serviceWorker" in navigator&&location.protocol!=="file:"){const ask=m=>{const c=navigator.serviceWorker.controller;if(c)c.postMessage(m)};
 [3000,8000,15000,30000].forEach(ms=>setTimeout(()=>ask("status"),ms));setInterval(()=>{if(navigator.onLine)ask("check")},5*60*1000);
 document.addEventListener("visibilitychange",()=>{if(!document.hidden&&navigator.onLine)ask("check")});addEventListener("focus",()=>{if(navigator.onLine)ask("check")})}
window.__saUpd=UPD;

// ---------- test hooks ----------
window.__sa={get state(){return state},get busy(){return busy},boost,BOOST,doBoost,shark,fish,surf,touch,perf,sfxCount,TYPES,TIERS,LAUNCH,BEAT,STEER,FAST_SFX,SURFERS,MAX_LEVEL,ROUND_SECONDS,
 get score(){return score},get timeLeft(){return timeLeft},set timeLeft(v){timeLeft=v},get best(){return best},get endReason(){return endReason},get soundOn(){return soundOn},get songsOn(){return songsOn},get fxOn(){return fxOn},get musOn(){return musOn()},get titleMusicPlaying(){return !!(music.title&&!music.title.paused)},get chip(){return !!chip.buf},get chipPlaying(){return !!chip.src},get chipFailed(){return chip.failed},get acState(){return AC?AC.state:"none"},get looping(){return !!raf},MUSIC_VOL,get placeholder(){return !!placeholder},
 get type(){return sType},get camY(){return camY},get WORLD_H(){return WORLD_H},get sizeK(){return sizeK},DIVE,diveK,WORLD,ZONES,GROW,CREATURES,DODGE,depthOf,fleeK,ptsOf,growOf,bite,spawnFish,setCreature,get titleT(){return T.t},get titleShark(){return T.sr},get titleLog(){return T.log},get titleTorn(){return false},get titleArt(){return T.art},get titleArtOK(){return false},get titleBite(){return null},titleInk:()=>title?titleInk():0,get titleFrags(){return T.frags?T.frags.length:0},TITLE:{ENTER:TITLE_ENTER,ACROSS:TITLE_ACROSS,TURN:TITLE_TURN,SNAP:TITLE_SNAP,CALM_IN:TITLE_CALM_IN,GLIDE:TITLE_GLIDE,SWIM:TITLE_SWIM,FADE:TITLE_ART_FADE},get titlePose(){return {pose:T.pose,rel:T.rel,relT:T.relT,sr:T.sr}},get titleRect(){return titleRect()},get titleLayout(){return titleLayout()},get rotPaused(){return fsRot},BUILD,set god(v){godMode=!!v},get SURF(){return SURF},get BED(){return BED},trait,maxSpeed:()=>sharkMax(shark.lvl),power,canLaunch,rel,feed,need,beatNow,beatLen,setRound(s){window.__saRound=s},
 clearFood(){for(const f of fish){f.off=true;f.x=-1e6;f.vx=0;f.vy=0}for(const s of surf)s.zip=999},
 placeFishAtMouth(ti,kind){const f=fish[0];kind=kind||(shark.lvl===0?"plankton":"fish");setCreature(f,kind==="plankton"?bite()*.4:TIERS[ti||0].s,kind);f.band=[SURF+6,Infinity];f.vy=0;const [mx,my]=mouth();f.x=mx;f.y=my;f.vx=0;return fish.indexOf(f)},
 placeFishAt(ti,x,y,vx){const f=fish.find(q=>!q.used)||fish[0];setCreature(f,TIERS[ti].s,"fish");f.band=[SURF+6,Infinity];f.x=x;f.y=y;f.vx=vx||0;f.vy=0;return fish.indexOf(f)},
 placeSurfer(i,x,k){const s=surf[i];s.zip=0;s.x=x;s.vx=0;if(k!=null){s.k=k;s.ate=0}},get surfersCaught(){return surfersCaught},surfEaten,SURFACE,ZONE,LIGHT,SAIL_SHRINK,SAIL_SPAN,SURFER_SPAN,sailDepthK,diveD,pastSurf,pastCargo,canEatSurf,pickSurfK,get depthMark(){return depthMark},set depthMark(v){depthMark=Math.max(0,+v||0)},get lightProbe(){return lightProbe},set lightProbe(v){lightProbe=!!v},VANISH,CHASE,chaseCapped,chaseCap,MOUTH,mouthPt,mouthHit,LATE,lateK,surfDrawK,fpx,TURN3D,pops,addPop,popHit,goneAt,lookMin,eatSurf,spawnSurf,get sprites(){return {sprB,sprF}},
 render3DShark,sim(sec,bot,step){step=step||1/60;const n=Math.round(sec/step);let i=0;for(;i<n&&state==="play";i++){if(bot)bot(step);updPlay(step)}return i*step},startAs(t,m){sType=t;if(m)setMode(m);startGame()},setMode,get mode(){return mode},get elapsed(){return elapsed},MODE:{MODES},surferCaught,
 setLevel(l){shark.lvl=Math.min(l,MAX_LEVEL);shark.meter=0;buildShark();shark.Lt=shark.L;setWorldK(wK(l))},drawK,wK,DRAW,DEEP,EAT,get worldK(){return worldK},trueGrow,get dead(){return dead},get camX(){return camX},set camX(v){camX=v},set camY(v){camY=v},get tiles(){return tiles},get tileC(){return tileC},updTiles,spawnStats,LAYERS,SPAWN,ALLOWED,ANGLER_D,allowedD,layerOf,depthRaw,DEPTH_LIMIT,CAP_COL,get bandOf(){return bandOf},inWindow,respawnAll(){updTiles(true,true);for(const f of fish)spawnFish(f,false)},drawWater,get FX(){return FX},set FX(v){FX=v},get DPR(){return DPR},get RSK(){return RSK},adapt,ADAPT,ADAPT_ON,DPR_CAP,RS0,SPECIES,PLANK_SP,get specSpr(){return specSpr},spSprite,drawSpecies,render3DShark,TYPES,sharkMax,get pops(){return pops},get depthHintT(){return depthHintT},BODY,onBody,mouth,LOOK,RINGS,lk};

// Install button + landscape lock (like Dino Colossus). Hidden when already installed; no per-frame cost.
(function(){try{screen.orientation&&screen.orientation.lock&&screen.orientation.lock("landscape").catch(()=>{})}catch(e){}
 const b=document.getElementById("instb"),t=document.getElementById("insth");if(!b)return;let dp=null;
 const inst=()=>matchMedia("(display-mode: standalone)").matches||matchMedia("(display-mode: fullscreen)").matches||navigator.standalone===true;
 const hide=()=>{b.classList.add("hide");t.classList.add("hide")};if(inst())hide();
 addEventListener("beforeinstallprompt",e=>{e.preventDefault();dp=e});addEventListener("appinstalled",hide);
 b.onclick=async e=>{e.stopPropagation();if(dp){dp.prompt();const r=await dp.userChoice;dp=null;if(r.outcome==="accepted")hide()}else{const ios=/iphone|ipad|ipod/i.test(navigator.userAgent);t.textContent=ios?"On iPhone: tap Share, then Add to Home Screen.":"Tap ⋮ in Chrome, then Add to Home screen / Install app.";t.classList.remove("hide")}}})();
