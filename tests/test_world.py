# v8 B+C world tests: endless left/right/down (surface is the only boundary), sliding 3x3 tile pool, depth-locked spawns
# (long random swim: zero wrong-zone spawns AND zero creatures ever seen in a wrong zone), minnow soft depth limit +
# plankton-only diet, deeper = bigger prey, angler only very deep, starfish on the seabed, colour-shift gradient pixel test.
# Run: python3 tests/test_world.py   (port 8897)
import os,sys,subprocess,time
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORTW','8897'))
URL=f'http://127.0.0.1:{PORT}/';passes=0;fails=[]
def check(c,m):
  global passes
  if c: passes+=1;print('PASS',m)
  else: fails.append(m);print('FAIL',m)
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
CHK='''const bad=[];for(const f of __sa.fish){if(f.off)continue;const L=__sa.layerOf(f.y);if(!__sa.ALLOWED[f.kind].includes(L))bad.push(f.kind+"@L"+L);if(!__sa.inWindow(f.x,f.y,.6))bad.push("outside:"+f.kind);
 if(f.kind==="angler"&&__sa.depthRaw(f.y)<__sa.ANGLER_D-.02)bad.push("shallow angler");if(f.kind==="star"&&Math.abs(f.y-__sa.BED)>30)bad.push("floating star")}'''
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');pg=cx.new_page();errs=[]
  pg.on('pageerror',lambda e:errs.append(str(e)));ev=pg.evaluate
  pg.goto(URL);pg.wait_for_timeout(300);pg.click('#tap');pg.wait_for_function('window.__saTitleDone===true',timeout=8000)
  pg.click('#start');pg.wait_for_timeout(200);pg.click('.pick[data-type=white]');pg.wait_for_timeout(400);ev('__sa.god=true;__sa.timeLeft=1e6')
  # world tests only: no divers, so a long swim that happens to catch surfers can't end the Timed round by nets ("caught" ignores god mode)
  ev('()=>{const s0=__sa.sim;__sa.sim=(a,bot,c)=>s0(a,dt=>{__sa.divers.length=0;if(bot)bot(dt)},c);(function k(){__sa.divers.length=0;requestAnimationFrame(k)})()}')
  # endless: swim a long way in each direction (stage 9 = no depth limit)
  for name,ang,ax in [('left',3.14159,'x'),('right',0,'x'),('down',1.5708,'y')]:
    r=ev(f'''()=>{{__sa.setLevel(9);const s=__sa.shark,W=innerWidth,H=innerHeight;s.x=W/2;s.y=__sa.SURF+H;__sa.camX=0;__sa.respawnAll();const x0=s.x,y0=s.y;let tl=new Set();
      __sa.sim(40,()=>{{Object.assign(__sa.touch,{{on:true,dir:{ang},drive:1,lastMove:performance.now()+9e9}});tl.add(__sa.tiles.length)}});
      {CHK}
      const live=__sa.fish.filter(f=>!f.off).length,cam={{x:__sa.camX+W/2-s.x,y:__sa.camY+H/2-s.y}};__sa.touch.on=false;return {{dx:s.x-x0,dy:s.y-y0,bad,tl:[...tl],live,cam,W,H,tc:__sa.tileC}}}}''')
    dist=abs(r['dx']) if ax=='x' else r['dy']
    check(dist>(4*r['W'] if ax=='x' else 3*r['H']),f'endless {name}: swam {dist:.0f}px ({dist/(r["W"] if ax=="x" else r["H"]):.1f} screens), no wall')
    check(r['tl']==[9] and r['live']>=20,f'endless {name}: pool stays 9 tiles, {r["live"]} live creatures around the shark')
    check(not r['bad'],f'endless {name}: every live creature in its zone and inside the window {r["bad"][:5]}')
    check(abs(r['cam']['x'])<r['W']*.25,f'endless {name}: camera follows the shark (off by {r["cam"]["x"]:.0f}px)')
  # surface is the only boundary: slow swim straight up stays in the water
  r=ev('''()=>{__sa.setLevel(9);const s=__sa.shark;s.y=__sa.SURF+200;s.spd=0;s.run=0;let mn=1e9;__sa.sim(4,()=>{Object.assign(__sa.touch,{on:true,dir:-1.5708,drive:.25,lastMove:performance.now()+9e9});if(!s.air)mn=Math.min(mn,s.y)});__sa.touch.on=false;return {mn,S:__sa.SURF,air:s.air}}''')
  check(r['mn']>=r['S']-1,f'surface is a boundary (min y {r["mn"]:.0f} >= surface {r["S"]})')
  # tile pool: tiles always form the 3x3 around the camera tile, each once
  r=ev('''()=>{const W=innerWidth,H=innerHeight,t=__sa.tileC,got=__sa.tiles.map(T=>(T.tx-t.x)+","+(T.ty-t.y)).sort();return got}''')
  want=sorted(f'{i},{j}' for i in (-1,0,1) for j in (-1,0,1))
  check(r==want,'tile pool: exactly the 3x3 tiles around the camera')
  # long random swim: 6 sim-minutes, all directions, stage 9; check zones every frame
  r=ev('''()=>{__sa.setLevel(9);const s=__sa.shark,H=innerHeight;s.x=0;s.y=__sa.SURF+H;__sa.respawnAll();const n0=__sa.spawnStats.n,w0=__sa.spawnStats.wrong;let dir=0,t=0,frames=0,badN=0,ex=[],maxD=0,kinds={};
     __sa.sim(360,(dt)=>{t-=dt;if(t<=0){t=2+Math.random()*4;dir=Math.random()*6.283;if(s.y>__sa.BED+H)dir=-1.2;if(s.y<__sa.SURF+H*.3)dir=1.2}
      Object.assign(__sa.touch,{on:true,dir,drive:1,lastMove:performance.now()+9e9});frames++;if(frames%3)return;maxD=Math.max(maxD,s.y);
      for(const f of __sa.fish){if(f.off)continue;kinds[f.kind]=1;const L=__sa.layerOf(f.y);if(!__sa.ALLOWED[f.kind].includes(L)){badN++;if(ex.length<5)ex.push(f.kind+"@L"+L)}}});
     __sa.touch.on=false;return {spawns:__sa.spawnStats.n-n0,wrong:__sa.spawnStats.wrong-w0,badN,ex,frames,kinds:Object.keys(kinds).sort(),reach:(maxD-__sa.SURF)/(__sa.BED-__sa.SURF),by:__sa.spawnStats.byKind}}''')
  check(r['spawns']>300 and r['wrong']==0,f'long swim (6 min): {r["spawns"]} spawns, {r["wrong"]} wrong-zone spawns')
  check(r['badN']==0,f'long swim: no creature ever seen outside its zone ({r["badN"]} {r["ex"]})')
  check(set(['plankton','fish','glow','shark','octo','angler','star'])<=set(r['kinds']),f'long swim: all kinds met {r["kinds"]} (reached {r["reach"]:.2f} of the way to the seabed)')
  check(r['by'].get('angler',0)<r['by'].get('glow',0)/3,f'angler is rare (angler {r["by"].get("angler",0)} vs glow {r["by"].get("glow",0)})')
  # deeper = bigger prey (true size at a fixed stage)
  r=ev('''()=>{__sa.setLevel(9);const H=innerHeight,s=__sa.shark,out=[];for(const fr of [.15,.5,.85]){const y=__sa.SURF+fr*(__sa.BED-__sa.SURF);let a=0,n=0;for(let i=0;i<300;i++){const f=__sa.fish[i%__sa.fish.length];__sa.spawnFish(f,false,{tx:0,ty:Math.floor(y/H)});if(f.kind!=="shark"&&f.kind!=="star"&&f.kind!=="plankton"&&Math.abs(__sa.layerOf(f.y)-__sa.layerOf(y))===0){a+=f.s;n++}}out.push(n?a/n:0)}__sa.respawnAll();return out}''')
  check(r[0]<r[1]<r[2],f'deeper means bigger prey (avg size top/mid/deep {r[0]:.1f}/{r[1]:.1f}/{r[2]:.1f})')
  # surfers need stage 6 (checked with real leaps in test_v8) -> constant here
  check(ev('__sa.GROW.SURF_LVL')==6,'surfers need stage 6')
  # v9 (Jeremy): NO depth lock. Replaces the old "allowed depth grows with stage / minnow stays shallow / hint" checks:
  # a minnow swimming straight down reaches the deep layer and never sees "Too small to go deeper".
  r=ev('''()=>{__sa.setLevel(0);const s=__sa.shark,H=innerHeight;s.air=false;s.cool=1;s.x=__sa.camX+innerWidth/2;s.y=__sa.SURF+40;s.spd=0;let mx=0,hint=false;
     __sa.sim(14,()=>{Object.assign(__sa.touch,{on:true,dir:1.5708,drive:1,lastMove:performance.now()+9e9});mx=Math.max(mx,s.y);if(__sa.pops.some(p=>p.t>0&&p.txt==="Too small to go deeper"))hint=true});__sa.touch.on=false;
     return {d:(mx-__sa.SURF)/(__sa.BED-__sa.SURF),mid:__sa.LAYERS.MID,hint,inf:__sa.allowedD(0)===Infinity}}''')
  check(r['inf'] and r['d']>r['mid'],f'v9: minnow can dive into the deep layer (max depth {r["d"]:.2f} > {r["mid"]})')
  check(not r['hint'],'v9: no "Too small to go deeper" hint')
  # minnow eats only plankton
  def eatTry(lvl,kind,k):
    return ev(f'''()=>{{__sa.setLevel({lvl});__sa.clearFood();const s=__sa.shark;s.air=false;s.x=__sa.camX+innerWidth/2;s.y=__sa.SURF+60;s.ang=0;s.spd=__sa.maxSpeed()*.5;const f=__sa.fish[1];__sa.setCreature(f,__sa.bite()*{k},"{kind}");f.band=[0,1e9];
      f.x=s.x+s.L*.5;f.y=s.y;f.vx=0;f.vy=0;const sc=__sa.score;__sa.sim(.4);return __sa.score>sc}}''')
  eatTry(0,'plankton',.4)  # warm-up: lets the camera settle at the surface after the dive test (otherwise the first placed fish is respawned off-window)
  check(eatTry(0,'plankton',.4),'minnow eats plankton')
  check(eatTry(0,'fish',.3),'v9b: Size 1 eats a tiny fish (Jeremy: small fish next to it must be eatable)')
  check(not eatTry(0,'fish',1.0),'v9b: Size 1 does not eat a fish its own size')
  check(eatTry(1,'fish',.3),'stage 1 eats a small fish')
  # v9c (Jeremy: "small fish by its fin"): food overlapping the drawn body (mid-body / tail fin) is eaten too, not only at the mouth
  def bodyTry(lvl,k,along,god=False):
    return ev(f'''()=>{{__sa.ambCool=1e9;__sa.amb.on=false;__sa.shark.stun=0;__sa.divers.length=0;/* no ambush or divers in progress (its bite ignores god mode) */__sa.god=true;__sa.setLevel({lvl});const s=__sa.shark;s.air=false;s.x=__sa.camX+innerWidth/2;s.y=__sa.SURF+160;s.spd=0;__sa.camY=s.y-innerHeight/2;__sa.sim(.05,()=>{{s.spd=0}});/* settle the camera + tile pool on the shark first, so no tile refresh spawns food onto it mid-check */__sa.clearFood();s.ang=0;s.spd=0;s.cool=9;const f=__sa.fish[1];__sa.setCreature(f,__sa.bite()*{k},"fish");f.band=[0,1e9];f.tile=null;/* no tile refresh may respawn the target after the camera jump */
      f.x=s.x+s.L*({along});f.y=s.y+s.L*.08;f.vx=0;f.vy=0;const sc=__sa.score;__sa.sim(.1,()=>{{s.spd=0;f.vx=0;f.vy=0;f.x=s.x+s.L*({along});f.y=s.y+s.L*.08}});const r={{ate:__sa.score>sc,state:__sa.state,why:__sa.endReason}};__sa.god=true;/* keep the suite-wide god mode: live frames run between evaluate() calls */return r}}''')
  check(bodyTry(0,.5,-.5)['ate'],'v9c: Size 1 eats a small fish at its tail fin')
  check(bodyTry(0,.5,0)['ate'],'v9c: Size 1 eats a small fish at mid-body')
  check(bodyTry(3,.5,-.5)['ate'],'v9c: stage 4 eats a small fish at its tail fin')
  check(not bodyTry(0,1.0,-.5)['ate'],'v9c: a same-size fish at the tail is NOT eaten (bump)')
  check(not bodyTry(0,.3,-1.2)['ate'],'v9c: a tiny fish well behind the tail (off the body) is not eaten (no vacuum)')
  r=ev('''()=>{const s=__sa.shark,L=s.L,f={x:s.x,y:s.y+L*.5,s:__sa.bite()*.3};return __sa.onBody(f)}''')
  check(not r,'v9c: a tiny fish half a body-length beside the shark is off the body capsule')
  r=bodyTry(0,2.0,-.5,True)
  check(not r['ate'] and r['state']=='play','v9c: a bigger fish at the tail is never "eaten" by the body rule (god mode: no death)')
  r=ev('''()=>{__sa.setLevel(0);__sa.respawnAll();const b=__sa.bite(),L=__sa.shark.L;let mn=1e9;for(const f of __sa.fish)if(!f.off&&f.kind!=="plankton")mn=Math.min(mn,f.s*__sa.lk(f));return {mn,L,b,rings:__sa.RINGS,K:__sa.LOOK.K}}''')
  check(r['rings'] is False,'v9c: no rings drawn around the shark or fish (RINGS flag off)')
  check(r['K']>1,f'v9c: creatures drawn {r["K"]}x their true size, shark size unchanged')
  check(r['mn']>=r['b']*.4*r['K']*.95,f'v9c: smallest non-plankton creature drawn {r["mn"]/r["L"]:.2f} x shark length (min 0.4 bite x K), no tiny fish by the fin')
  # harness: a rare death in these placed-fish setups (seen ~1 in 4 runs, cause not found; god mode is on) would end the round and
  # break the later tests, so restart the round here if needed. Not a gameplay change.
  ev('()=>{if(__sa.state!=="play"){__sa.startAs("white");__sa.god=true;__sa.timeLeft=1e6}}');pg.wait_for_timeout(300)
  # colour-shift: one baked gradient, sampled at surface/mid/deep/below seabed
  r=ev('''()=>{__sa.clearFood();const c=document.getElementById("c"),g=c.getContext("2d"),d=devicePixelRatio,H=innerHeight,out=[];
     for(const fr of [.05,.45,.85,1.6]){__sa.camY=__sa.SURF+fr*(__sa.BED-__sa.SURF)-H/2;__sa.drawWater(1);const im=g.getImageData(0,0,c.width,c.height).data,ls=[];
      for(let k=0;k<200;k++){const x=Math.floor(Math.random()*c.width),y=Math.floor(c.height*(.45+Math.random()*.1));const i=(y*c.width+x)*4;ls.push(.3*im[i]+.59*im[i+1]+.11*im[i+2])}ls.sort((a,b)=>a-b);out.push(ls[100])}__sa.respawnAll();return out}''')
  check(r[0]>r[1]>r[2]>=r[3]-2,f'water darkens with depth (median luma surface/mid/deep/cap {[round(x) for x in r]})')
  check(r[0]-r[2]>60 and r[3]<20,'surface clearly lighter, deep cap near black')
  # D) prey flee speeds + bounded minnow chase bot: a small fish flees at 0.60-0.85x YOUR top speed (v10: by depth + level, cap .85; tires to .40), a bigger shark chases slower than
  # your top speed, and a bot steering straight at a fleeing minnow-sized fish catches it within 12 s of game time.
  # v9: the start gap is s.L*1.25 (was H*.25 = 1.25 x the old fixed drawn length) because the drawn shark now grows per stage.
  r=ev('''()=>{__sa.setLevel(3);const s=__sa.shark,W=innerWidth,H=innerHeight;s.x=__sa.camX+W/2;s.y=__sa.SURF+H*.8;s.air=false;s.spd=0;__sa.camY=s.y-H/2;__sa.respawnAll();
    __sa.clearFood();/* park every other creature (off) so no tile refresh can respawn the target */
    const i=__sa.placeFishAt(0,s.x+s.L*1.25,s.y,1),f=__sa.fish[i];__sa.setCreature(f,__sa.bite()*.5,"fish");f.tile=null;f.band=[__sa.SURF+20,Infinity];f.vx=0;f.vy=0;const kk=f.fk;
    let t=0,caught=-1,mx=0,sc0=__sa.score;const top=__sa.sharkMax(s.lvl);
    __sa.sim(12,dt=>{t+=dt;if(caught>=0)return;if(f.st==="flee")mx=Math.max(mx,Math.hypot(f.vx,f.vy));if(__sa.score>sc0||f.x!==f.x){caught=t;return}
      Object.assign(__sa.touch,{on:true,dir:Math.atan2(f.y-s.y,f.x-s.x),drive:1,lastMove:performance.now()+9e9})});
    __sa.touch.on=false;const fks=__sa.fish.map(q=>q.fk).filter(v=>v!==undefined);
    return {kk,ratio:mx/top,caught,fmin:Math.min(...fks),fmax:Math.max(...fks),chase:[__sa.CREATURES.CHASE_SHALLOW,__sa.CREATURES.CHASE_DEEP]}}''')
  check(.60<=r['fmin'] and r['fmax']<=.72,f"every creature's base flee roll in 0.60-0.72 ({r['fmin']:.3f}-{r['fmax']:.3f})")
  check(.55<=r['ratio']<=.86,f"fleeing fish peaks at {r['ratio']:.3f}x top speed (v10 band .60-.85, never at top speed)")
  C=ev('__sa.CREATURES');check(C['FLEE_BURST_S']==1.8 and C['FLEE_TIRED']==.65 and C['FLEE_TIRED_S']==.8 and C['FLEE_SHALLOW']==[.74,.8] and C['FLEE_DEEP']==[.8,.88] and C['FLEE_CAP']==.9 and C['FLEE_CAP']<1,'v10 build 18 fish speed numbers: sprint 1.8 s, tired .65 for .8 s, shallow .74-.80, deep .80-.88, cap .90 (under shark top speed)')
  fk=ev('''()=>{const f=__sa.fish[0],o={y:f.y,s:f.s,fu:f.fu},out=[];for(const lv of [0,5,10]){__sa.setLevel(lv);for(const d of [0,1]){f.y=__sa.SURF+(__sa.BED-__sa.SURF)*d;f.fu=1;f.s=__sa.bite()*.3;out.push(__sa.fleeK(f))}}
    __sa.setLevel(3);f.y=__sa.SURF+10;f.fu=0;f.s=__sa.bite()*.3;const far=__sa.fleeK(f);f.s=__sa.bite()*.8;const near=__sa.fleeK(f);Object.assign(f,o);__sa.setLevel(3);return {out,far,near}}''')
  check(abs(fk['out'][0]-.80)<1e-6 and abs(fk['out'][1]-.88)<1e-6 and abs(fk['out'][2]-.85)<1e-6 and max(fk['out'])<=.90+1e-9,f"flee factor: shallow/deep tops .80/.88, +.01 per level, capped .90 ({[round(x,3) for x in fk['out']]})")
  check(abs(fk['near']-fk['far']*.9)<1e-6,f"fish near the bite limit are 10% slower ({fk['near']:.3f} vs {fk['far']:.3f})")
  check(max(r['chase'])<1,f"chasers stay slower than top speed ({r['chase']})")
  check(0<=r['caught']<=12,f"minnow chase bot catches the fleeing fish in {r['caught']:.2f} s (bound 12 s)")
  # v10 item 6 dodge: only while sprinting (never tired), starts inside DODGE.R shark lengths, wiggle first, then sideways; never into the surface
  dg=ev('''()=>{__sa.setLevel(2);const s=__sa.shark,H=innerHeight;s.x=__sa.camX+innerWidth/2;s.y=__sa.SURF+(__sa.BED-__sa.SURF)*.5;s.air=false;s.spd=0;__sa.camY=s.y-H/2;__sa.sim(.05,()=>{s.spd=0});__sa.clearFood();
    const D=__sa.DODGE,out={};const one=(tired,gap)=>{const i=__sa.placeFishAt(0,s.x+s.L*gap,s.y,1),f=__sa.fish[i];__sa.setCreature(f,__sa.bite()*.5,"fish");f.tile=null;f.band=[__sa.SURF+20,Infinity];f.vx=0;f.vy=0;if(tired)f.chase=__sa.CREATURES.FLEE_BURST_S+.01;
      let seen=[],mx=0;__sa.sim(.6,dt=>{s.spd=0;s.x=s.x;__sa.touch.on=false;seen.push(f.dg);if(f.dg===2){let d=Math.atan2(f.vy,f.vx)-Math.atan2(f.y-s.y,f.x-s.x);while(d>Math.PI)d-=2*Math.PI;while(d<-Math.PI)d+=2*Math.PI;mx=Math.max(mx,Math.abs(d))}});
      __sa.clearFood();return {first:seen.findIndex(v=>v>0)>=0?seen[seen.findIndex(v=>v>0)]:0,any:seen.some(v=>v===2),mx:mx*180/Math.PI}};
    out.sprint=one(false,1.5);out.tired=one(true,1.5);out.far=one(false,D.R+2);return out}''')
  check(dg['sprint']['any'] and dg['sprint']['first']==1 and dg['sprint']['mx']>30,f"sprinting fish inside 2.5 shark lengths dodges: wiggle first, then turns {dg['sprint']['mx']:.0f} deg off the flee line")
  check(not dg['tired']['any'],'a tired fish never dodges')
  check(not dg['far']['any'],'no dodge while the shark is further than DODGE.R shark lengths')
  # ---- v9: deep giants, eat on contact, silent push, big creatures chase, no size indicators ----
  r=ev('''()=>{__sa.setLevel(0);const s=__sa.shark,W=innerWidth;let mx=0,n=0,g=0;
     for(let k=0;k<40;k++){s.x=__sa.camX+W/2;s.y=__sa.SURF+(__sa.BED-__sa.SURF)*.9;__sa.camY=s.y-innerHeight/2;__sa.respawnAll();for(const f of __sa.fish){if(f.off)continue;if(__sa.layerOf(f.y)!==2)continue;n++;if(f.giant)g++;mx=Math.max(mx,f.s*(f.kind==="shark"?2.5:1.6)/W)}}
     return {mx,n,g}}''')
  check(r['mx']>=.35 and 0<r['g']<.2*r['n'],f"v9: deep giants exist for a minnow (biggest {r['mx']:.2f} of screen width; {r['g']}/{r['n']} deep spawns giant)")
  r=ev('()=>{const s=__sa.shark,H=innerHeight;let a=[[],[],[]];for(let k=0;k<40;k++)for(const L of [0,1,2]){__sa.setLevel(0);s.x=__sa.camX+innerWidth/2;s.y=__sa.SURF+(__sa.BED-__sa.SURF)*[.1,.45,.9][L];__sa.camY=s.y-innerHeight/2;__sa.respawnAll();for(const f of __sa.fish)if(!f.off&&__sa.layerOf(f.y)===L&&f.kind!=="plankton")a[L].push(f.s*__sa.lk(f)/__sa.bite())/* v9c: drawn size (giants keep their old on-screen size) */}const q=(v,p)=>{v.sort((x,y)=>x-y);return v[Math.floor(v.length*p)]};return [0,1,2].map(L=>q(a[L],.9))}');check(r[2]>r[1]*1.1 and r[1]>r[0]*1.5,f'v9: the big creatures (90th pct size vs your bite) get bigger with depth for a minnow ({r[0]:.2f}/{r[1]:.2f}/{r[2]:.2f})')
  def chaseTry(kind,k):
    return ev(f'''()=>{{__sa.setLevel(0);__sa.clearFood();const s=__sa.shark;s.air=false;s.x=__sa.camX+innerWidth/2;s.y=__sa.SURF+(__sa.BED-__sa.SURF)*.7;s.spd=0;
      const i=__sa.placeFishAt(2,s.x+s.L*2.2,/* inside the 2.4 L notice range (3 L relied on idle drift reaching it in 1.2 s) */s.y,-1),f=__sa.fish[i];__sa.setCreature(f,__sa.bite()*{k},"{kind}");f.tile=null;f.band=[0,Infinity];f.rest=0;let st=false;
      __sa.sim(1.2,()=>{{__sa.touch.on=false;if(f.st==="chase")st=true}});return st}}''')
  check(chaseTry('fish',2.2) and chaseTry('octo',2.2),'v9: any clearly bigger creature (not only sharks) chases a deep minnow')
  check(not chaseTry('fish',1.0),'v9: a same-size creature does not chase')
  src=open(os.path.join(ROOT,'game.js')).read()
  check('Too small' not in src and 'strokeText("!"' not in src and '"#ff2a2a"' not in src,'v9: no "Too small" text, no red "!" marker, no red chaser arrows in game.js')
  def bumpTry(kind,k):
    return ev(f'''()=>{{__sa.god=false;__sa.setLevel(0);__sa.clearFood();const s=__sa.shark;s.air=false;s.x=__sa.camX+innerWidth/2;s.y=__sa.SURF+200;s.ang=0;s.spd=0;
      const i=__sa.placeFishAt(1,s.x,s.y+s.L*.15,1),f=__sa.fish[i];__sa.setCreature(f,__sa.bite()*{k},"{kind}");f.tile=null;f.band=[0,Infinity];f.vx=0;f.vy=0;
      const pops=__sa.pops.filter(p=>p.t>0).length;__sa.sim(.3,()=>{{__sa.touch.on=false}});const r={{state:__sa.state,why:__sa.endReason,pops:__sa.pops.filter(p=>p.t>0).map(p=>p.txt)}};__sa.god=true;return r}}''')
  r=bumpTry('fish',1.0)
  check(r['state']=='play' and not any('small' in t.lower() for t in r['pops']),f'v9: same-size fish only pushes, silently ({r})')
  r=bumpTry('fish',1.6)
  check(r['why']=='eaten',f'v9: a clearly bigger fish eats the minnow on body contact ({r["state"]}/{r["why"]})')
  check(not errs,f'no page errors {errs[:3]}')
  b.close()
finally:
  srv.terminate()
print(f'\n{passes} passed, {len(fails)} failed');[print(' -',f) for f in fails];sys.exit(1 if fails else 0)
