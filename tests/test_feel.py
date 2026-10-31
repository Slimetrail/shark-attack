# Touch-feel, lifecycle and tuning-constant tests. Run: python3 tests/test_feel.py
import subprocess,time,sys,os,math,json
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT4','8877'))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
URL=f'http://127.0.0.1:{PORT}/';fails=[];passes=0
def check(c,m):
    global passes
    print(('PASS ' if c else 'FAIL ')+m,flush=True)
    if c: passes+=1
    else: fails.append(m)
def ev(pg,js): return pg.evaluate(js)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
  cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True);pg=cx.new_page();errs=[]
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
  pg.goto(URL+'?round=300');pg.wait_for_timeout(300);pg.click('#tap');pg.wait_for_function('window.__saTitleDone===true',timeout=15000);pg.click('#start');pg.wait_for_timeout(150);pg.click('.pick[data-type=white]');pg.wait_for_timeout(300)
  def stage(): ev(pg,'()=>{__sa.clearFood();const s=__sa.shark;s.x=innerWidth/2;s.y=__sa.SURF+innerHeight*.45;s.ang=0;s.spd=__sa.maxSpeed()*.2;__sa.touch.on=false;__sa.touch.drive=0}')
  # tuning constants are exposed and sane
  D=ev(pg,'__sa.DIV');src=open(os.path.join(ROOT,'game.js')).read();check('return m?+m[1]:60' in src and D['DIVER_CATCHES_TO_LOSE']==3 and D['AMBUSH_ON_HIT'][1]==False and D['AMBUSH_CHANCE']==.5 and D['AMBUSH_ON_HIT'][3]==True,'defaults: 60 s round, 3 net hits, ambush hit1 never / hit2 50% / hit3 ends')
  check(D['AMBUSH_ARRIVE_MS']>=1200,'ambush warning time >= 1.2 s')
  # v10 analog: no dead spot; a jitter of 1-2 px from the first touch gives only a tiny drive (slow), never a burst
  stage();pg.mouse.move(200,200);pg.mouse.down();a0=ev(pg,'__sa.shark.ang')
  for dx,dy in [(1,1),(2,-1),(-1,2),(1,-2)]: pg.mouse.move(200+dx,200+dy);pg.wait_for_timeout(20)
  dj=ev(pg,'__sa.touch.drive');check(0<dj<.02,f'tiny jitter (2 px from the first touch) = tiny drive {dj:.4f}, no dead zone, no burst');pg.mouse.up()
  # speed cap
  stage();pg.mouse.move(30,200);pg.mouse.down()
  for i in range(40): pg.mouse.move(30+(i%2)*0+ (i*9)%380,200);pg.wait_for_timeout(16)
  pg.wait_for_timeout(600);sp=ev(pg,'[__sa.shark.spd,__sa.maxSpeed()]');pg.mouse.up()
  check(sp[0]<=sp[1]*1.001,f'speed never exceeds the cap ({sp[0]:.0f} <= {sp[1]:.0f} px/s)')
  # slow stop on release
  stage();ev(pg,'__sa.shark.spd=__sa.maxSpeed()');s0=ev(pg,'__sa.shark.spd');pg.wait_for_timeout(250);s1=ev(pg,'__sa.shark.spd');pg.wait_for_timeout(1500);s2=ev(pg,'__sa.shark.spd')
  check(s1>s0*.6 and s2<s0*.5 and s2>0,f'release: drifts and slows gradually ({s0:.0f} -> {s1:.0f} -> {s2:.0f} px/s), never a dead stop')
  # pointercancel ends steering
  stage();pg.mouse.move(100,200);pg.mouse.down();pg.mouse.move(200,200,steps=4)
  ev(pg,'document.getElementById("c").dispatchEvent(new PointerEvent("pointercancel",{bubbles:true}))');check(ev(pg,'__sa.touch.on')==False,'pointercancel releases the finger (no stuck steering)');pg.mouse.up()
  # wiggle escape with real pointer events
  stage();ev(pg,'__sa.setAmbushForce(true);__sa.netHit(null)');ev(pg,'__sa.shark.stun=0;__sa.shark.safe=0');ev(pg,'__sa.ambCool=0;__sa.amb.on=false;__sa.netHit(null)')
  pg.mouse.move(150,250);pg.mouse.down()
  for i in range(6): pg.mouse.move(260 if i%2==0 else 150,250,steps=3);pg.wait_for_timeout(25)
  pg.mouse.up();check(ev(pg,'__sa.shark.stun')==0,'wiggle escape frees the shark before the ambusher arrives');pg.wait_for_timeout(1600);check(ev(pg,'__sa.state')=='play','escaped shark survives the ambush')
  # surface glide: shallow upward angle keeps speed (no speed-killing bumps)
  stage();ev(pg,'()=>{const s=__sa.shark;s.y=__sa.SURF+s.L*.1;s.ang=-.2;s.spd=__sa.maxSpeed()*.4;s.run=0;Object.assign(__sa.touch,{on:true,dir:-.2,drive:1,lastMove:performance.now()+9e9})}');sp0=ev(pg,'__sa.shark.spd');pg.wait_for_timeout(300);ev(pg,'__sa.touch.on=false')
  check(ev(pg,'__sa.shark.spd')>=sp0*.95,'shallow angle into the surface glides along it without losing speed')
  # backgrounding pauses game + music, returning resumes
  ev(pg,'()=>{Object.defineProperty(document,"hidden",{configurable:true,get:()=>true});document.dispatchEvent(new Event("visibilitychange"))}');pg.wait_for_timeout(300)
  tl=ev(pg,'__sa.timeLeft');pg.wait_for_timeout(500)
  check(not ev(pg,'__sa.looping') and ev(pg,'__sa.timeLeft')==tl and ev(pg,'__sa.acState') in ('suspended','none'),f"backgrounded: game paused and audio suspended ({ev(pg,'__sa.acState')})")
  ev(pg,'()=>{Object.defineProperty(document,"hidden",{configurable:true,get:()=>false});document.dispatchEvent(new Event("visibilitychange"))}');pg.wait_for_timeout(400)
  check(ev(pg,'__sa.looping') and ev(pg,'__sa.timeLeft')<tl and ev(pg,'__sa.acState')=='running','back in front: game and audio resume')
  # no long-press menu / zoom / scroll
  prevented=ev(pg,'(()=>{const e=new MouseEvent("contextmenu",{bubbles:true,cancelable:true});document.getElementById("c").dispatchEvent(e);return e.defaultPrevented})()')
  css=ev(pg,'(()=>{const s=getComputedStyle(document.body);return [s.touchAction,s.userSelect||s.webkitUserSelect,s.overflow]})()')
  vp=ev(pg,'document.querySelector("meta[name=viewport]").content')
  check(prevented and css[0]=='none' and css[1]=='none' and css[2]=='hidden' and 'user-scalable=no' in vp,f'no long-press menu, no scroll, no pinch zoom {css}')
  man=json.load(open(os.path.join(ROOT,'manifest.webmanifest')));check(man['orientation']=='landscape','manifest locks landscape')
  check(not errs,f'no console errors {errs}')
  b.close()
finally: srv.terminate()
print(f'{passes} passed, {len(fails)} failed');sys.exit(1 if fails else 0)
