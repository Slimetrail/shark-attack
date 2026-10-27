// Shark Attack v1 — side-view 2D ocean. Original art & code. 2D canvas, light on CPU.
"use strict";
// ======================= EASY-TO-CHANGE SETTINGS =======================
// ROUND_SECONDS: round length. 60 s is the DEFAULT and is NOT YET CONFIRMED by Jeremy. Test override: ?round=N
const ROUND_SECONDS=(()=>{const m=/[?&]round=(\d+(\.\d+)?)/.exec(location.search);return m?+m[1]:60})();
const N_SURF=3,MAX_LEVEL=10,MAX_PARTS=30,BEST_KEY="sharkAttack_best",SND_KEY="sharkAttack_sound",CALM_KEY="sharkAttack_calm",TYPE_KEY="sharkAttack_type",HINT_KEY="sharkAttack_hinted";
// Fish tiers: small / medium / big / giant. Fish bigger than the shark are dangerous (red + "!").
const TIERS=[{s:16,pts:1,grow:1,col:"#ffd23f",n:8},{s:28,pts:2,grow:2,col:"#7be04a",n:3},{s:44,pts:3,grow:3,col:"#b06cff",n:1},{s:62,pts:5,grow:4,col:"#ff7a1e",n:1}];
const N_FISH=TIERS.reduce((a,t)=>a+t.n,0);
// Steering: the finger's SLIDE direction = swim direction. Each px slid adds "drive" (speed); drive fades when the finger rests.
const STEER={MIN:.2,DRIVE_PX:.55,DRIVE_DECAY:.5,TURN:6,ACC:1.8,DEC:1.2};// DRIVE_PX: screen widths of sliding for full drive
// Launch: heading up through the surface. power = LAUNCH.K * (speed/max) * (run-up distance at speed / screen height), capped at 1.
const LAUNCH={K:2.2,MIN_POWER:.22,MIN_SPEED:.45,UP:-.35,H_MAX:.32,G:1.6,COOL:.3};// H_MAX: max height as fraction of screen height, G: gravity in screen-heights/s^2
const SURFERS=[{kind:"kneel",pts:3,hy:16},{kind:"stand",pts:5,hy:46}];// hy: how high above the water the surfer's catch point is
const BEAT={PLACEHOLDER_BPM:100,CHIPTUNE_BPM:80/*eighth-note pulse of the v2 render (music team: TEMPO_EIGHTH_BPM=80)*/,ASSIST_MS:80,PERFECT_MS:45,PERFECT_BONUS:1,on:true};
const SAFE_SPAWN_S=1.5;
// DIVERS + AMBUSH. The 3-hit lose rule and the ambush odds/timing are OUR choice, to confirm with Jeremy.
const DIVER_TRIGGER_SURFERS=3,DIVER_SPEED_FRACTION=.5,DIVER_DETECT_RANGE=.28,DIVER_GIVEUP_MS=3000,DIVER_GRACE_MS=2000,DIVER_COOLDOWN_MS=4000,DIVER_SAFE_AFTER_STUN_MS=1500,DIVER_CATCHES_TO_LOSE=3,DIVER_MAX=3,DIVER_SIZE=46,DIVER_NET_REACH=.25,DIVER_GROWTH_LOSS=2;
const STUN_MS=1000,AMBUSH_STUN_MS=2000;// a hit that brings an ambush stuns longer so the threat is real (it arrives at AMBUSH_ARRIVE_MS)
const AMBUSH_ON_HIT=[false,false,null,true],AMBUSH_CHANCE=.5;// index = net hit number; null = roll AMBUSH_CHANCE. Hit 3 also ends the round ("Caught!") so it never actually ambushes
const AMBUSH_ARRIVE_MS=1350,AMBUSH_COOLDOWN_MS=6000,STRUGGLE_SHORTEN_MS=250,STRUGGLE_PX=.2,AMBUSHER_SIZE=1.6,AMBUSHER_LEAVE_MS=3000;// STRUGGLE_PX: screen widths of drag/wiggle per shorten step
const AMB_T={body:"#3a4552",hi:"#5f6d7b",belly:"#c4ccd2",ext:"#141b22",stripe:null,hammer:false};// dark bull-style, unlike the 3 pick types
const DIVER_TIP_KEY="sharkAttack_diverTip";
// Shark types — they differ in size and play (decided with Jeremy: numbers are OUR choice, tune them here).
// size: start-size multiplier (fish danger is always judged against the shark's CURRENT size), speed: top speed, acc: acceleration,
// turn: turning rate, catchR: air catch radius for surfers, leap: launch height, grow: growth-meter fill rate. bars: pick-screen stat bars 1..5.
const TYPES_MECHANICAL=!/[?&]flat/.test(location.search);// true = types play differently (decided). ?flat (tests) makes all three identical, looks only
const TYPES={
 white:{name:"Great White",desc:"Biggest and fastest, but turns wide and speeds up slowly.",body:"#6f8ea8",hi:"#a9c6dc",belly:"#f4f8fb",ext:"#2d4558",stripe:null,hammer:false,
  size:1.2,speed:1.12,acc:.8,turn:.8,catchR:1.0,leap:1.0,grow:1.0,bars:{Size:5,Speed:5,Jump:3}},
 hammer:{name:"Hammerhead",desc:"Turns the tightest and grabs surfers best. Jumps a bit lower.",body:"#7f9488",hi:"#b8cbbf",belly:"#eef3ee",ext:"#34463c",stripe:null,hammer:true,
  size:1.0,speed:1.0,acc:1.0,turn:1.3,catchR:1.35,leap:.9,grow:1.0,bars:{Size:3,Speed:3,Jump:2}},
 tiger:{name:"Tiger Shark",desc:"Smallest, but quick off the mark, jumps highest and grows fast.",body:"#8a8a70",hi:"#c9c29a",belly:"#f7f1de",ext:"#45412c",stripe:"#e0841a",hammer:false,
  size:.9,speed:1.0,acc:1.3,turn:1.05,catchR:1.0,leap:1.2,grow:1.5,bars:{Size:2,Speed:3,Jump:5}}};
// =======================================================================
const SHOW_FPS=/[?&]fps/.test(location.search);
const C=document.getElementById("c"),X=C.getContext("2d",{alpha:false});
const $=id=>document.getElementById(id);
let W=0,H=0,DPR=1,state="tap",roundLen=ROUND_SECONDS,SURF=150,BED=800;
let sType=TYPES[localStorage.getItem(TYPE_KEY)]?localStorage.getItem(TYPE_KEY):"white";
const trait=k=>TYPES_MECHANICAL?TYPES[sType][k]:1;
const P={ink:"#082a3d",foam:"rgba(220,248,255,.45)",red:"#e2463c",yel:"#ffcc33"};
function mk(w,h){const c=document.createElement("canvas");c.width=Math.max(1,Math.ceil(w));c.height=Math.max(1,Math.ceil(h));return c}

// ---------- art ----------
function drawFish(g,s,col,tier,danger){g.lineJoin="round";
 if(danger){g.save();g.lineWidth=9;g.strokeStyle="#ff2a2a";g.beginPath();g.ellipse(-s*.1,0,s*.78,s*.4,0,0,7);g.stroke();g.restore()}
 g.lineWidth=tier>1?3.5:2.5;g.strokeStyle=P.ink;g.fillStyle=danger?"#ff5a4e":col;
 g.beginPath();g.moveTo(-s*.45,0);g.lineTo(-s*.85,-s*.35);g.lineTo(-s*.8,s*.35);g.closePath();g.fill();g.stroke();
 g.beginPath();g.ellipse(0,0,s*.55,s*.32,0,0,7);g.fill();g.stroke();
 if(tier>=1){g.beginPath();g.moveTo(-s*.1,-s*.3);g.lineTo(s*.05,-s*.5);g.lineTo(s*.15,-s*.28);g.fill();g.stroke()}
 if(tier>=2){g.strokeStyle="rgba(8,42,61,.5)";for(let i=0;i<tier;i++){g.beginPath();g.moveTo(-s*.15+i*s*.12,-s*.25);g.lineTo(-s*.15+i*s*.12,s*.25);g.stroke()}g.strokeStyle=P.ink}
 if(tier>=3){g.fillStyle="#fff";for(let i=0;i<3;i++){g.beginPath();g.moveTo(s*.4,-s*.08+i*s*.05);g.lineTo(s*.47,-s*.05+i*s*.05);g.lineTo(s*.4,-s*.02+i*s*.05);g.fill()}}
 g.fillStyle="#fff";g.beginPath();g.arc(s*.28,-s*.06,s*.1,0,7);g.fill();g.stroke();g.fillStyle=P.ink;g.beginPath();g.arc(s*.31,-s*.06,s*.05,0,7);g.fill();
 if(danger){g.lineWidth=3;g.beginPath();g.moveTo(s*.18,-s*.2);g.lineTo(s*.38,-s*.13);g.stroke()}}
