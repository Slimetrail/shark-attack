# b53 tests (Skeptic FIX on b52 via Eve): B13 blocked storage still starts; B9 late game always has visible prey; B5 turn reads 3D;
# test gaps: cargo 100, surfer shrink floor, no divers, title re-layout on resize.
# Run: /workspace/.pwvenv/bin/python tests/test_b53.py (port 8953, override SA_PORT53). Pretend phone (Chromium touch emulation), never a real phone.
import os,sys,subprocess,time,json,re
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('SA_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT53','8953'));URL=f'http://127.0.0.1:{PORT}/'
ONLY=os.environ.get('SA_ONLY','')
passes=0;fails=[]
def check(c,m):
  global passes
  if c: passes+=1;print('PASS',m)
  else: fails.append(m);print('FAIL',m)
def rd(p):return open(os.path.join(ROOT,p),encoding='utf8').read()
check(json.load(open(os.path.join(ROOT,'version.json'))).get('build')=='53','version.json build 53')
ih=rd('index.html');check('game.js?v=53' in ih and 'content="53"' in ih and 'game.js?v=53' in rd('sw.js'),'index.html meta 53, game.js?v=53, sw.js shell game.js?v=53 (cache sharkattack-v53)')
check('A Slimetrail production' in ih and 'No ads, no tracking, works offline.' in ih,'credit line and "No ads, no tracking, works offline." kept')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
def J(pg,e):
  try:return pg.evaluate(e)
  except Exception as ex:print('page call failed:',str(ex).split('\n')[0]);return None
