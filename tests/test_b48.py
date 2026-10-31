# b48 tests: endless world (no floor picture, no vents, no seabed starfish; the shark swims down forever) and growth shown relatively
# (the shark stays the same size on screen, the world and the other creatures shrink around it). Intro/bite/sound untouched (see b46/b47).
# Run: /workspace/.pwvenv/bin/python tests/test_b48.py  (port 8900). Screenshots -> art-shots-b48/ (not committed).
import os,sys,subprocess,time
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT48','8900'));URL=f'http://127.0.0.1:{PORT}/'
SHOTS=os.path.join(ROOT,'art-shots-b48');os.makedirs(SHOTS,exist_ok=True);passes=0;fails=[]
def check(c,m):
  global passes
  if c: passes+=1;print('PASS',m)
  else: fails.append(m);print('FAIL',m)
html=open(os.path.join(ROOT,'index.html')).read();sw=open(os.path.join(ROOT,'sw.js')).read();js=open(os.path.join(ROOT,'game.js')).read()
check('"build":"48"' in open(os.path.join(ROOT,'version.json')).read() and 'content="48"' in html and 'game.js?v=48' in html and 'game.js?v=48' in sw,'build 48 in version.json, index.html and sw.js')
check('floorSpr' not in js.replace('floorSpr=null','') and 'ventSpr' not in js.replace('ventSpr=null',''),'no floor sprite or vent glow is built or drawn')
check('Slimetrail Productions. No ads, no tracking, works offline.' in html and 'jeremy' not in html.lower() and 'jeremy' not in sw.lower() and 'jeremy' not in open(os.path.join(ROOT,'manifest.webmanifest')).read().lower(),'credits: Slimetrail Productions line, no personal name in index.html, sw.js or manifest')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');pg=cx.new_page()
  errs=[];out=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
  pg.on('request',lambda r:out.append(r.url) if not r.url.startswith(URL) else None);ev=pg.evaluate
  pg.goto(URL);pg.wait_for_timeout(300);pg.click('#tap');pg.wait_for_timeout(800);pg.tap('#start');pg.wait_for_timeout(300);pg.click('.pick[data-type=white]');pg.wait_for_timeout(500)
  check(ev('__sa.state')=='play','play starts');ev('__sa.god=true');ev('__sa.timeLeft=999')
  # relative growth
  r=ev('''()=>{const o=[];for(const l of [0,3,6,9]){__sa.setLevel(l);__sa.sim(.5);o.push({l,L:__sa.shark.L,k:__sa.worldK,tg:__sa.trueGrow(l)})}return o}''')
  check(all(abs(x['L']/r[0]['L']-1)<.005 for x in r),f"shark drawn the same size at stages 0/3/6/9 ({[round(x['L'],1) for x in r]} px)")
  check(all(abs(x['k']*x['tg']-1)<.01 for x in r) and all(r[i+1]['k']<r[i]['k'] for i in range(3)),f"world scale = 1/true size and shrinks each stage ({[round(x['k'],2) for x in r]})")
  q=ev('''()=>{__sa.setLevel(0);const f=__sa.fish[5];__sa.setCreature(f,__sa.bite()*.6,"fish");const s0=f.s,L0=__sa.shark.L;__sa.setLevel(4);return {r:f.s/s0,k:__sa.wK(4)/__sa.wK(0),L:__sa.shark.L/L0}}''')
  check(abs(q['r']-q['k'])<.01 and q['r']<1 and abs(q['L']-1)<.005,f"other creatures shrink on screen by the world factor x{q['r']:.3f} while the shark stays x{q['L']:.3f}")
  for l,name in [(0,'stage0'),(8,'stage8')]:
    ev(f'()=>{{__sa.setLevel({l});const s=__sa.shark;s.y=__sa.SURF+innerHeight*.5;s.x=__sa.camX+innerWidth/2;__sa.camY=s.y-innerHeight/2;__sa.respawnAll&&__sa.respawnAll()}}');pg.wait_for_timeout(900);pg.screenshot(path=f'{SHOTS}/size-{name}.png')
  # endless down: swim far below the old floor, camera follows, no floor drawn, deep creatures still spawn
  ev('__sa.setLevel(9)')
  for fr,name in [(.98,'old-floor-depth'),(2.5,'below-old-floor'),(6,'far-below')]:
    d=ev(f'''()=>{{const s=__sa.shark;s.y=__sa.SURF+(__sa.BED-__sa.SURF)*{fr};s.x=__sa.camX+innerWidth/2;s.spd=0;__sa.touch.on=false;__sa.camY=s.y-innerHeight/2;for(const f of __sa.fish)__sa.spawnFish(f,false);return 1}}''')
    pg.wait_for_timeout(1200)
    st=ev('({sy:__sa.shark.y,cy:__sa.camY,state:__sa.state,n:__sa.fish.filter(f=>!f.off&&Math.abs(f.y-__sa.shark.y)<innerHeight*1.5).length,star:__sa.fish.filter(f=>!f.off&&f.kind==="star").length})')
    check(st['state']=='play' and 0<st['sy']-st['cy']<412,f"{name}: shark on screen at depth {fr} x old floor depth (camera follows)")
    check(st['n']>=5 and st['star']==0,f"{name}: creatures still around ({st['n']}), no seabed starfish")
    pg.screenshot(path=f'{SHOTS}/{name}.png')
  # swim straight down with the finger for 6 s from below the old floor: depth keeps increasing (no wall)
  y0=ev('__sa.shark.y');ev('()=>{Object.assign(__sa.touch,{on:true,dir:Math.PI/2,drive:1,lastMove:performance.now()+9e9})}');pg.wait_for_timeout(6000);y1=ev('__sa.shark.y');ev('__sa.touch.on=false')
  check(y1>y0+100,f'swimming down below the old floor keeps going ({y0:.0f} -> {y1:.0f})')
  # no floor band drawn: rows at and below the old floor are plain dark water (low spread of colour across the row)
  sp=ev('''()=>{const c=document.getElementById("c"),g=c.getContext("2d");__sa.camY=__sa.BED-innerHeight*.5;__sa.drawWater(1);const im=g.getImageData(0,0,c.width,c.height).data,res=[];
    for(const fy of [.55,.7,.85]){const y=Math.floor(c.height*fy);let mn=1e9,mx=-1;for(let x=0;x<c.width;x+=8){const i=(y*c.width+x)*4,l=.3*im[i]+.59*im[i+1]+.11*im[i+2];mn=Math.min(mn,l);mx=Math.max(mx,l)}res.push(mx-mn)}return res}''')
  check(max(sp)<60,f'no rocky floor drawn where the seabed was (row brightness spread {[round(x) for x in sp]})')
  ft=ev('()=>new Promise(r=>{const a=[];let l=performance.now();const f=n=>{a.push(n-l);l=n;if(a.length<90)requestAnimationFrame(f);else r(a)};requestAnimationFrame(f)})');ft.sort()
  check(ft[int(len(ft)*.9)]<40,f'deep play frames p90 {ft[int(len(ft)*.9)]:.1f} ms (<40)')
  check(not errs,f'no console errors {errs[:3]}');check(not out,f'no outside requests {out[:3]}')
  cx.close();b.close()
finally: srv.terminate()
print(f'\n{passes} passed, {len(fails)} failed');sys.exit(1 if fails else 0)