function drawDiver(g,s){g.lineJoin="round";g.lineCap="round";g.lineWidth=2.5;g.strokeStyle=P.ink;// side view facing right, cartoon
 g.fillStyle="#ffcc33";g.beginPath();g.moveTo(-s*.75,-s*.05);g.lineTo(-s*1.0,-s*.22);g.lineTo(-s*1.02,s*.12);g.closePath();g.fill();g.stroke();// fins
 g.fillStyle="#9aa7b3";g.beginPath();g.roundRect(-s*.45,-s*.36,s*.55,s*.16,s*.08);g.fill();g.stroke();// tank
 g.fillStyle="#ff7a1e";g.beginPath();g.ellipse(-s*.25,0,s*.52,s*.2,0,0,7);g.fill();g.stroke();// suit
 g.fillStyle="#ffe0bd";g.beginPath();g.arc(s*.32,-s*.04,s*.17,0,7);g.fill();g.stroke();// head
 g.fillStyle="#7fe0ff";g.beginPath();g.roundRect(s*.34,-s*.14,s*.16,s*.13,s*.04);g.fill();g.stroke();// mask
 g.strokeStyle="#6b4a2a";g.lineWidth=3;g.beginPath();g.moveTo(s*.1,s*.06);g.lineTo(s*.8,-s*.1);g.stroke();// pole
 g.strokeStyle=P.ink;g.lineWidth=2;g.fillStyle="rgba(255,255,255,.25)";g.beginPath();g.ellipse(s*.98,-s*.14,s*.2,s*.24,0,0,7);g.fill();g.stroke();
 g.lineWidth=1;g.beginPath();for(let i=-2;i<=2;i++){g.moveTo(s*.8,-s*.14+i*s*.08);g.lineTo(s*1.16,-s*.14+i*s*.08);g.moveTo(s*.98+i*s*.07,-s*.36);g.lineTo(s*.98+i*s*.07,s*.08)}g.stroke()}
function drawSurfer(g,s,stand){// side view on a board, board centred at 0,0 (on the water line)
 g.lineJoin="round";g.lineCap="round";g.strokeStyle=P.ink;g.lineWidth=3;g.fillStyle=stand?"#3bb3ff":"#ff5d8f";
 g.beginPath();g.ellipse(0,0,s*.7,s*.09,0,0,7);g.fill();g.stroke();g.fillStyle="#fff";g.fillRect(-s*.5,-s*.025,s,s*.05);
 const skin="#f2b27a";
 if(stand){g.lineWidth=6;g.strokeStyle="#1d5fa8";g.beginPath();g.moveTo(-s*.12,-s*.06);g.lineTo(-s*.05,-s*.35);g.lineTo(s*.12,-s*.06);g.stroke();
  g.fillStyle="#ffd23f";g.strokeStyle=P.ink;g.lineWidth=3;g.beginPath();g.roundRect(-s*.14,-s*.66,s*.24,s*.34,6);g.fill();g.stroke();
  g.strokeStyle=skin;g.lineWidth=6;g.beginPath();g.moveTo(-s*.1,-s*.6);g.lineTo(-s*.38,-s*.5);g.moveTo(s*.08,-s*.6);g.lineTo(s*.36,-s*.72);g.stroke();
  g.fillStyle=skin;g.strokeStyle=P.ink;g.lineWidth=3;g.beginPath();g.arc(-s*.02,-s*.8,s*.13,0,7);g.fill();g.stroke();g.fillStyle="#6b3d1f";g.beginPath();g.arc(-s*.02,-s*.84,s*.13,Math.PI,0);g.fill()}
 else{g.fillStyle="#ff9f1c";g.strokeStyle=P.ink;g.lineWidth=3;g.beginPath();g.roundRect(-s*.16,-s*.36,s*.26,s*.28,6);g.fill();g.stroke();
  g.strokeStyle=skin;g.lineWidth=6;g.beginPath();g.moveTo(s*.06,-s*.28);g.lineTo(s*.3,-s*.08);g.stroke();
  g.fillStyle=skin;g.strokeStyle=P.ink;g.lineWidth=3;g.beginPath();g.arc(s*.0,-s*.48,s*.12,0,7);g.fill();g.stroke();g.fillStyle="#ffd23f";g.beginPath();g.arc(-s*.02,-s*.52,s*.12,Math.PI,0);g.fill()}
 g.fillStyle=P.ink;g.beginPath();g.arc(stand?s*.05:s*.06,stand?-s*.8:-s*.48,2.2,0,7);g.fill()}
function sideSharkPath(g,L,open,T){const h=L*.22;g.beginPath();g.moveTo(L*.5,-h*.05);
 if(T&&T.hammer){g.lineTo(L*.5,-h*.55);g.lineTo(L*.4,-h*.62);g.bezierCurveTo(L*.32,-h*.95,L*.1,-h*1.0,-L*.15,-h*.75)}
 else g.bezierCurveTo(L*.42,-h*.85,L*.1,-h*1.0,-L*.15,-h*.75);
 g.lineTo(-L*.02,-h*.75);g.lineTo(-L*.12,-h*1.9);g.lineTo(-L*.26,-h*.62);
 g.bezierCurveTo(-L*.36,-h*.45,-L*.42,-h*.2,-L*.46,-h*.1);g.lineTo(-L*.6,-h*1.1);g.quadraticCurveTo(-L*.56,0,-L*.62,h*.9);g.lineTo(-L*.46,h*.1);
 g.bezierCurveTo(-L*.3,h*.6,-L*.05,h*.85,L*.12,h*.7);g.lineTo(L*.05,h*1.35);g.lineTo(L*.22,h*.62);
 g.bezierCurveTo(L*.32,h*.55,L*.4,h*.4,L*.44,h*(open?.55:.25));if(open){g.lineTo(L*.3,h*.18);g.lineTo(L*.52,h*.05)}g.closePath()}
// fake-3D (extruded + beveled) cartoon shark, pre-rendered once per size/type. Origin offset: shark centre is at canvas centre + (L*.05, 0)
function render3DShark(L,open,T,shadow){T=T||TYPES.white;const h=L*.22,pad=L*.12,c=mk(L*1.3+pad*2,h*3.6+pad*2),g=c.getContext("2d");g.translate(c.width/2+L*.05,c.height*.5);g.lineJoin="round";
 if(shadow){g.save();g.translate(L*.03,h*1.25);g.scale(1,.35);g.fillStyle="rgba(0,20,40,.28)";sideSharkPath(g,L,open,T);g.fill();g.restore()}
 for(let i=8;i>0;i--){g.save();g.translate(i*L*.004,i*L*.004);g.fillStyle=i>1?T.ext:P.ink;sideSharkPath(g,L,open,T);g.fill();g.restore()}
 sideSharkPath(g,L,open,T);g.lineWidth=Math.max(2.5,L*.022);g.strokeStyle=P.ink;g.stroke();
 const gr=g.createLinearGradient(0,-h*1.9,0,h*1.3);gr.addColorStop(0,T.hi);gr.addColorStop(.45,T.body);gr.addColorStop(.62,T.belly);gr.addColorStop(1,"#fff");g.fillStyle=gr;g.fill();
 g.save();sideSharkPath(g,L,open,T);g.clip();
 if(T.stripe){g.strokeStyle=T.stripe;g.lineWidth=L*.035;g.lineCap="round";for(let i=0;i<6;i++){const x=-L*.36+i*L*.12;g.beginPath();g.moveTo(x,-h*1.2);g.quadraticCurveTo(x+L*.03,-h*.5,x-L*.01,-h*.05);g.stroke()}}
 g.lineWidth=L*.05;g.strokeStyle="rgba(10,30,50,.35)";g.translate(-L*.012,-L*.012);sideSharkPath(g,L,open,T);g.stroke();
 g.strokeStyle="rgba(255,255,255,.55)";g.translate(L*.024,L*.024);sideSharkPath(g,L,open,T);g.stroke();g.restore();
 g.fillStyle="rgba(255,255,255,.45)";g.beginPath();g.ellipse(L*.12,-h*.55,L*.2,h*.12,-.12,0,7);g.fill();
 g.strokeStyle=P.ink;g.lineWidth=Math.max(1.5,L*.01);for(let i=0;i<3;i++){g.beginPath();g.moveTo(L*(.2-i*.035),-h*.2);g.quadraticCurveTo(L*(.18-i*.035),h*.05,L*(.2-i*.035),h*.3);g.stroke()}
 const ex=T.hammer?L*.46:L*.34,ey=T.hammer?-h*.45:-h*.35;g.fillStyle="#fff";g.beginPath();g.arc(ex,ey,L*.04,0,7);g.fill();g.lineWidth=Math.max(1.5,L*.012);g.stroke();g.fillStyle=P.ink;g.beginPath();g.arc(ex+L*.01,ey+L*.005,L*.02,0,7);g.fill();
 g.fillStyle="#fff";g.lineWidth=Math.max(1,L*.006);const ty=open?h*.18:h*.2;for(let i=0;i<5;i++){const x=L*(.31+i*.04);g.beginPath();g.moveTo(x,ty);g.lineTo(x+L*.018,ty+h*.16);g.lineTo(x+L*.036,ty);g.closePath();g.fill();g.stroke()}
 c.L=L;return c}
function render3DTitle(w){const fs=Math.floor(w*.17),c=mk(w,fs*2.7),g=c.getContext("2d");g.textAlign="center";g.textBaseline="middle";g.font=`900 ${fs}px system-ui,"Arial Black",sans-serif`;g.lineJoin="round";
 const lines=[["SHARK",fs*.85],["ATTACK",fs*1.95]];
 for(const [t,y] of lines){g.fillStyle="rgba(0,20,40,.3)";g.fillText(t,w/2+fs*.12,y+fs*.16);
  for(let i=8;i>0;i--){g.fillStyle=i>1?"#a3271f":P.ink;g.fillText(t,w/2+i*fs*.012,y+i*fs*.012)}
  g.lineWidth=fs*.09;g.strokeStyle=P.ink;g.strokeText(t,w/2,y);
  const gr=g.createLinearGradient(0,y-fs*.5,0,y+fs*.5);gr.addColorStop(0,"#fff27a");gr.addColorStop(.5,"#ffcc33");gr.addColorStop(.51,"#ff9f1c");gr.addColorStop(1,"#f06a12");g.fillStyle=gr;g.fillText(t,w/2,y);
  g.save();g.globalCompositeOperation="source-atop";g.fillStyle="rgba(255,255,255,.35)";g.fillRect(0,y-fs*.45,w,fs*.18);g.restore()}
 return c}