BLOCK='''Object.defineProperty(window,"localStorage",{configurable:true,get(){throw new DOMException("The operation is insecure.","SecurityError")}});'''
def newpg(b,w=844,h=390,block=False):
  cx=b.new_context(viewport={'width':w,'height':h},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block')
  if block: cx.add_init_script(BLOCK)
  pg=cx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(URL);pg.wait_for_timeout(600);return cx,pg,errs
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
  # ---- B13 blocked storage ----
  if not ONLY or 'store' in ONLY:
   cx,pg,errs=newpg(b,block=True)
   check(J(pg,'typeof window.__sa==="object"&&__sa.state') in ('tap','title') if J(pg,'typeof window.__sa')=='object' else False,f'storage blocked: game loads to the title (errors {errs[:1]})')
   check(J(pg,'(()=>{try{localStorage;return false}catch(e){return true}})()')==True,'storage really is blocked in this page (throws)')
   pg.touchscreen.tap(422,195);pg.wait_for_timeout(5000)
   bb=pg.locator('#snd').bounding_box() if J(pg,'typeof __sa')=='object' else None;bb=bb or {'x':0,'y':0,'width':1,'height':1};a0=J(pg,'__sa.soundOn');pg.touchscreen.tap(bb['x']+bb['width']/2,bb['y']+bb['height']/2);pg.wait_for_timeout(200)
   r=J(pg,'(()=>{const a='+str(a0).lower()+';const b=__sa.soundOn;return {a,b,mem:__saLS.mem(),lbl:document.getElementById("snd").textContent,st:__sa.state}})()')
   check(r and r['a']!=r['b'] and r['mem'],f'storage blocked: sound toggle works on the title, settings in memory {r}')
   st=J(pg,'(()=>{__sa.startAs("white","timed");return __sa.state})()');check(st=='play',f'storage blocked: a run starts ({st})')
   r=J(pg,'(()=>{__sa.god=true;for(let i=0;i<5;i++){__sa.placeFishAtMouth(0);__sa.sim(.25)}const sc=__sa.score;__sa.timeLeft=0;__sa.sim(.2);return {sc,st:__sa.state,best:__sa.best}})()')
   check(r and r['st']!='play' and r['best']>=r['sc']>0,f'storage blocked: round ends, best score kept in memory {r}')
   r=J(pg,'(()=>{__sa.setMode("endless");return __sa.mode})()');check(r=='endless',f'storage blocked: mode setting works ({r})')
   check(not errs,f'storage blocked: no page errors {errs[:2]}')
   cx.close()
  # ---- B9 late game: always something visible to chase ----
  if not ONLY or 'late' in ONLY:
   cx,pg,errs=newpg(b);pg.touchscreen.tap(422,195);pg.wait_for_timeout(300);J(pg,'__sa.startAs("white","endless");__sa.god=true')
   SAMPLE='''(()=>{const s=__sa.shark,W=innerWidth,H=innerHeight,cx=__sa.camX,cy=__sa.camY,L=s.L;
     const fish=__sa.fish.filter(f=>!f.off&&!(f.fade>0)&&f.kind!=="plankton"&&__sa.rel(f)<0&&Math.abs(f.x-s.x)<W*.75&&Math.abs(f.y-s.y)<H*.75)/* reachable: within 0.75 screen of the shark */.map(f=>(__sa.fpx?__sa.fpx(f):f.s*1.25)*(f.kind==="shark"?2.5:1));/* drawn length; small sharks draw 2.5x */
     const sk=q=>__sa.surfDrawK?__sa.surfDrawK(q):Math.max(__sa.SURFACE.MINK,Math.min(1.8,__sa.worldK));
     const surf=__sa.surf.filter(q=>!(q.zip>0)&&q.x>cx-20&&q.x<cx+W+20&&__sa.SURF>cy&&__sa.SURF<cy+H).map(q=>({k:q.k,len:2*(__sa.SURFERS[q.k].hw||18)*sk(q)}));return {L,fish,surf}})()'''
   def place(L,where):
     return J(pg,f'''(()=>{{__sa.setLevel({L});const s=__sa.shark;s.air=false;s.ang=0;s.spd=0;let dep=.08;if("{where}"==="deep"){{const V=__sa.VANISH;dep=2.2;for(let i=0;i<V.EDGES.length;i++)if(s.lvl<V.LVL[i]){{dep=(i?V.EDGES[i-1]:0)+.12;break}}}}
       s.y=__sa.SURF+(__sa.BED-__sa.SURF)*dep;__sa.respawnAll();__sa.surf.forEach(q=>__sa.spawnSurf(q,false));__sa.sim(2);return dep}})()''')
   for L in (18,24,49,79,199):
     ns=[];mins=[];big=[]
     for k in range(6):
       place(L,'surf');r=J(pg,SAMPLE)
       if not r: continue
       ns.append(len(r['surf']));mins+= [q['len'] for q in r['surf']];big+=[q['len']/r['L'] for q in r['surf'] if q['k']>=2]
     mean=sum(ns)/max(1,len(ns))
     check(mean>=2 and min(ns or [0])>=1,f'size {L+1} at the surface: on screen {ns} surface prey (target mean >= 2, never 0)')
     check(bool(big) and min(big)>=.5,f'size {L+1}: every sail boat / cargo ship drawn >= 0.5 x shark length (min {min(big or [0]):.2f} x, {min(mins or [0]):.0f} px)')
   for L in (18,24,49,79,199):
     ns=[];sz=[]
     for k in range(6):
       place(L,'deep');r=J(pg,SAMPLE)
       if not r: continue
       ns.append(len(r['fish']));sz+=r['fish']
     check(sum(ns)/max(1,len(ns))>=2 and min(ns or [0])>=1,f'size {L+1} in the shallowest band that still has fish: food fish within 0.75 screen of the shark {ns} (target mean >= 2, never 0)')
     check(bool(sz) and min(sz)>=18,f'size {L+1}: food fish drawn >= 18 px (min {min(sz or [0]):.1f})')
   LUM='''((boxes)=>{const c=document.getElementById("c"),g=c.getContext("2d"),k=c.width/innerWidth;const lum=(x,y,w,h)=>{x=Math.max(0,Math.round(x*k));y=Math.max(0,Math.round(y*k));w=Math.max(1,Math.round(w*k));h=Math.max(1,Math.round(h*k));const d=g.getImageData(x,y,w,h).data;let s=0;const a=[];for(let i=0;i<d.length;i+=4){const v=.2126*d[i]+.7152*d[i+1]+.0722*d[i+2];a.push(v);s+=v}return {m:s/a.length,a}};
     return boxes.map(b=>lum(b[0],b[1],b[2],b[3]))})'''
   CON='''new Promise(res=>{const c=document.getElementById("c"),g=c.getContext("2d"),k=c.width/innerWidth,raf=()=>new Promise(r=>requestAnimationFrame(()=>r()));
     const rd=(x,y,w,h)=>{x=Math.max(0,Math.round(x*k));y=Math.max(0,Math.round(y*k));w=Math.max(1,Math.round(w*k));h=Math.max(1,Math.round(h*k));const d=g.getImageData(x,y,w,h).data,a=[];for(let i=0;i<d.length;i+=4)a.push(.2126*d[i]+.7152*d[i+1]+.0722*d[i+2]);return a};
     (async()=>{await raf();const cx=__sa.camX,cy=__sa.camY,W=innerWidth,H=innerHeight,fp=f=>(__sa.fpx?__sa.fpx(f):f.s*1.25)*(f.kind==="shark"?2.5:1);
      const F=__sa.fish.filter(f=>!f.off&&!(f.fade>0)&&f.kind!=="plankton"&&__sa.rel(f)<0&&f.x>cx+30&&f.x<cx+W-30&&f.y>cy+60&&f.y<cy+H-30&&Math.hypot(f.x-__sa.shark.x,f.y-__sa.shark.y)>__sa.shark.L*.7);
      const B=F.map(f=>{const w=fp(f)*.6;return [f.x-cx-w/2,f.y-cy-w/4,w,w/2]});const A=B.map(b=>rd(...b));F.forEach(f=>{f.off=true});await raf();await raf();
      const Z=B.map(b=>rd(...b)),bg=rd(200,120,440,200);const bgm=bg.reduce((s,v)=>s+v,0)/bg.length;
      const p90=B.map((b,i)=>{const d=A[i].map((v,j)=>Math.abs(v-Z[i][j])).sort((x,y)=>x-y);return d[Math.floor(d.length*.9)]||0});res({bgm,p90,n:B.length})})()})'''
   for L in (18,24):
    r=None
    for tries in range(5):
     place(L,'deep');pg.wait_for_timeout(100);r=J(pg,CON)
     if r and r['n']>0: break
    bgm=r['bgm'] if r else 0;p90=r['p90'] if r else []
    check(bgm>=24,f'size {L+1} deep water background luma {bgm:.1f} (target >= 24 of 255)')
    check(bool(p90) and sum(p90)/len(p90)>=25,f'size {L+1} deep: fish stand out from the water, 90th-percentile pixel difference fish vs no fish {[round(d) for d in p90]} (target mean >= 25 luma)')
   check(not errs,f'late game: no page errors {errs[:2]}');cx.close()
  # ---- test gaps: points, surfer shrink (no floor), no divers ----
  if not ONLY or 'gaps' in ONLY:
   cx,pg,errs=newpg(b);pg.touchscreen.tap(422,195);pg.wait_for_timeout(300);J(pg,'__sa.startAs("white","endless");__sa.god=true')
   P=J(pg,'__sa.SURFERS.map(s=>s.pts)');check(P==[15,20,40,100],f'points exactly surfer 15/20, sail boat 40, cargo ship 100 {P}')
   r=J(pg,'''(()=>{__sa.setLevel(18);__sa.respawnAll(true);const s=__sa.shark;s.air=false;s.ang=0;s.spd=0;s.y=__sa.SURF+s.L*.12;__sa.surf.forEach(q=>q.zip=999);__sa.placeSurfer(0,s.x+s.L*.3,3);const sc=__sa.score;__sa.sim(.2);return __sa.score-sc})()''')
   check(r==100,f'eating a cargo ship adds exactly +100 ({r})')
   r=J(pg,'''(()=>{const o={};for(const L of [0,6,12,18,24]){__sa.setLevel(L);o[L+1]=__sa.surfDrawK({k:0})}return o})()''')
   wk=J(pg,'(__sa.setLevel(18),__sa.worldK)')
   check(bool(r) and r['13']<.55 and r['19']<r['13'] and r['25']<r['19'] and abs(r['19']-(wk or 0))<1e-9,f'surfers keep shrinking with the world, no 0.55 floor (draw scale by size {r})')
   src=rd('game.js')
   for w in ('drawDiver','spawnDiver','netHit','Divers!'):
     check(w not in src,f'game.js has no {w}')
   check(not errs,f'gaps: no page errors {errs[:2]}');cx.close()
  # ---- B5 3D turn ----
  if not ONLY or 'turn' in ONLY:
   cx,pg,errs=newpg(b);pg.touchscreen.tap(422,195);pg.wait_for_timeout(300);J(pg,'__sa.startAs("white","endless");__sa.god=true;__sa.setLevel(3);__sa.clearFood()')
   T=J(pg,'__sa.TURN3D');check(bool(T) and T['SEC']<=.8,f'turn lasts <= 0.8 s ({T and T["SEC"]})')
   out={}
   for deg,tdeg in ((40,15),(90,50),(130,95)):
     J(pg,f'window.__saYawHold=[{deg}*Math.PI/180,{tdeg}*Math.PI/180]');pg.wait_for_timeout(150);out[deg]=J(pg,'Object.assign({},window.__saTurn)')
   J(pg,'window.__saYawHold=null')
   check(all(out[d] and (out[d].get('slices') or 0)>=8 for d in out),f'mid-turn the body is drawn as >= 8 bending spine slices, not one squashed picture {[(d,(out[d] or {}).get("slices")) for d in out]}')
   check(bool(out[90]) and out[90]['head']>.5,f'head-on view at the head mid-turn ({out[90] and out[90]["head"]})')
   check(not errs,f'turn: no page errors {errs[:2]}');cx.close()
  b.close()
finally:
  srv.terminate()
print(f'\n{passes} passed, {len(fails)} failed')
for f in fails: print(' FAIL:',f)
sys.exit(1 if fails else 0)
