# b52 tests (Jeremy t1339u + t1343u, via Eve): infinite growth, surfers -> sail boats -> cargo ships, depth bands empty of fish as you grow,
# a boost that really is fast, a 3D-looking turn (no instant mirror), no divers, bonus points for surface prey.
# Run: /workspace/.pwvenv/bin/python tests/test_b52.py (port 8905, override with SA_PORT52). Pretend phone (Chromium touch emulation), never a real phone.
import os,sys,subprocess,time,json,re
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT52','8905'));URL=f'http://127.0.0.1:{PORT}/'
passes=0;fails=[]
def check(c,m):
  global passes
  if c: passes+=1;print('PASS',m)
  else: fails.append(m);print('FAIL',m)
def rd(p):return open(os.path.join(ROOT,p),encoding='utf8').read()
# --- static checks ---
check(json.load(open(os.path.join(ROOT,'version.json'))).get('build')=='52','version.json build 52')
ih=rd('index.html');check('game.js?v=52' in ih and re.search(r'content="52"',ih) is not None,'index.html meta build 52 and game.js?v=52')
check('sharkattack-v' in rd('sw.js'),'sw.js cache prefix kept (sharkattack-v + build)')
gj=rd('game.js');check(all('b52' in l for l in gj.split('\n') if re.search(r'diver',l,re.I)),'game.js: "diver" only in the b52 removal note')
for f in ('index.html','README.md'): check(re.search(r'divers?\b',rd(f),re.I) is None or f=='README.md' and 'No divers' in rd(f),f'{f}: no divers (README only says they were removed)')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
class Bad:
  "result of a page call that threw (e.g. a b52 hook missing on b51): every comparison is False, so the check FAILs instead of crashing"
  def __getitem__(s,k):return s
  def __lt__(s,o):return False
  __gt__=__le__=__ge__=__lt__
  def __eq__(s,o):return False
  def __bool__(s):return False
  def __contains__(s,o):return False
  def __iter__(s):return iter(())
  def __len__(s):return 0
  def __format__(s,f):return 'ERR'
  def __mul__(s,o):return s
  __rmul__=__add__=__sub__=__rsub__=__truediv__=__mul__
  def __float__(s):return float('nan')