function biteTitle(c,cx,cy,r){// cartoon bite: scalloped chunk removed + dark rim
 const g=c.getContext("2d");g.save();g.globalCompositeOperation="destination-out";g.beginPath();
 for(let i=0;i<6;i++){const a=-Math.PI/2+(i-2.5)*.42;g.moveTo(cx+Math.cos(a)*r,cy+Math.sin(a)*r);g.arc(cx+Math.cos(a)*r,cy+Math.sin(a)*r,r*.42,0,7)}
 g.arc(cx,cy+r*.15,r*.95,0,7);g.fill();g.restore();
 g.save();g.globalCompositeOperation="source-atop";g.strokeStyle=P.ink;g.lineWidth=r*.18;g.beginPath();
 for(let i=0;i<6;i++){const a=-Math.PI/2+(i-2.5)*.42;g.moveTo(cx+Math.cos(a)*r+r*.42,cy+Math.sin(a)*r);g.arc(cx+Math.cos(a)*r,cy+Math.sin(a)*r,r*.42,0,7)}g.arc(cx,cy+r*.15,r*.95,0,7);g.stroke();g.restore()}


// ---------- world ----------
const shark={stun:0,safe:0,x:0,y:0,ang:0,spd:0,lvl:0,L:70,Lt:70,wag:0,chomp:0,meter:0,run:0,air:false,vx:0,vy:0,h:0,sq:0,cool:0,perfect:false,face:1};
const fish=[],surf=[],parts=[],pops=[];
const divers=[];const amb={on:false,t:0,x:0,y:0,x0:0,y0:0,dir:1,phase:"",lt:0,reachT:-1,ate:false,spr:null,L:0};
let netHits=0,surfersCaught=0,ambCool=0,bannerT=0,diverTipT=0,diverSpr=null,struggles=0;
TIERS.forEach((t,ti)=>{for(let i=0;i<t.n;i++)fish.push({x:0,y:0,vx:0,vy:0,ph:Math.random()*6,tier:ti,s:t.s,danger:false,bump:0})});
for(let i=0;i<N_SURF;i++)surf.push({x:0,vx:0,ph:Math.random()*6,k:i===0?1:0,zip:0});
for(let i=0;i<MAX_PARTS;i++)parts.push({x:0,y:0,vx:0,vy:0,t:0});
for(let i=0;i<6;i++)pops.push({x:0,y:0,t:0,txt:""});
const waves=[];for(let i=0;i<10;i++)waves.push({x:Math.random(),y:Math.random(),w:20+Math.random()*30,sp:.006+Math.random()*.01});
let score=0,timeLeft=ROUND_SECONDS,best=+(localStorage.getItem(BEST_KEY)||0),elapsed=0,endReason="",shake=0,hintT=0;
let calm=localStorage.getItem(CALM_KEY)==="1"||matchMedia("(prefers-reduced-motion: reduce)").matches;
const touch={on:false,x:0,y:0,dx:0,dy:0,drive:0};
let bg=null,sprC=null,sprO=null,fishSpr=[],surfSpr=[],title=null,tShark=null,tSharkO=null;
const need=l=>6+l*2;
const sharkL=l=>Math.min(W,H)*.2*trait("size")*(1+.1*l);
const bite=()=>shark.L*.4;
function rel(f){const r=f.s/bite();return r<.87?-1:r>1.15?1:0}// -1 food, 0 same size (bump), 1 danger
const sharkMax=l=>Math.min(W,H)*.75*(1+.04*l)*trait("speed");
function buildSprites(){
 SURF=Math.max(safeTop()+120,H*.2);BED=H-Math.max(28,H*.04);
 bg=mk(W*DPR,H*DPR);const g=bg.getContext("2d");g.scale(DPR,DPR);
 let gr=g.createLinearGradient(0,0,0,SURF);gr.addColorStop(0,"#7fd3ff");gr.addColorStop(1,"#d8f3ff");g.fillStyle=gr;g.fillRect(0,0,W,SURF);
 g.fillStyle="#fff7c2";g.beginPath();g.arc(W*.84,SURF*.42,22,0,7);g.fill();
 g.fillStyle="#fff";for(const [x,y,r] of[[.18,.35,16],[.26,.33,22],[.34,.36,15],[.6,.25,12],[.66,.23,17]]){g.beginPath();g.arc(W*x,SURF*y,r,0,7);g.fill()}
 gr=g.createLinearGradient(0,SURF,0,H);gr.addColorStop(0,"#1aa6dc");gr.addColorStop(.6,"#0b6a9c");gr.addColorStop(1,"#08466e");g.fillStyle=gr;g.fillRect(0,SURF,W,H-SURF);
 g.fillStyle="rgba(255,255,255,.06)";for(let i=0;i<5;i++){g.beginPath();g.moveTo(W*(.1+i*.2),SURF);g.lineTo(W*(.02+i*.2),H*.75);g.lineTo(W*(.14+i*.2),H*.75);g.closePath();g.fill()}
 g.fillStyle="#e9c77b";g.strokeStyle=P.ink;g.lineWidth=3;g.beginPath();g.moveTo(0,BED);for(let x=0;x<=W;x+=40)g.quadraticCurveTo(x+20,BED-8,x+40,BED);g.lineTo(W,H);g.lineTo(0,H);g.closePath();g.fill();g.stroke();
 g.fillStyle="#2fa36b";for(const x of[.08,.3,.72,.9]){g.beginPath();g.moveTo(W*x,BED);g.quadraticCurveTo(W*x-14,BED-40,W*x,BED-70);g.quadraticCurveTo(W*x+10,BED-40,W*x+6,BED);g.fill();g.stroke()}
 g.strokeStyle=P.ink;g.lineWidth=3;g.beginPath();g.moveTo(0,SURF);g.lineTo(W,SURF);g.stroke();
 buildShark();
 {const s=DIVER_SIZE,c=mk(s*2.5*DPR,s*.9*DPR),q=c.getContext("2d");q.scale(DPR,DPR);q.translate(s*1.15,s*.45);drawDiver(q,s);diverSpr=c}
 fishSpr=TIERS.map((t,ti)=>[0,1].map(d=>{const s=t.s,pad=d?6:2,c=mk((s*1.8+pad*2)*DPR,(s*1.05+pad*2)*DPR),q=c.getContext("2d");q.scale(DPR,DPR);q.translate(s*.88+pad,s*.52+pad);drawFish(q,s,t.col,ti,d);return c}));
 surfSpr=[0,1].map(k=>{const s=60,c=mk(s*1.5*DPR,s*1.1*DPR),q=c.getContext("2d");q.scale(DPR,DPR);q.translate(s*.75,s*.98);drawSurfer(q,s,k);return c});
 const tw=Math.min(W*.94,520);title=render3DTitle(tw*DPR);title.dw=tw;const L=Math.min(W*.62,330)*DPR;tShark=render3DShark(L,false,TYPES[sType],true);tSharkO=render3DShark(L,true,TYPES[sType],true);tShark.L=tSharkO.L=L/DPR}
function buildShark(){const L=sharkL(shark.lvl);shark.L=L;sprC=render3DShark(L*DPR,false,TYPES[sType]);sprO=render3DShark(L*DPR,true,TYPES[sType]);sprC.L=sprO.L=L}
let _st=-1;function safeTop(){if(_st<0){const d=document.createElement("div");d.style.cssText="position:fixed;top:env(safe-area-inset-top);";document.body.appendChild(d);_st=d.getBoundingClientRect().top||0;d.remove()}return _st}
function resize(){DPR=Math.min(2,window.devicePixelRatio||1);W=innerWidth;H=innerHeight;C.width=Math.round(W*DPR);C.height=Math.round(H*DPR);buildSprites();if(state!=="play")placeAll()}
function rnd(a,b){return a+Math.random()*(b-a)}
function spawnFish(f,edge){const big=f.tier>=2||(state==="play"&&rel(f)>0);for(let k=0;k<12;k++){const side=Math.random()<.5;f.x=(edge||big)?(side?-f.s:W+f.s):rnd(20,W-20);f.y=rnd(SURF+40,BED-30);
 if(state!=="play"||Math.hypot(f.x-shark.x,f.y-shark.y)>Math.min(W,H)*(big||elapsed<SAFE_SPAWN_S?.6:.25))break}
 const dir=f.x<W/2?1:-1;f.vx=dir*rnd(25,45)*(f.tier>=2?.7:1);f.vy=0;f.bump=0}
function spawnSurf(s,edge){s.zip=0;s.x=edge?(Math.random()<.5?-50:W+50):rnd(50,W-50);s.vx=(Math.random()<.5?-1:1)*rnd(25,45);s.k=Math.random()<.35?1:0}
function placeAll(){for(const f of fish)spawnFish(f,false);for(const s of surf)spawnSurf(s,false)}

// ---------- audio (one AudioContext, synthesized SFX, capped voices) ----------
const FAST_SFX={AT:.7,COOL:1.5};// bubbles when speed rises past 70% of max (upward crossing only), at most once per 1.5 s
const MAX_VOICES=8;
let AC=null,soundOn=localStorage.getItem(SND_KEY)!=="0",sfx=null,noiseBuf=null,voices=0,music={title:null,game:null,cur:null},chip={buf:null,src:null,bus:null,t0:0,failed:false,want:false},placeholder=null,phT0=0;
const sfxCount={chomp:0,bubbles:0,gulp:0,played:0};// test hooks: requested count per sound; "played" = actually sounded (unmuted)
function initAudio(){if(!AC){try{AC=new (window.AudioContext||window.webkitAudioContext)();sfx=AC.createGain();sfx.gain.value=.45;sfx.connect(AC.destination);
  noiseBuf=AC.createBuffer(1,Math.floor(AC.sampleRate*.12),AC.sampleRate);const d=noiseBuf.getChannelData(0);for(let i=0;i<d.length;i++)d[i]=(Math.random()*2-1)*(1-i/d.length)}catch(e){AC=null}
 music.title=new Audio("audio/title-cathedrale.ogg");music.title.loop=true;music.title.preload="auto";music.title.volume=0;
 loadChip()}
 if(AC&&AC.state==="suspended")AC.resume().catch(()=>{})}
