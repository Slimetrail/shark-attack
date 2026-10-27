# v6 tests: landscape, deep world with camera, depth zones, volcanic floor, flee/chase creatures, slowed growth, face-on intro shark.
# Run: python3 tests/test_v6.py   (port 8883, headless Chromium, landscape phone sizes)
import os,sys,json,subprocess,time,math
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT7','8883'))
URL=f'http://127.0.0.1:{PORT}/';SHOTS=os.environ.get('SA_SHOTS','/workspace/shark-shots')
os.makedirs(SHOTS,exist_ok=True);passes=0;fails=[]
def check(c,m):
  global passes
  if c: passes+=1;print('PASS',m)
  else: fails.append(m);print('FAIL',m)
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  man=json.load(open(os.path.join(ROOT,'manifest.webmanifest')));check(man['orientation']=='landscape','manifest orientation landscape')
  sw=open(os.path.join(ROOT,'sw.js')).read();check('VER="6"' in sw and 'game.js?v=6' in sw,'service worker cache bumped to v6')
  check('game.js?v=6' in open(os.path.join(ROOT,'index.html')).read(),'index loads game.js?v=6')
  for w,h in [(915,412),(844,390)]:
    cx=b.new_context(viewport={'width':w,'height':h},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');pg=cx.new_page();errs=[];outside=[]
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    pg.on('request',lambda r:outside.append(r.url) if not r.url.startswith(URL) else None)
    ev=pg.evaluate;tag=f'{w}x{h}'
    pg.goto(URL);pg.wait_for_timeout(300);check(not pg.is_visible('#rot'),f'{tag}: no rotate prompt in landscape');pg.click('#tap')
    pg.wait_for_function('__sa.titleT>0.95',timeout=5000);pg.wait_for_timeout(150)
    if w==915: pg.screenshot(path=f'{SHOTS}/v6-title-open-mouth.png')
    pg.wait_for_function('window.__saTitleDone===true',timeout=8000)
    if w==915: pg.screenshot(path=f'{SHOTS}/v6-title-bitten.png')
    check(pg.is_visible('#start') and pg.locator('#start').bounding_box()['y']+pg.locator('#start').bounding_box()['height']<=h,f'{tag}: start button on screen')
    pg.click('#start');pg.wait_for_timeout(250)
    boxes=[pg.locator('.pick').nth(i).bounding_box() for i in range(3)]
    check(all(bb['y']+bb['height']<=h and bb['x']+bb['width']<=w for bb in boxes) and abs(boxes[0]['y']-boxes[2]['y'])<5,f'{tag}: pick cards side by side and fully on screen')
    if w==915: pg.screenshot(path=f'{SHOTS}/v6-pick.png')
    pg.click('.pick[data-type=white]');pg.wait_for_timeout(400);check(ev('__sa.state')=='play',f'{tag}: play starts');ev('__sa.god=true')
    check(abs(ev('__sa.WORLD_H')-h*5)<2 and ev('__sa.BED')>h*4,f'{tag}: world is 5 screens tall, floor far below')
    ev('__sa.timeLeft=999')
    if w==915: pg.screenshot(path=f'{SHOTS}/v6-shallow.png')
    # camera follows the shark down
    for frac,name in [(.45,'mid'),(.75,'deep'),(.985,'floor')]:
      ev(f'()=>{{const s=__sa.shark;s.y=__sa.SURF+(__sa.BED-__sa.SURF)*{frac};s.x=innerWidth/2;s.spd=0;__sa.touch.on=false;for(const f of __sa.fish)__sa.spawnFish(f,false)}}');pg.wait_for_timeout(1500)
      cy=ev('__sa.camY');sy=ev('__sa.shark.y')
      check(sy-cy>0 and sy-cy<h,f'{tag}: camera follows the shark to {name} depth (shark on screen at {sy-cy:.0f}px)')
      if w==915: pg.screenshot(path=f'{SHOTS}/v6-{name}.png')
    fl=ev('()=>{const k={};for(const f of __sa.fish)k[f.kind]=(k[f.kind]||0)+1;return k}');big=ev('Math.max(...__sa.fish.filter(f=>f.kind==="shark").map(f=>f.s),0)')
    check(fl.get('glow',0)>=3,f'{tag}: glowing fish down at the volcanic floor {fl}')
    ev('__sa.timeLeft=999')
    # sizes deeper are larger: sample spawns
    sz=ev('()=>{const f={};const r=d=>{let m=0,n=0,k=0;for(let i=0;i<400;i++){__sa.shark.y=__sa.SURF+(__sa.BED-__sa.SURF)*d;__sa.spawnFish(f,false);if(f.kind==="shark"){m+=f.s;n++}k+=f.kind==="shark"}return [n?m/n:0,k/400]};const a=r(.05),c=r(.9);__sa.shark.y=__sa.SURF+innerHeight*.45;return [a,c]}')
    check(sz[1][0]>sz[0][0]*1.5 and sz[1][1]>sz[0][1]*2,f'{tag}: sharks bigger and more common deep down (shallow avg {sz[0][0]:.0f}px p={sz[0][1]:.2f}, deep avg {sz[1][0]:.0f}px p={sz[1][1]:.2f})')
    # flee / chase
    r=ev('''()=>{__sa.clearFood();const s=__sa.shark;s.y=__sa.SURF+(__sa.BED-__sa.SURF)*.5;s.x=innerWidth/2;s.spd=0;s.ang=0;__sa.touch.on=false;s.safe=0;
      const a=__sa.fish[0],c=__sa.fish[1];__sa.setCreature(a,__sa.bite()*.5,"fish");a.x=s.x+110;a.y=s.y;a.vx=0;a.vy=0;
      __sa.setCreature(c,__sa.bite()*2.2,"shark");c.x=s.x-190;c.y=s.y;c.vx=0;c.vy=0;const ax=a.x,cx=c.x;__sa.sim(.6);return [a.x-ax,c.x-cx,a.st,c.st]}''')
    check(r[0]>10 and r[2]=='flee',f'{tag}: smaller fish runs away ({r[0]:.0f}px, {r[2]})')
    check(r[1]>10 and r[3]=='chase',f'{tag}: bigger shark chases ({r[1]:.0f}px, {r[3]})')
    if w==915:
      ev('''()=>{const s=__sa.shark;const a=__sa.fish[2],c=__sa.fish[1];__sa.setCreature(a,__sa.bite()*.5,"fish");a.x=s.x+90;a.y=s.y-30;a.vx=120;__sa.fish[1].x=s.x-200}''');pg.wait_for_timeout(250);pg.screenshot(path=f'{SHOTS}/v6-chase-flee.png')
    cs=ev('''()=>{const s=__sa.shark,c=__sa.fish[1];__sa.setCreature(c,__sa.bite()*2.2,"shark");c.x=s.x-200;c.y=s.y;s.spd=0;let t=0,gave=false;for(;t<6&&__sa.state==="play";t+=.1){s.x=c.x+170;s.y=c.y;__sa.sim(.1);if(c.rest>0){gave=true;break}}return [gave,t,__sa.state]}''')
    check(cs[0] and cs[1]<=5,f'{tag}: chasers give up after ~{cs[1]:.1f}s')
    mx=ev('[__sa.CREATURES.CHASE_DEEP,__sa.CREATURES.CHASE_SHALLOW]');check(max(mx)<1,'chasers always slower than your top speed')
    ev('()=>{__sa.shark.y=__sa.SURF+innerHeight*.45;__sa.clearFood()}')
    check(ev('__sa.need(0)')==16 and ev('__sa.need(1)')==24,'growth needs 16 + 8 per size (slowed)')
    if w==915:
      ev('()=>{const s=__sa.shark;s.y=__sa.BED-60;for(const f of __sa.fish)__sa.spawnFish(f,false);let n=0;for(const f of __sa.fish){if(n<3){__sa.setCreature(f,__sa.bite()*2.4,"shark");f.x=100+n*320;f.y=s.y-90-n*20;n++}}}');pg.wait_for_timeout(500);pg.screenshot(path=f'{SHOTS}/v6-volcanic-big-sharks.png')
    check(not errs,f'{tag}: no console errors {errs[:3]}');check(not outside,f'{tag}: no outside requests {outside[:3]}')
    cx.close()
  # rotate prompt in portrait
  cx=b.new_context(viewport={'width':412,'height':915},device_scale_factor=2,is_mobile=True,has_touch=True,bypass_csp=True,service_workers='block');pg=cx.new_page();pg.goto(URL);pg.wait_for_timeout(400)
  check(pg.is_visible('#rot') and 'sideways' in pg.inner_text('#rot'),'portrait: "Turn your phone sideways" prompt');pg.screenshot(path=f'{SHOTS}/v6-rotate-portrait.png')
  pg.evaluate('()=>{__sa.startAs("white","timed")}');pg.wait_for_timeout(500);t0=pg.evaluate('__sa.timeLeft');pg.wait_for_timeout(700);check(pg.evaluate('__sa.timeLeft')==t0 and pg.evaluate('__sa.rotPaused'),'portrait pauses play')
  cx.close()
  # score + credits screens, perf
  cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,is_mobile=True,has_touch=True,bypass_csp=True,service_workers='block');pg=cx.new_page();pg.goto(URL);pg.wait_for_timeout(300);pg.click('#tap');pg.wait_for_function('window.__saTitleDone===true',timeout=8000)
  for m,shot in [('timed','v6-score-timed'),('endless','v6-score-endless')]:
    pg.evaluate(f'()=>{{__sa.startAs("tiger","{m}");__sa.feed(40);__sa.god=false}}');pg.wait_for_timeout(1200);pg.evaluate('__sa.timeLeft=0.01') if m=='timed' else pg.evaluate('()=>{const s=__sa.shark,c=__sa.fish[0];s.safe=0;__sa.setCreature(c,__sa.bite()*3,"shark");c.x=s.x+s.L*.2;c.y=s.y;c.vx=-50}')
    pg.wait_for_function('__sa.state==="over"',timeout=4000);pg.wait_for_timeout(600);bb=pg.locator('#overUi .card').bounding_box();check(bb['y']>=0 and bb['y']+bb['height']<=412,f'{m} score card fits landscape');pg.screenshot(path=f'{SHOTS}/{shot}.png')
  pg.goto(URL);pg.wait_for_timeout(300);pg.click('#tap');pg.wait_for_function('window.__saTitleDone===true',timeout=8000);pg.click('#cred');pg.wait_for_timeout(400)
  txt=pg.inner_text('#credUi');check(all(k in txt for k in ['Ivan Ili','CC BY 3.0','Durand','6615','Sibley','IMSLP']),'credits intact');bb=pg.locator('#credBack').bounding_box();check(bb and bb['y']+bb['height']<=412,'credits Back button on screen');pg.screenshot(path=f'{SHOTS}/v6-credits.png')
  cx.close()
  b.close()
finally: srv.terminate()
print(f'\n{passes} passed, {len(fails)} failed');sys.exit(1 if fails else 0)