def J(pg,e):
  try:return pg.evaluate(e)
  except Exception as ex:print('page call failed:',str(ex).split('\n')[0]);return Bad()
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
  cx=b.new_context(viewport={'width':844,'height':390},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block')
  pg=cx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(URL);pg.wait_for_timeout(500);pg.touchscreen.tap(422,195);pg.wait_for_timeout(300)
  J(pg,'__sa.startAs("white","endless");__sa.god=true');pg.wait_for_timeout(300)
  # 6 no divers
  check(J(pg,'!("divers" in __sa)&&!("spawnDiver" in __sa)&&!("DIV" in __sa)&&!("netHit" in __sa)'),'no diver / net hooks exist in the game')
  r=J(pg,'(()=>{for(let i=0;i<12;i++)__sa.surferCaught();__sa.sim(20);return {st:__sa.state,why:__sa.endReason}})()')
  check(r['st']=='play','12 surfers caught, 20 s later still playing, never "Caught!" '+str(r))
  # 1 infinite growth
  check(J(pg,'__sa.MAX_LEVEL')==None or J(pg,'__sa.MAX_LEVEL===Infinity'),'MAX_LEVEL is Infinity (no size cap)')
  r=J(pg,'(()=>{__sa.setLevel(30);const l0=__sa.shark.lvl;for(let i=0;i<200;i++)__sa.feed(50);return {l0,l1:__sa.shark.lvl}})()')
  check(r['l1']>r['l0'],f'feeding past old cap keeps growing (size {r["l0"]+1} -> {r["l1"]+1})')
  for L in (100,1000,5000):
    r=J(pg,f'''(()=>{{__sa.setLevel({L});__sa.respawnAll(true);__sa.sim(3);const s=__sa.shark,ok=v=>Number.isFinite(v);return {{k:__sa.worldK,fin:ok(s.x)&&ok(s.y)&&ok(s.spd)&&ok(s.L)&&__sa.fish.every(f=>ok(f.s)&&ok(f.x)&&ok(f.y)),st:__sa.state}}}})()''')
    check(r['fin'] and r['k']>0 and r['k']<1e-3 and r['st']=='play',f'size {L+1}: no NaN/Infinity, world scale {r["k"]:.3g} > 0, still playing')
  pg.wait_for_timeout(200)
  # 2+7 prey chain and points
  r=J(pg,'''(()=>{const out={};for(const L of [6,12,17]){__sa.setLevel(L);const ks=new Set();for(let i=0;i<300;i++){const s=__sa.surf[0];__sa.spawnSurf(s,true);ks.add(s.k)}out[L]=[...ks].sort()}return out})()''')
  check(r['6']==[0,1],f'size 7: surfers only {r["6"]}')
  check(2 in r['12'] and 3 not in r['12'],f'size 13: sail boats appear, no cargo yet {r["12"]}')
  check(3 in r['17'] and 2 in r['17'],f'size 18: cargo ships appear (with sail boats) {r["17"]}')
  P=(list(J(pg,'__sa.SURFERS.map(s=>s.pts)') or [])+[0,0,0,0])[:4] if len(J(pg,'__sa.SURFERS'))>=4 else [0,0,0,0];fishMax=J(pg,'(()=>{const f={kind:"fish",s:__sa.bite()*1.0};return __sa.ptsOf(f)})()')
  check(P[3]>P[2]>max(P[0],P[1]) and min(P[0],P[1])>=3*fishMax,f'points cargo {P[3]} > sail {P[2]} > surfer {P[0]}/{P[1]} >= 3x a bite-size fish ({fishMax})')
  # physical surface bite on a cargo ship
  r=J(pg,'''(()=>{__sa.setLevel(18);__sa.respawnAll(true);const s=__sa.shark;s.air=false;s.ang=0;s.spd=0;s.y=__sa.SURF+s.L*.12;__sa.surf.forEach(q=>q.zip=999);__sa.placeSurfer(0,s.x+s.L*.3,3);const sc=__sa.score,n=__sa.surfEaten[3];__sa.sim(.2);const p=__sa.pops.find(p=>p.t>0&&p.big);return {d:__sa.surfEaten[3]-n,ds:__sa.score-sc,pop:p?p.txt:null}})()''')
  check(r['d']==1 and r['ds']>=P[3],f'cargo ship bitten at the surface: eaten, score +{r["ds"]}, big pop {r["pop"]!r}')
  # 3 depth bands
  def band(L,dep):
    return J(pg,f'''(()=>{{__sa.setLevel({L});const s=__sa.shark;s.y=__sa.SURF+(__sa.BED-__sa.SURF)*{dep};s.spd=0;__sa.respawnAll(true);__sa.sim(3);const live=__sa.fish.filter(f=>!f.off&&!(f.fade>0));return {{min:Math.min(...live.map(f=>__sa.depthRaw(f.y))),n:live.length,near:live.filter(f=>Math.abs(f.y-s.y)<innerHeight*1.5&&Math.abs(f.x-s.x)<innerWidth*1.5).length}}}})()''')
  r=band(0,.15);check(r['min']<.3 and r['near']>0,f'size 1: shallow water has fish (min depth {r["min"]:.2f}, {r["near"]} near)')
  for L,edge in ((9,.3),(13,.62),(17,1.0),(22,1.6)):
    r=band(L,edge+.25);check(r['min']>=edge-1e-6,f'size {L+1}: no live fish above depth {edge} (shallowest {r["min"]:.2f})')
    check(r['near']>0,f'size {L+1}: shark just below that depth still finds fish ({r["near"]} near) - no soft lock')
  r=band(400,2.2);check(r['near']>0,f'size 401: deepest band still has fish ({r["near"]} near)')
  # 4 boost
  r=J(pg,'''(()=>{__sa.setLevel(3);const s=__sa.shark;s.air=false;s.y=__sa.SURF+(__sa.BED-__sa.SURF)*.5;s.ang=0;Object.assign(__sa.touch,{on:true,dir:0,drive:1,lastMove:performance.now()+9e9});__sa.boost.t=0;__sa.boost.cd=0;__sa.sim(3);const m=__sa.maxSpeed(),v0=s.spd/m;__sa.doBoost();__sa.sim(.6);const v1=s.spd/m;__sa.sim(1.6);const v2=s.spd/m;return {v0,v1,v2,cd:__sa.boost.cd,fl:__sa.CREATURES.FLEE_CAP}})()''')
  check(r['v1']>=2*r['v0'] and r['v1']>=1.9,f'boost: {r["v0"]:.2f} -> {r["v1"]:.2f} of top speed (>= 2x)')
  check(r['v1']>r['fl']*2,f'boost is far faster than the fastest fleeing fish ({r["fl"]} of top speed)')
  check(r['v2']<1.3 and r['cd']>0,f'boost is a burst: back to {r["v2"]:.2f} after it ends, recharging {r["cd"]:.2f}s')
  J(pg,'Object.assign(__sa.touch,{on:false})')
  # 5 turn (real frames)
  r=J(pg,'''new Promise(res=>{__sa.setLevel(2);const s=__sa.shark;s.air=false;s.y=__sa.SURF+(__sa.BED-__sa.SURF)*.4;s.ang=0;s.spd=__sa.maxSpeed()*.5;Object.assign(__sa.touch,{on:true,dir:0,drive:.5,lastMove:performance.now()+9e9});
   setTimeout(()=>{__sa.touch.dir=Math.PI;const out=[],t0=performance.now();const f=()=>{const q=window.__saTurn;out.push([performance.now()-t0,q?q.cF:null,q?q.head:null]);if(performance.now()-t0<1300)requestAnimationFrame(f);else res(out)};requestAnimationFrame(f)},700)})''')
  cf=[x[1] for x in r]
  check(len(cf)>0 and all(c is not None for c in cf),'turn state exposed every frame')
  if len(cf)>0 and all(c is not None for c in cf):
    jumps=max(abs(cf[i+1]-cf[i]) for i in range(len(cf)-1));t_a=next((x[0] for x in r if x[1]<.95),None);t_b=next((x[0] for x in r if x[1]<-.95),None)
    check(jumps<.45,f'no instant mirror: biggest per-frame change in facing {jumps:.2f} (a flip would be 2.0)')
    check(any(abs(c)<.25 for c in cf),'shark passes through a side-on/head-on midpoint')
    check(t_a is not None and t_b is not None and .4<=(t_b-t_a)/1000<=.85,f'turn takes {((t_b or 0)-(t_a or 0))/1000:.2f} s (target .5-.8)')
    check(max(x[2] for x in r)>.5,'head-on view shows at the midpoint')
  check(not errs,f'no page errors {errs[:2]}')
  b.close()
finally:
  srv.terminate()
print(f'\n{passes} passed, {len(fails)} failed')
for f in fails: print(' FAIL:',f)
sys.exit(1 if fails else 0)