// Gameplay music: Slopcore's 8-bit "Reflets dans l'eau" v2, played as a WebAudio buffer loop (sample-accurate, no gap at the loop point).
// If it fails to load or decode, the original placeholder loop below is the fallback.
const CHIP_URL="audio/gameplay-chiptune.ogg",MUSIC_VOL={title:.8,game:.3};// game track is ~9 dB louder than the title file, so it plays lower to sit under the SFX
function loadChip(){if(!AC||chip.buf||chip.loading)return;chip.loading=true;fetch(CHIP_URL).then(r=>{if(!r.ok)throw new Error("chip "+r.status);return r.arrayBuffer()})
 .then(b=>new Promise((ok,no)=>AC.decodeAudioData(b,ok,no))).then(buf=>{chip.buf=buf;if(chip.want&&placeholder){phStop();chipStart()}}).catch(()=>{chip.failed=true})}
function chipStart(){if(!AC||!chip.buf||chip.src)return;const bus=AC.createGain(),t=AC.currentTime;bus.gain.setValueAtTime(0,t);bus.gain.linearRampToValueAtTime(soundOn?MUSIC_VOL.game:0,t+.6);bus.connect(AC.destination);
 const src=AC.createBufferSource();src.buffer=chip.buf;src.loop=true;src.connect(bus);src.start(t);chip.src=src;chip.bus=bus;chip.t0=t}
function chipStop(){if(!chip.src)return;const s=chip.src,b=chip.bus;try{b.gain.setTargetAtTime(0,AC.currentTime,.15);s.stop(AC.currentTime+.8);setTimeout(()=>b.disconnect(),1000)}catch(e){}chip.src=null;chip.bus=null}
function voice(dur){if(!AC||!soundOn||voices>=MAX_VOICES)return false;voices++;setTimeout(()=>voices--,dur*1000+60);sfxCount.played++;return true}
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
 splash(){noise(.12,.3,900)},launch(){blip(180,520,.18,"triangle",.25)},ripple(){blip(300,420,.08,"sine",.15)},bump(){blip(220,180,.06,"triangle",.18)},
 divers(){[880,660,880,660].forEach((f,i)=>blip(f,f,.11,"square",.14,i*.13))},net(){noise(.1,.25,1400);blip(400,200,.2,"triangle",.25)},ambush(){blip(110,90,.5,"sawtooth",.16);blip(130,100,.45,"sawtooth",.12,.3)},caught(){[523,494,466,440].forEach((f,i)=>blip(f,f,.18,"triangle",.25,i*.15))},
 perfect(){blip(1047,1568,.12,"square",.15)},end(){[784,659,523,392].forEach((f,i)=>blip(f,f*.98,.2,"triangle",.25,i*.16))}};
// FALLBACK only (used if the chiptune file fails to load/decode): tiny ORIGINAL 8-bit loop (not Debussy, not the real track) at BEAT.PLACEHOLDER_BPM, cheap look-ahead scheduler.
const PH_NOTES=[63,70,75,79, 61,68,73,77, 60,67,72,75, 58,65,70,74];const PH_BASS=[39,37,36,34];
function phStart(){if(!AC||placeholder)return;const bus=AC.createGain();bus.gain.value=soundOn?.1:0;bus.connect(AC.destination);let step=0,next=AC.currentTime+.05;phT0=next;const st=30/BEAT.PLACEHOLDER_BPM;
 const tick=()=>{while(next<AC.currentTime+.25){const m=440*Math.pow(2,(PH_NOTES[step%16]-69)/12),o=AC.createOscillator(),g=AC.createGain();o.type="square";o.frequency.value=m;g.gain.setValueAtTime(.5,next);g.gain.exponentialRampToValueAtTime(.01,next+st*.8);o.connect(g);g.connect(bus);o.start(next);o.stop(next+st*.85);
   if(step%4===0){const b=AC.createOscillator(),g2=AC.createGain();b.type="triangle";b.frequency.value=440*Math.pow(2,(PH_BASS[(step>>2)%4]-69)/12);g2.gain.setValueAtTime(.9,next);g2.gain.linearRampToValueAtTime(0,next+st*3.8);b.connect(g2);g2.connect(bus);b.start(next);b.stop(next+st*3.9)}
   step++;next+=st}};placeholder={bus,id:setInterval(tick,100)};tick()}
function phStop(){if(!placeholder)return;clearInterval(placeholder.id);const b=placeholder.bus;try{b.gain.setTargetAtTime(0,AC.currentTime,.2);setTimeout(()=>b.disconnect(),800)}catch(e){}placeholder=null}
let fadeId=0;
function playMusic(which){const id=++fadeId,from=music.cur,to=which==="title"?music.title:null;chip.want=which==="game";
 if(which==="game"){if(chip.buf)chipStart();else phStart()}else{phStop();chipStop()}music.cur=to;if(to&&soundOn)to.play().catch(()=>{});
 let k=0;const step=()=>{if(id!==fadeId)return;k+=.1;if(from&&from!==to)from.volume=Math.max(0,from.volume-.1);if(to)to.volume=soundOn?Math.min(MUSIC_VOL.title,k*MUSIC_VOL.title):0;if(k<1)setTimeout(step,60);else if(from&&from!==to)from.pause()};step()}
function setSound(on){soundOn=on;localStorage.setItem(SND_KEY,on?"1":"0");$("snd").textContent=on?"🔊 Sound on":"🔈 Sound off";if(placeholder)placeholder.bus.gain.value=on?.1:0;if(chip.bus){chip.bus.gain.cancelScheduledValues(AC.currentTime);chip.bus.gain.value=on?MUSIC_VOL.game:0}
 for(const a of[music.title])if(a){if(on&&a===music.cur){a.volume=MUSIC_VOL.title;a.play().catch(()=>{})}else a.volume=0}}

// ---------- title ----------
const T={t:0,bitten:false,done:false,shX:0};const TITLE_SWIM=2.4;
function startTitle(){state="title";T.t=0;T.bitten=false;T.done=false;window.__saTitleDone=false;title=render3DTitle(Math.min(W*.94,520)*DPR);title.dw=Math.min(W*.94,520);show("titleUi")}
function titleRect(){const tw=title.dw,th=title.height*(tw/title.width);return {x:(W-tw)/2,y:Math.max(safeTop()+20,H*.12),w:tw,h:th}}
function updTitle(dt){T.t+=dt;const r=titleRect(),L=tShark.L,p=Math.min(1,T.t/TITLE_SWIM);T.shX=-L*.8+p*(W+L*1.6);const biteX=r.x+r.w*.62;
 if(!T.bitten&&T.shX+L*.45>=biteX){T.bitten=true;biteTitle(title,(biteX-r.x)/r.w*title.width,title.height*.62,title.height*.2);SFX.chomp();addPop(biteX,r.y+r.h*.5,"CHOMP!");for(let i=0;i<10;i++)spark(biteX,r.y+r.h*.6,1)}
 if(p>=1&&!T.done&&T.t>TITLE_SWIM+.3){T.done=true;window.__saTitleDone=true}}
function drawTitle(t){const r=titleRect();X.drawImage(title,r.x,r.y+Math.sin(t*1.5)*3,r.w,r.h);
 if(T.t<TITLE_SWIM){const sy=r.y+r.h*.55,open=T.shX>r.x+r.w*.35&&T.shX<r.x+r.w*.75&&!(T.bitten&&T.shX>r.x+r.w*.7),s=open?tSharkO:tShark,dw=s.width/DPR,dh=s.height/DPR;X.drawImage(s,T.shX-dw/2-s.L*.05,sy-dh/2+Math.sin(t*6)*4,dw,dh)}
 else{const fx=W/2+Math.cos(t*.6)*W*.3,fy=SURF;X.fillStyle=TYPES[sType].body;X.strokeStyle=P.ink;X.lineWidth=3;X.beginPath();X.moveTo(fx-16,fy);X.lineTo(fx+(Math.sin(t*.6)>0?-6:6),fy-30);X.lineTo(fx+16,fy);X.closePath();X.fill();X.stroke()}}

// ---------- play ----------
let lastBub=-9,wasFast=false;
function startGame(){hideAll();state="play";score=0;elapsed=0;endReason="";roundLen=window.__saRound||ROUND_SECONDS;timeLeft=roundLen;
 shark.lvl=0;shark.meter=0;buildShark();shark.Lt=shark.L;shark.x=W/2;shark.y=(SURF+BED)/2;shark.ang=0;shark.spd=sharkMax(0)*.25;shark.run=0;shark.air=false;shark.h=0;shark.cool=0;shark.sq=0;
 touch.on=false;touch.drive=0;shake=0;shark.stun=0;shark.safe=0;divers.length=0;amb.on=false;amb.ate=false;netHits=0;surfersCaught=0;ambCool=0;bannerT=0;diverTipT=0;struggles=0;touch.strug=0;wasFast=false;lastBub=-9;for(const p of parts)p.t=0;for(const p of pops)p.t=0;placeAll();playMusic("game");
 hintT=localStorage.getItem(HINT_KEY)?0:6;localStorage.setItem(HINT_KEY,"1")}
function spark(x,y,big){for(const p of parts)if(p.t<=0){const a=Math.random()*6.28,v=rnd(40,140)*(big?1.4:1);p.x=x;p.y=y;p.vx=Math.cos(a)*v;p.vy=Math.sin(a)*v-(big?60:0);p.t=.5;return}}
function addPop(x,y,txt){let o=pops[0];for(const p of pops)if(p.t<o.t)o=p;o.x=Math.max(50,Math.min(W-50,x));o.y=y;o.t=1;o.txt=txt}
function addScore(n){score+=n}
function feed(g){if(shark.lvl>=MAX_LEVEL){shark.meter=need(shark.lvl);return}shark.meter+=g*trait("grow");
 while(shark.meter>=need(shark.lvl)&&shark.lvl<MAX_LEVEL){shark.meter-=need(shark.lvl);shark.lvl++;const keep=shark.L;buildShark();shark.Lt=shark.L;shark.L=keep;SFX.grow();addPop(shark.x,shark.y-shark.L*.6,"BIGGER!")}}
function beatLen(){return 60/(chip.src?BEAT.CHIPTUNE_BPM:BEAT.PLACEHOLDER_BPM)}
function beatNow(){if(chip.src)return (AC.currentTime-chip.t0)%chip.buf.duration;if(placeholder&&AC)return AC.currentTime-phT0;return elapsed}
function mouth(){const k=shark.L*.48;return [shark.x+Math.cos(shark.ang)*k,shark.y+Math.sin(shark.ang)*k]}
function angDiff(a,b){let d=b-a;while(d>Math.PI)d-=6.2832;while(d<-Math.PI)d+=6.2832;return d}
function power(){const max=sharkMax(shark.lvl);return Math.min(1,LAUNCH.K*(shark.spd/max)*(shark.run/H))}
function canLaunch(){return shark.spd>=sharkMax(shark.lvl)*LAUNCH.MIN_SPEED&&power()>=LAUNCH.MIN_POWER}
function launch(){const p=power(),g0=LAUNCH.G*H,hm=LAUNCH.H_MAX*H*p*trait("leap"),vy0=Math.sqrt(2*g0*hm);let T=2*vy0/g0,g=g0,assisted=false;
 if(BEAT.on){const bl=beatLen(),tl=beatNow()+T,d=Math.round(tl/bl)*bl-tl;if(Math.abs(d)*1000<=BEAT.ASSIST_MS){T+=d;g=2*vy0/T;assisted=true}}// time-stretch the arc so it lands on the beat
 shark.air=true;shark.g=g;shark.vy=-vy0;shark.vx=Math.cos(shark.ang)*shark.spd*.85;shark.perfect=assisted;shark.sq=.12;shark.run=0;shark.peak=vy0*vy0/(2*g);
 window.__saLastLaunch={power:p,height:shark.peak,air:T,base:2*vy0/g0,assisted};SFX.launch();SFX.splash();for(let i=0;i<8;i++)spark(shark.x,SURF,1);addPop(shark.x,SURF-20,p>.7?"BIG AIR!":"WHOOSH!")}
function gameOver(why){endReason=why;endRound()}
function struggle(d){touch.strug=(touch.strug||0)+d;while(touch.strug>=W*STRUGGLE_PX&&shark.stun>0){touch.strug-=W*STRUGGLE_PX;shark.stun=Math.max(0,shark.stun-STRUGGLE_SHORTEN_MS/1000);struggles++;spark(shark.x,shark.y,0);SFX.bump()}}
function surferCaught(){surfersCaught++;const want=Math.min(DIVER_MAX,Math.floor(surfersCaught/DIVER_TRIGGER_SURFERS));while(divers.length<want)spawnDiver()}
function spawnDiver(x,y){let bx=0,by=0,bd=-1;
 for(let k=0;k<6;k++){const e=k%3,cx=e===0?-30:e===1?W+30:rnd(40,W-40),cy=e===2?SURF+20:rnd(SURF+40,BED-40),d=Math.hypot(cx-shark.x,cy-shark.y)-divers.reduce((m,o)=>Math.hypot(cx-o.x,cy-o.y)<80?m+999:m,0);if(d>bd){bd=d;bx=cx;by=cy}}// edge or surface, farthest from the shark
 const d={x:x??bx,y:y??by,ang:0,st:"wander",grace:DIVER_GRACE_MS/1000,cool:0,lost:0,wt:0,ph:Math.random()*6};d.ang=Math.atan2(shark.y-d.y,shark.x-d.x);divers.push(d);
 bannerT=1.5;SFX.divers();if(!localStorage.getItem(DIVER_TIP_KEY)){diverTipT=4.5;localStorage.setItem(DIVER_TIP_KEY,"1")}return d}
function diverSpeed(){return sharkMax(shark.lvl)*DIVER_SPEED_FRACTION}
function netPt(d){return [d.x+Math.cos(d.ang)*DIVER_SIZE*.98,d.y+Math.sin(d.ang)*DIVER_SIZE*.98]}
function wantAmbush(n){if(amb.on||ambCool>0)return false;const r=AMBUSH_ON_HIT[Math.min(n,3)];if(r!==null)return r;if(window.__saAmbushForce!=null)return window.__saAmbushForce;return Math.random()<AMBUSH_CHANCE}
function netHit(d){netHits++;if(d)d.cool=DIVER_COOLDOWN_MS/1000;SFX.net();addPop(shark.x,shark.y-shark.L*.5,"NETTED!");shark.meter=Math.max(0,shark.meter-DIVER_GROWTH_LOSS);
 if(netHits>=DIVER_CATCHES_TO_LOSE){gameOver("caught");return}
 const a=wantAmbush(netHits);shark.stun=(a?AMBUSH_STUN_MS:STUN_MS)/1000;touch.strug=0;if(a)startAmbush()}
function startAmbush(){const L=shark.L*AMBUSHER_SIZE;amb.on=true;amb.t=0;amb.phase="come";amb.reachT=-1;amb.ate=false;amb.dir=shark.x<W/2?-1:1;// enters from the farther edge
 amb.x0=amb.dir<0?W+L*.7:-L*.7;amb.y0=Math.max(SURF+L*.25,Math.min(BED-L*.25,shark.y+rnd(-40,40)));amb.x=amb.x0;amb.y=amb.y0;
 if(amb.L!==L||!amb.spr){amb.L=L;amb.spr=render3DShark(L*DPR,true,AMB_T);amb.spr.L=L}ambCool=AMBUSH_COOLDOWN_MS/1000;SFX.ambush();window.__saLastAmbush=amb}
function updDivers(dt){if(ambCool>0)ambCool-=dt;if(bannerT>0)bannerT-=dt;if(diverTipT>0)diverTipT-=dt;
 const v=diverSpeed(),range=H*DIVER_DETECT_RANGE,L=shark.L;
 for(const d of divers){d.ph+=dt*5;if(d.grace>0)d.grace-=dt;if(d.cool>0)d.cool-=dt;const dist=Math.hypot(shark.x-d.x,shark.y-d.y);
  if(d.cool>0){d.st="wander";d.wa=Math.atan2(d.y-shark.y,d.x-shark.x);d.wt=.5}else   if(dist<range&&!shark.air){d.st="chase";d.lost=0}else if(d.st==="chase"){d.lost+=dt;if(d.lost*1000>=DIVER_GIVEUP_MS)d.st="wander"}
  let tgt,sp;if(d.st==="chase"){tgt=Math.atan2(shark.y-d.y,shark.x-d.x);sp=v}else{d.wt-=dt;if(d.wt<=0){d.wt=rnd(1.2,2.5);d.wa=d.ang+rnd(-1.4,1.4)}tgt=d.wa??d.ang;sp=v*.45}
  d.ang+=angDiff(d.ang,tgt)*Math.min(1,dt*2.5);d.x+=Math.cos(d.ang)*sp*dt;d.y+=Math.sin(d.ang)*sp*dt;
  if(d.y<SURF+16){d.y=SURF+16;d.ang=Math.abs(d.ang)}if(d.y>BED-20){d.y=BED-20;d.ang=-Math.abs(d.ang)}// stays in the water
  if(d.x<-40){d.x=-40;d.ang=Math.PI-d.ang;d.wa=0}else if(d.x>W+40){d.x=W+40;d.ang=Math.PI-d.ang;d.wa=Math.PI}
  if(d.grace<=0&&d.cool<=0&&!shark.air&&shark.stun<=0&&shark.safe<=0){const [nx,ny]=netPt(d),r=L*DIVER_NET_REACH+8;if((nx-shark.x)**2+(ny-shark.y)**2<r*r){netHit(d);if(state!=="play")return}}}
 if(amb.on){amb.t+=dt;const La=amb.L;
  if(amb.phase==="come"){const k=Math.min(1,amb.t*1000/AMBUSH_ARRIVE_MS),e=k*k*(3-2*k);amb.x=amb.x0+(shark.x-amb.dir*L*.2-amb.x0)*e;amb.y=amb.y0+(shark.y-amb.y0)*e;
   if(Math.hypot(amb.x-shark.x,amb.y-shark.y)<La*.15&&amb.reachT<0)amb.reachT=amb.t;
   if(k>=1){if(shark.stun>0&&!shark.air){amb.ate=true;gameOver("eaten");return}amb.phase="leave";amb.lt=0;addPop(shark.x,shark.y-L*.6,"ESCAPED!")}}
  else{amb.lt+=dt;const sp=amb.lt*1000<AMBUSHER_LEAVE_MS?40:320;amb.x-=amb.dir*sp*dt;amb.y+=Math.sin(amb.lt*2)*20*dt;// circles off slowly, then swims away
   if(amb.lt*1000>=AMBUSHER_LEAVE_MS&&(amb.x<-La||amb.x>W+La))amb.on=false}}}
function updPlay(dt){elapsed+=dt;timeLeft-=dt;if(hintT>0)hintT-=dt;if(timeLeft<=0){timeLeft=0;gameOver("time");return}
 shark.L+=(shark.Lt-shark.L)*Math.min(1,dt*4);if(shake>0)shake-=dt;if(shark.cool>0)shark.cool-=dt;if(shark.sq>0)shark.sq-=dt;shark.wag+=dt*(4+shark.spd/40);if(shark.chomp>0)shark.chomp-=dt;
 const max=sharkMax(shark.lvl),L=shark.L;
 if(shark.air){// ballistic arc: safe from fish, can grab surfers
  shark.vy+=shark.g*dt;shark.x+=shark.vx*dt;shark.y+=shark.vy*dt;shark.ang=Math.atan2(shark.vy,shark.vx);shark.h=Math.max(0,SURF-shark.y);
  if(shark.x<L*.3||shark.x>W-L*.3){shark.vx=-shark.vx;shark.x=Math.max(L*.3,Math.min(W-L*.3,shark.x))}
  if(shark.y>=SURF&&shark.vy>0){shark.air=false;shark.h=0;shark.y=SURF+2;shark.spd=Math.min(max,Math.hypot(shark.vx,shark.vy)*.6);shark.cool=LAUNCH.COOL;SFX.splash();if(!calm)shake=.22;shark.sq=.12;
   for(let i=0;i<12;i++)spark(shark.x,SURF,1);const bl=beatLen(),off=Math.abs(((beatNow()+bl/2)%bl)-bl/2)*1000;window.__saLastLand={offMs:off};
   if(BEAT.on&&off<=BEAT.PERFECT_MS){addScore(BEAT.PERFECT_BONUS);SFX.perfect();addPop(shark.x,SURF-30,"PERFECT! +"+BEAT.PERFECT_BONUS)}}}
 else{
  if(shark.safe>0&&shark.stun<=0)shark.safe-=dt;
  if(shark.stun>0){shark.stun=Math.max(0,shark.stun-dt);shark.safe=DIVER_SAFE_AFTER_STUN_MS/1000;touch.drive=0;shark.ang+=Math.sin(elapsed*25)*dt*2}
  else if(touch.on){shark.ang+=angDiff(shark.ang,touch.dir)*Math.min(1,dt*STEER.TURN*trait("turn"));if(performance.now()-touch.lastMove>80)touch.drive=Math.max(0,touch.drive-dt*STEER.DRIVE_DECAY)}
  else touch.drive=Math.max(0,touch.drive-dt*STEER.DRIVE_DECAY*2);
  const tgt=shark.stun>0?0:max*(touch.on?STEER.MIN+(1-STEER.MIN)*touch.drive:STEER.MIN);
  shark.spd+=(tgt-shark.spd)*Math.min(1,dt*(tgt>shark.spd?STEER.ACC*trait("acc"):STEER.DEC));// eased = weighty
  shark.x+=Math.cos(shark.ang)*shark.spd*dt;shark.y+=Math.sin(shark.ang)*shark.spd*dt;
  if(shark.spd>max*.45)shark.run+=shark.spd*dt*(shark.spd/max);else shark.run*=Math.exp(-dt*2);shark.run=Math.min(shark.run,H*1.2);
  const fr=shark.spd/max;if(fr>=FAST_SFX.AT&&!wasFast&&elapsed-lastBub>=FAST_SFX.COOL){SFX.bubbles();lastBub=elapsed;for(let i=0;i<3;i++)spark(shark.x-Math.cos(shark.ang)*L*.5,shark.y,0)}wasFast=fr>=FAST_SFX.AT;
  // surface: launch if fast with enough run-up, else bump back down with a ripple
  if(shark.y-L*.08<=SURF){if(Math.sin(shark.ang)<LAUNCH.UP&&shark.cool<=0&&canLaunch())launch();
   else{shark.y=SURF+L*.08;const sn=Math.sin(shark.ang);if(sn<-.5){shark.ang=-shark.ang;shark.spd*=.75;shark.run*=.5;SFX.ripple();addPop(shark.x,SURF+10,"splish");spark(shark.x,SURF,0)}else if(sn<0)shark.ang=Math.cos(shark.ang)>=0?0:Math.PI}}// steep: bump down; shallow: glide along the surface without losing speed
  if(!shark.air){const b=BED-L*.15;if(shark.y>b){shark.y=b;shark.ang=-Math.abs(shark.ang)}
   if(shark.x<L*.35){shark.x=L*.35;shark.ang=Math.PI-shark.ang}else if(shark.x>W-L*.35){shark.x=W-L*.35;shark.ang=Math.PI-shark.ang}}}
 updDivers(dt);if(state!=="play")return;
 const [mx,my]=mouth(),er=L*.2;
 for(const f of fish){f.ph+=dt*3;const dx=f.x-shark.x,dy=f.y-shark.y,d2=dx*dx+dy*dy,r=rel(f);f.danger=r>0;
  if(r<0&&!shark.air&&d2<(L*1.3)*(L*1.3)){const d=Math.sqrt(d2)||1;f.vy+=dy/d*60*dt;f.x+=dx/d*30*dt}
  if(r>0&&!shark.air&&d2<(L*3)*(L*3)){f.vy-=dy/Math.sqrt(d2+1)*15*dt}// big fish drift toward the shark a little
  f.vy*=.98;f.x+=f.vx*dt;f.y+=(f.vy+Math.sin(f.ph)*8)*dt;if(f.y<SURF+f.s*.6){f.y=SURF+f.s*.6;f.vy=Math.abs(f.vy)}if(f.y>BED-f.s*.6){f.y=BED-f.s*.6;f.vy=-Math.abs(f.vy)}
  if(f.x<-f.s*1.5)f.x=W+f.s;else if(f.x>W+f.s*1.5)f.x=-f.s;if(f.bump>0)f.bump-=dt;
  if(shark.air)continue;const t=TIERS[f.tier];
  if(r<0){const ex=f.x-mx,ey=f.y-my,rr=er+f.s*.4;if(ex*ex+ey*ey<rr*rr){addScore(t.pts);feed(t.grow);SFX.chomp();shark.chomp=.2;addPop(f.x,f.y,"+"+t.pts);for(let i=0;i<4;i++)spark(f.x,f.y,0);spawnFish(f,true)}}
  else{const rr=L*.32+f.s*.4;if(d2<rr*rr){if(r>0){const dir=f.vx<0?-1:1,fx=f.x+dir*f.s*.45,qx=fx-shark.x,qy=f.y-shark.y,q=L*.34+f.s*.15;if(qx*qx+qy*qy<q*q){gameOver("eaten");return}}
    const d=Math.sqrt(d2)||1;f.vy+=dy/d*80;shark.x-=dx/d*6;shark.y-=dy/d*6;if(f.bump<=0){SFX.bump();f.bump=.4}}}}
 for(const s of surf){s.ph+=dt*2;if(s.zip>0){s.zip-=dt;if(s.zip<=0)spawnSurf(s,true);continue}
  s.x+=s.vx*dt;if(s.x<-60)s.x=W+55;else if(s.x>W+60)s.x=-55;const hy=SURFERS[s.k].hy,cx=s.x,cy=SURF-hy;
  if(shark.air){const ex=cx-mx,ey=cy-my,rr=(L*.22+18)*trait("catchR");if(ex*ex+ey*ey<rr*rr){const pts=SURFERS[s.k].pts;addScore(pts);feed(2);SFX.pop();shark.chomp=.25;addPop(cx,cy-20,"+"+pts+" SPLASH!");for(let i=0;i<8;i++)spark(cx,SURF,1);s.zip=1.6;surferCaught()}}
  else if(Math.abs(cx-mx)<L*.4&&my<SURF+L*.3&&!(s.bump>0)){s.bump=.6;s.vx=(cx>shark.x?1:-1)*60;SFX.bump();addPop(cx,cy-20,"boing")}
  if(s.bump>0)s.bump-=dt}
 for(const p of parts)if(p.t>0){p.t-=dt;p.x+=p.vx*dt;p.y+=p.vy*dt;p.vx*=.94;p.vy=p.vy*.94+140*dt}}
function drawPlay(t){
 X.font="900 22px system-ui,sans-serif";X.textAlign="center";X.textBaseline="middle";X.lineWidth=5;X.strokeStyle=P.ink;
 for(const f of fish){const s=fishSpr[f.tier][f.danger?1:0],dw=s.width/DPR,dh=s.height/DPR;X.setTransform(f.vx<0?-DPR:DPR,0,0,DPR,f.x*DPR,f.y*DPR);X.drawImage(s,-dw/2,-dh/2,dw,dh)}
 X.setTransform(DPR,0,0,DPR,0,0);
 for(const f of fish){if(!f.danger)continue;if(f.x>0&&f.x<W){X.fillStyle="#ff2a2a";X.strokeText("!",f.x,f.y-f.s*.7);X.fillText("!",f.x,f.y-f.s*.7)}
  else if(Math.abs(f.x-W/2)<W/2+f.s*3){const ex=Math.max(18,Math.min(W-18,f.x)),d=f.x<0?-1:1;X.fillStyle="#ff2a2a";X.beginPath();X.moveTo(ex+d*12,f.y);X.lineTo(ex-d*8,f.y-12);X.lineTo(ex-d*8,f.y+12);X.closePath();X.fill();X.stroke();X.fillStyle="#fff";X.fillText("!",ex-d,f.y+1)}}
 for(const s of surf){if(s.zip>0)continue;const sp=surfSpr[s.k],dw=sp.width/DPR,dh=sp.height/DPR,y=SURF+Math.sin(s.ph)*2;X.setTransform(s.vx<0?-DPR:DPR,0,0,DPR,s.x*DPR,y*DPR);X.drawImage(sp,-dw/2,-dh*.89,dw,dh)}
 X.setTransform(DPR,0,0,DPR,0,0);
 for(const d of divers){const f=Math.cos(d.ang)<0?-1:1,dw=diverSpr.width/DPR,dh=diverSpr.height/DPR;X.setTransform(DPR*f,0,0,DPR,d.x*DPR,(d.y+Math.sin(d.ph)*2)*DPR);X.rotate(f>0?d.ang:-(d.ang-Math.PI));X.globalAlpha=d.grace>0?.55:1;X.drawImage(diverSpr,-DIVER_SIZE*1.15,-DIVER_SIZE*.45,dw,dh);X.globalAlpha=1}
 X.setTransform(DPR,0,0,DPR,0,0);X.lineWidth=4;X.strokeStyle=P.ink;
 for(const d of divers)if((d.x<0||d.x>W)&&Math.hypot(d.x-shark.x,d.y-shark.y)<H*.5){const ex=d.x<0?14:W-14,s=d.x<0?-1:1;X.fillStyle="#ff9a1e";X.beginPath();X.moveTo(ex+s*10,d.y);X.lineTo(ex-s*8,d.y-11);X.lineTo(ex-s*8,d.y+11);X.closePath();X.fill();X.stroke()}
 if(amb.on){const s=amb.spr,dw=s.width/DPR,dh=s.height/DPR,f=amb.phase==="come"?-amb.dir:amb.dir*-1*-1;const face=amb.phase==="come"?-amb.dir:amb.dir;
  X.setTransform(DPR*(face<0?-1:1),0,0,DPR,amb.x*DPR,amb.y*DPR);X.globalAlpha=amb.phase==="come"?.6+.4*Math.min(1,amb.t/(AMBUSH_ARRIVE_MS/1000)):.75;X.drawImage(s,-dw/2,-dh/2,dw,dh);X.globalAlpha=1;X.setTransform(DPR,0,0,DPR,0,0);
  if(amb.phase==="come"){const ex=Math.max(22,Math.min(W-22,amb.x)),ey=amb.y-amb.L*.35;X.font="900 40px system-ui,sans-serif";X.lineWidth=7;X.fillStyle="#ff2a2a";X.strokeText("!",ex,ey);X.fillText("!",ex,ey);X.font="900 22px system-ui,sans-serif";X.lineWidth=5}}
 const L=shark.L,ks=L/sprC.L,max=sharkMax(shark.lvl),sr=shark.spd/max;
 if(shark.air){const k=Math.max(.25,1-shark.h/(H*.35));X.fillStyle="rgba(4,30,50,.35)";X.beginPath();X.ellipse(shark.x,SURF+4,L*.4*k,6*k,0,0,7);X.fill()}// shadow on the water shrinks as it rises
 else{if(sr>.35){const c=Math.cos(shark.ang),sn=Math.sin(shark.ang),bx=shark.x-c*L*.55,by=shark.y-sn*L*.55,len=L*(.3+sr*.9);X.strokeStyle="rgba(235,252,255,"+(.2+sr*.4)+")";X.lineWidth=3;X.beginPath();
   for(const side of[-1,1]){X.moveTo(bx-sn*side*L*.08,by+c*side*L*.08);X.lineTo(bx-c*len-sn*side*len*.25,by-sn*len+c*side*len*.25)}X.stroke()}// wake = speed cue
  const pw=power(),ok=canLaunch();if(pw>.03){X.lineWidth=ok?5:3;X.strokeStyle=ok?"rgba(255,210,63,.95)":"rgba(235,252,255,.6)";X.beginPath();X.arc(shark.x,shark.y,L*.62,-Math.PI/2,-Math.PI/2+pw*6.283);X.stroke()}}// launch-power ring, gold = can leap
 const sq=shark.sq>0?Math.sin(shark.sq/.12*Math.PI):0,wob=Math.sin(shark.wag)*.04*(shark.air?0:1),flip=Math.cos(shark.ang)<0?-1:1;
 X.setTransform(DPR,0,0,DPR,shark.x*DPR,shark.y*DPR);X.rotate(shark.ang+wob);X.scale(ks*(1+sq*.15),ks*(1-sq*.18)*flip);
 const s=shark.chomp>0?sprO:sprC,dw=s.width/DPR,dh=s.height/DPR;X.globalAlpha=shark.safe>0&&shark.stun<=0&&Math.sin(t*20)<0?.45:1;X.drawImage(s,-dw/2-sprC.L*.05,-dh/2,dw,dh);X.globalAlpha=1;X.setTransform(DPR,0,0,DPR,0,0);
 if(shark.stun>0){X.fillStyle="#ffe14d";X.strokeStyle=P.ink;X.lineWidth=2;for(let i=0;i<4;i++){const a=t*5+i*1.57,x=shark.x+Math.cos(a)*L*.35,y=shark.y-L*.32+Math.sin(a)*L*.08;X.beginPath();for(let j=0;j<10;j++){const r=j%2?3:8,b=j*.628;X.lineTo(x+Math.cos(b)*r,y+Math.sin(b)*r)}X.closePath();X.fill();X.stroke()}
  if(amb.on&&amb.phase==="come"){X.font="900 20px system-ui,sans-serif";X.lineWidth=5;X.strokeText("WIGGLE TO BREAK FREE!",W/2,shark.y+L*.6);X.fillStyle="#fff";X.fillText("WIGGLE TO BREAK FREE!",W/2,shark.y+L*.6)}}}
function drawHud(){const top=safeTop()+8,mw=Math.min(150,W*.36),mx=(W-mw)/2,my=top+12,fr=shark.lvl>=MAX_LEVEL?1:shark.meter/need(shark.lvl);
 X.fillStyle=P.ink;X.fillRect(mx-3,my-3,mw+6,22);X.fillStyle="#bfe9ff";X.fillRect(mx,my,mw,16);X.fillStyle="#7be04a";X.fillRect(mx,my,mw*fr,16);
 X.font="900 13px system-ui,sans-serif";X.fillStyle=P.ink;X.textAlign="center";X.textBaseline="top";X.fillText(shark.lvl>=MAX_LEVEL?"MAX SIZE":"SIZE "+(shark.lvl+1),W/2,my+1);
 X.font="900 32px system-ui,sans-serif";X.lineJoin="round";X.lineWidth=7;X.strokeStyle=P.ink;X.textAlign="left";X.strokeText("🐟"+score,12,top);X.fillStyle="#fff";X.fillText("🐟"+score,12,top);
 const tl=Math.ceil(timeLeft),ts="⏱"+tl;X.textAlign="right";X.strokeText(ts,W-12,top);X.fillStyle=tl<=10?"#ffd23f":"#fff";X.fillText(ts,W-12,top);
 {const iy=top+48;for(let i=0;i<DIVER_CATCHES_TO_LOSE;i++){const x=W-22-i*26;X.lineWidth=2;X.strokeStyle=P.ink;X.fillStyle=i<netHits?"#e2463c":"rgba(255,255,255,.35)";X.beginPath();X.arc(x,iy,9,0,7);X.fill();X.stroke();X.lineWidth=1;X.beginPath();X.moveTo(x-6,iy-3);X.lineTo(x+6,iy-3);X.moveTo(x-6,iy+3);X.lineTo(x+6,iy+3);X.moveTo(x-3,iy-7);X.lineTo(x-3,iy+7);X.moveTo(x+3,iy-7);X.lineTo(x+3,iy+7);X.stroke()}}// net-hit icons
 if(bannerT>0){X.globalAlpha=Math.min(1,bannerT*3);X.textAlign="center";X.font="900 54px system-ui,sans-serif";X.lineWidth=9;X.strokeText("Divers!",W/2,SURF+140);X.fillStyle="#ff9a1e";X.fillText("Divers!",W/2,SURF+140);X.globalAlpha=1}
 if(diverTipT>0){X.globalAlpha=Math.min(1,diverTipT);X.textAlign="center";X.font="800 18px system-ui,sans-serif";X.lineWidth=6;const y=SURF+200;X.strokeText("Nets stun you.",W/2,y);X.strokeText("Big sharks love a stunned shark!",W/2,y+23);X.fillStyle="#fff";X.fillText("Nets stun you.",W/2,y);X.fillText("Big sharks love a stunned shark!",W/2,y+23);X.globalAlpha=1}
 if(hintT>0){X.globalAlpha=Math.min(1,hintT);X.textAlign="center";X.font="800 19px system-ui,sans-serif";X.lineWidth=6;const y=SURF+30;X.strokeText("Swim down to build speed,",W/2,y);X.strokeText("then swim up fast to leap!",W/2,y+24);X.fillStyle="#fff";X.fillText("Swim down to build speed,",W/2,y);X.fillText("then swim up fast to leap!",W/2,y+24);X.globalAlpha=1}
 X.textAlign="left"}
function endRound(){state="over";shark.air=false;shake=0;C.style.transform="";const eaten=endReason==="eaten",caught=endReason==="caught";shark.stun=0;amb.on=false;$("reason").textContent=eaten?"Gulp!":caught?"Caught!":"Time's up!";$("reason").className=eaten?"gulp":caught?"caught":"";
 if(score>best){best=score;localStorage.setItem(BEST_KEY,String(best))}$("final").textContent=score;$("bestTxt").textContent=(score>=best&&score>0?"🏆 New best! ":"Best: ")+best;
 $("roundNote").textContent=`Round length: ${roundLen} seconds (default — not yet confirmed).`;if(eaten)SFX.gulp();else if(caught)SFX.caught();else SFX.end();phStop();chipStop();chip.want=false;show("overUi")}

// ---------- shared draw ----------
function drawWater(t){X.setTransform(1,0,0,1,0,0);X.drawImage(bg,0,0);X.setTransform(DPR,0,0,DPR,0,0);X.strokeStyle=P.foam;X.lineWidth=3;X.lineCap="round";X.beginPath();
 for(const w of waves){const x=((w.x+t*w.sp)%1)*(W+80)-40,y=SURF+20+w.y*(BED-SURF-60)+Math.sin(t+w.x*9)*6;X.moveTo(x,y);X.quadraticCurveTo(x+w.w*.5,y-6,x+w.w,y)}X.stroke();
 X.strokeStyle="#e8fbff";X.lineWidth=4;X.beginPath();for(let x=0;x<=W;x+=24){const y=SURF+Math.sin(t*2+x*.05)*2.5;x?X.lineTo(x,y):X.moveTo(x,y)}X.stroke()}
function drawFx(dt){X.fillStyle="#e8fbff";X.strokeStyle=P.ink;X.lineWidth=1.5;for(const p of parts)if(p.t>0){const r=3+p.t*8;X.beginPath();X.arc(p.x,p.y,r,0,7);X.fill();X.stroke()}
 X.textAlign="center";X.textBaseline="middle";X.lineJoin="round";for(const p of pops)if(p.t>0){p.t-=dt*1.1;p.y-=dt*40;X.globalAlpha=Math.min(1,p.t*2);X.font="900 24px system-ui,sans-serif";X.lineWidth=6;X.strokeStyle=P.ink;X.strokeText(p.txt,p.x,p.y);X.fillStyle=P.yel;X.fillText(p.txt,p.x,p.y)}X.globalAlpha=1;X.textAlign="left"}

// ---------- loop ----------
let last=0,raf=0,fpsT=0,fpsN=0,fps=0;const perf={frames:0,js:0,dtSum:0,reset(){this.frames=0;this.js=0;this.dtSum=0}};
function frame(now){raf=requestAnimationFrame(frame);let dt=(now-last)/1000;if(state!=="play"&&dt<1/31)return;// menus: ~30 fps
 last=now;if(dt>.1)dt=.1;const t0=performance.now(),t=now/1000;
 if(state==="play")updPlay(dt);else if(state==="title")updTitle(dt);
 drawWater(t);if(state==="play"||state==="over"){if(shake>0){C.style.transform=`translate(${(Math.random()-.5)*6}px,${(Math.random()-.5)*6}px)`;C._sh=1}else if(C._sh){C.style.transform="";C._sh=0}drawPlay(t);drawFx(dt);drawHud()}
 else{if(state==="title"||state==="credits")drawTitle(t);drawFx(dt)}
 if(SHOW_FPS){fpsN++;fpsT+=dt;if(fpsT>.5){fps=Math.round(fpsN/fpsT);fpsN=0;fpsT=0}X.font="bold 14px monospace";X.fillStyle="#fff";X.textAlign="left";X.fillText(fps+" fps",8,H-14)}
 perf.frames++;perf.dtSum+=dt;perf.js+=performance.now()-t0}
function startLoop(){if(!raf){last=performance.now();raf=requestAnimationFrame(frame)}}
function stopLoop(){cancelAnimationFrame(raf);raf=0}
document.addEventListener("visibilitychange",()=>{if(document.hidden){stopLoop();if(music.cur)music.cur.pause();if(AC)AC.suspend()}else{startLoop();if(AC)AC.resume();if(music.cur&&soundOn)music.cur.play().catch(()=>{})}});

// ---------- UI ----------
function hideAll(){for(const id of["titleUi","overUi","credUi","pickUi","tap"])$(id).classList.add("hide")}
function show(id){hideAll();$(id).classList.remove("hide")}
// steering: the finger's slide direction is the swim direction; sliding distance builds drive (speed)
C.addEventListener("pointerdown",e=>{if(state!=="play")return;e.preventDefault();initAudio();touch.on=true;touch.x=e.clientX;touch.y=e.clientY;touch.dir=shark.ang;touch.sx=Math.cos(shark.ang);touch.sy=Math.sin(shark.ang);touch.lastMove=performance.now();try{C.setPointerCapture(e.pointerId)}catch(_){}});
C.addEventListener("pointermove",e=>{if(!touch.on)return;const dx=e.clientX-touch.x,dy=e.clientY-touch.y,d=Math.hypot(dx,dy);if(d<3)return;
 if(shark.stun>0){touch.x=e.clientX;touch.y=e.clientY;struggle(d);return}
 touch.sx=touch.sx*.55+dx/d*.45;touch.sy=touch.sy*.55+dy/d*.45;touch.dir=Math.atan2(touch.sy,touch.sx);touch.drive=Math.min(1,touch.drive+d/(W*STEER.DRIVE_PX));touch.lastMove=performance.now();touch.x=e.clientX;touch.y=e.clientY});
const up=()=>{touch.on=false};C.addEventListener("pointerup",up);C.addEventListener("pointercancel",up);
document.addEventListener("touchmove",e=>e.preventDefault(),{passive:false});document.addEventListener("gesturestart",e=>e.preventDefault());document.addEventListener("contextmenu",e=>e.preventDefault());// no long-press menu
document.addEventListener("pointerdown",()=>{if(AC&&AC.state==="suspended")AC.resume().catch(()=>{})},true);
function buildPick(){const box=$("pickList");box.innerHTML="";for(const k of Object.keys(TYPES)){const t=TYPES[k],b=document.createElement("button");b.className="pick"+(k===sType?" sel":"");b.dataset.type=k;
  const cv=render3DShark(110*2,false,t);cv.style.width="110px";cv.className="pv";b.appendChild(cv);
  const info=document.createElement("div");info.className="pinfo";info.innerHTML=`<b>${t.name}</b><span class="pdesc">${t.desc}</span>`+Object.entries(t.bars).map(([n,v])=>`<span class="bar" data-stat="${n}" data-v="${v}"><i>${n}</i><em style="width:${v*20}%"></em></span>`).join("");b.appendChild(info);
  b.onclick=()=>{sType=k;localStorage.setItem(TYPE_KEY,k);buildSprites();startGame()};box.appendChild(b)}}
$("tap").addEventListener("pointerdown",()=>{initAudio();startTitle();playMusic("title")});
$("start").onclick=()=>{initAudio();state="pick";buildPick();show("pickUi")};
$("pickBack").onclick=()=>{state="title";show("titleUi")};
$("again").onclick=()=>startGame();
$("home").onclick=()=>{buildSprites();startTitle();playMusic("title")};
$("snd").onclick=()=>setSound(!soundOn);
function setCalm(v){calm=v;localStorage.setItem(CALM_KEY,v?"1":"0");$("calm").textContent=v?"🌙 Calm (no shake)":"🌊 Shake on"}setCalm(calm);$("calm").onclick=()=>setCalm(!calm);
$("cred").onclick=()=>{state="credits";show("credUi")};
$("credBack").onclick=()=>{state="title";show("titleUi")};
window.addEventListener("resize",resize);
setSound(soundOn);resize();show("tap");startLoop();
if("serviceWorker" in navigator&&location.protocol!=="file:")navigator.serviceWorker.register("sw.js").catch(()=>{});

// ---------- test hooks ----------
window.__sa={get state(){return state},shark,fish,surf,touch,perf,sfxCount,TYPES,TIERS,LAUNCH,BEAT,STEER,FAST_SFX,SURFERS,MAX_LEVEL,ROUND_SECONDS,
 get score(){return score},get timeLeft(){return timeLeft},set timeLeft(v){timeLeft=v},get best(){return best},get endReason(){return endReason},get soundOn(){return soundOn},get chip(){return !!chip.buf},get chipPlaying(){return !!chip.src},get chipFailed(){return chip.failed},get acState(){return AC?AC.state:"none"},get looping(){return !!raf},MUSIC_VOL,get placeholder(){return !!placeholder},
 get type(){return sType},get SURF(){return SURF},get BED(){return BED},trait,maxSpeed:()=>sharkMax(shark.lvl),power,canLaunch,rel,feed,need,beatNow,beatLen,setRound(s){window.__saRound=s},
 clearFood(){for(const f of fish){f.x=-999;f.vx=0;f.vy=0}for(const s of surf)s.zip=999},
 placeFishAtMouth(ti){const f=fish.find(q=>q.tier===(ti||0)),[mx,my]=mouth();f.x=mx;f.y=my;f.vx=0;return fish.indexOf(f)},
 placeFishAt(ti,x,y,vx){const f=fish.find(q=>q.tier===ti);f.x=x;f.y=y;f.vx=vx||0;f.vy=0;return fish.indexOf(f)},
 placeSurfer(i,x,k){const s=surf[i];s.zip=0;s.x=x;s.vx=0;if(k!=null)s.k=k},divers,amb,get netHits(){return netHits},get surfersCaught(){return surfersCaught},get struggles(){return struggles},get ambCool(){return ambCool},set ambCool(v){ambCool=v},get bannerT(){return bannerT},
 DIV:{DIVER_TRIGGER_SURFERS,DIVER_SPEED_FRACTION,DIVER_DETECT_RANGE,DIVER_GIVEUP_MS,DIVER_GRACE_MS,DIVER_COOLDOWN_MS,DIVER_SAFE_AFTER_STUN_MS,DIVER_NET_REACH,DIVER_CATCHES_TO_LOSE,DIVER_MAX,STUN_MS,AMBUSH_STUN_MS,AMBUSH_ON_HIT,AMBUSH_CHANCE,AMBUSH_ARRIVE_MS,AMBUSH_COOLDOWN_MS,STRUGGLE_SHORTEN_MS,STRUGGLE_PX,AMBUSHER_SIZE,AMBUSHER_LEAVE_MS},
 render3DShark,sim(sec,bot,step){step=step||1/60;const n=Math.round(sec/step);let i=0;for(;i<n&&state==="play";i++){if(bot)bot(step);updPlay(step)}return i*step},startAs(t){sType=t;startGame()},surferCaught,spawnDiver,diverSpeed,netHit,struggle,setAmbushForce(v){window.__saAmbushForce=v},
 setLevel(l){shark.lvl=l;shark.meter=0;buildShark();shark.Lt=shark.L}};
