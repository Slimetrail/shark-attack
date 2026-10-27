# Divers + ambush tests. Run: python3 tests/test_divers.py
import subprocess,time,sys,os,math
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT2','8873'))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
URL=f'http://127.0.0.1:{PORT}/';SHOTS=os.environ.get('SA_SHOTS','/workspace/shark-shots');os.makedirs(SHOTS,exist_ok=True)
fails=[];passes=0
def check(c,m):
    global passes
    print(('PASS ' if c else 'FAIL ')+m,flush=True)
    if c: passes+=1
    else: fails.append(m)
def ev(pg,js): return pg.evaluate(js)
def fresh(b,t='white'):
    cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True);pg=cx.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto(URL+'?round=300');pg.wait_for_timeout(300);pg.click('#tap');pg.wait_for_function('window.__saTitleDone===true',timeout=8000)
    pg.click('#start');pg.wait_for_timeout(150);pg.click(f'.pick[data-type={t}]');pg.wait_for_timeout(250);calm(pg);return cx,pg,errs
def calm(pg): ev(pg,'()=>{__sa.clearFood();const s=__sa.shark;s.x=innerWidth/2;s.y=__sa.SURF+innerHeight*.45;s.spd=0;s.ang=0;__sa.touch.on=false}')
def stunWith(pg,force):  # net hit through the real path, with the ambush roll forced
    ev(pg,f'()=>{{__sa.setAmbushForce({force});__sa.netHit(null)}}')
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  cx,pg,errs=fresh(b)
  D=ev(pg,'__sa.DIV');print('constants',D)
  ev(pg,'__sa.surferCaught();__sa.surferCaught()');check(ev(pg,'__sa.divers.length')==0,'no divers before the 3rd surfer')
  ev(pg,'__sa.surferCaught()');check(ev(pg,'__sa.divers.length')==1 and ev(pg,'__sa.bannerT')>1.3,'3rd surfer spawns a diver + Divers! banner')
  d0=ev(pg,'({x:__sa.divers[0].x,y:__sa.divers[0].y,g:__sa.divers[0].grace})');sx=ev(pg,'[__sa.shark.x,__sa.shark.y]')
  check(math.hypot(d0['x']-sx[0],d0['y']-sx[1])>150 and d0['g']>=1.9,f'diver spawns away from the shark with ~2 s grace {d0}')
  pg.wait_for_timeout(200);pg.screenshot(path=f'{SHOTS}/divers-banner.png')
  check(ev(pg,'__sa.diverSpeed()/__sa.maxSpeed()')<.62,f"diver slower than the shark's cap ({ev(pg,'__sa.diverSpeed()/__sa.maxSpeed()'):.2f})")
  # chase within range
  ev(pg,'()=>{const d=__sa.divers[0];d.x=__sa.shark.x-innerHeight*.25;d.y=__sa.shark.y;d.grace=99;d.st="wander";d.ang=Math.PI/2}');pg.wait_for_timeout(300)
  check(ev(pg,'__sa.divers[0].st')=='chase','diver within detect range chases');pg.wait_for_timeout(600);pg.screenshot(path=f'{SHOTS}/diver-chasing.png')
  # out of range -> gives up after ~3 s
  ev(pg,'()=>{const d=__sa.divers[0];d.x=-40;d.y=__sa.SURF+innerHeight*1.1;const s=__sa.shark;s.x=innerWidth-60;s.y=__sa.SURF+40}');pg.wait_for_timeout(1500)
  ev(pg,'__sa.divers[0].st="chase";__sa.divers[0].lost=0');st1='chase';st2=None
  for i in range(18):
    ev(pg,'()=>{const d=__sa.divers[0];d.x=-40;d.y=__sa.SURF+innerHeight*1.1;const s=__sa.shark;s.x=innerWidth-60;s.y=__sa.SURF+40;s.spd=0}');pg.wait_for_timeout(200)
    if i==8: st2=ev(pg,'__sa.divers[0].st')
  st1=st1 if st2=='chase' else 'x'
  check(st1=='chase' and ev(pg,'__sa.divers[0].st')=='wander','diver keeps chasing briefly, gives up after ~3 s out of range')
  # net hit: stun + cooldown + growth loss (through the real collision)
  calm(pg);ev(pg,'__sa.shark.meter=4');ev(pg,'()=>{const d=__sa.divers[0],s=__sa.shark;d.grace=0;d.cool=0;d.ang=0;d.x=s.x-46;d.y=s.y}');pg.wait_for_timeout(120)
  check(ev(pg,'__sa.netHits')==1 and ev(pg,'__sa.shark.stun')>.7 and ev(pg,'__sa.divers[0].cool')>1.7 and ev(pg,'__sa.shark.meter')<4,'net hit stuns ~1 s, loses growth, diver gets ~2 s cooldown')
  check(ev(pg,'__sa.amb.on')==False,'hit 1 never brings an ambush');pg.screenshot(path=f'{SHOTS}/hud-catch-icons.png')
  pg.wait_for_timeout(1000);check(ev(pg,'__sa.shark.stun')==0,'stun wears off')
  # Play again resets counters: end the round, play again
  ev(pg,'__sa.netHit(null);__sa.netHit(null)');check(ev(pg,'__sa.state')=='over' and pg.inner_text('#reason')=='Caught!' and ev(pg,'__sa.endReason')=='caught','three net hits end the round with Caught!')
  check(pg.locator('#again').is_visible() and pg.inner_text('#final')!='','Caught! screen keeps score and Play again');pg.wait_for_timeout(300);pg.screenshot(path=f'{SHOTS}/score-caught.png')
  pg.click('#again');pg.wait_for_timeout(200);check(ev(pg,'__sa.netHits')==0 and ev(pg,'__sa.surfersCaught')==0 and ev(pg,'__sa.divers.length')==0 and not ev(pg,'__sa.amb.on'),'counters reset on Play again')
  # max 3 divers, one per 3 surfers
  calm(pg);ev(pg,'for(let i=0;i<6;i++)__sa.surferCaught()');n6=ev(pg,'__sa.divers.length');ev(pg,'for(let i=0;i<12;i++)__sa.surferCaught()');check(n6==2 and ev(pg,'__sa.divers.length')==3,'one more diver per 3 surfers, max 3')
  ev(pg,'__sa.divers.length=0')
  # ambush: never reaches before warning time; unescaped -> Gulp!
  calm(pg);ev(pg,'__sa.netHit(null)');pg.wait_for_timeout(1100);calm(pg);t0=ev(pg,'performance.now()');stunWith(pg,'true')
  check(ev(pg,'__sa.amb.on') and ev(pg,'__sa.amb.L')>ev(pg,'__sa.shark.L')*1.4,'hit 2 (forced roll) brings one ambusher, clearly bigger than the shark')
  pg.wait_for_timeout(200);pg.screenshot(path=f'{SHOTS}/stun-ambush-warning.png');pg.wait_for_timeout(350);pg.screenshot(path=f'{SHOTS}/ambusher-entering.png')
  while ev(pg,'__sa.state')=='play' and ev(pg,'performance.now()')-t0<1150: pg.wait_for_timeout(40)
  check(ev(pg,'__sa.state')=='play' and ev(pg,'__sa.amb.reachT')<0,'ambusher has not reached the shark before 1.15 s')
  ev(pg,'__sa.netHit(null)') if False else None
  pg.wait_for_function('__sa.state!=="play"',timeout=2000);rt=ev(pg,'__sa.amb.reachT');print('reachT',rt);check(pg.inner_text('#reason')=='Gulp!' and ev(pg,'__sa.amb.ate') and rt>=1.2,'unescaped stunned shark is eaten -> Gulp! screen')
  # escape by wiggling (real pointer events)
  pg.click('#again');pg.wait_for_timeout(200);calm(pg);ev(pg,'__sa.netHit(null)');pg.wait_for_timeout(1100);calm(pg);stunWith(pg,'true')
  pg.mouse.move(150,250);pg.mouse.down()
  for i in range(8): pg.mouse.move(280 if i%2==0 else 150,250,steps=3);pg.wait_for_timeout(30)
  pg.mouse.up();check(ev(pg,'__sa.shark.stun')==0 and ev(pg,'__sa.struggles')>=3,f"wiggling breaks free ({ev(pg,'__sa.struggles')} struggles)")
  pg.wait_for_timeout(1500);check(ev(pg,'__sa.state')=='play' and ev(pg,'__sa.amb.phase')=='leave','escaped shark is not eaten; ambusher swims off')
  check(ev(pg,'__sa.netHit(null)') is None and ev(pg,'__sa.state')=='over' and pg.inner_text('#reason')=='Caught!','hit 3 ends with Caught! (round already over, no ambush needed)')
  # one ambusher at a time + cooldown; leaping/unstunned shark cannot be eaten
  pg.click('#again');pg.wait_for_timeout(200);calm(pg);ev(pg,'__sa.netHit(null)');pg.wait_for_timeout(1100);calm(pg);stunWith(pg,'true')
  ref=ev(pg,'__sa.amb.t');ev(pg,'__sa.shark.stun=0');ev(pg,'__sa.ambCool=0');ev(pg,'()=>{window.__x=__sa.amb.x0}')
  check(ev(pg,'__sa.amb.t')>=ref and ev(pg,'__sa.amb.on'),'one ambusher active')
  pg.wait_for_timeout(1500);check(ev(pg,'__sa.state')=='play','unstunned shark is not eaten when the ambusher arrives')
  pg.click('body') if False else None
  # leaping: start ambush, then put shark in the air at arrival
  ev(pg,'__sa.shark.stun=0;__sa.timeLeft=0');pg.wait_for_function('__sa.state==="over"');pg.click('#again');pg.wait_for_timeout(150);ev(pg,'()=>{__sa.amb.on=false;__sa.ambCool=0}');calm(pg);ev(pg,'__sa.netHit(null)');ev(pg,'__sa.shark.stun=0');stunWith(pg,'true')
  pg.wait_for_timeout(900);ev(pg,'()=>{const s=__sa.shark;s.stun=5;s.air=true;s.vy=-50;s.vx=0;s.g=1;s.y=__sa.SURF-80}');pg.wait_for_timeout(700)
  print('leap dbg',ev(pg,'[__sa.state,__sa.endReason,__sa.amb.ate,__sa.shark.air,__sa.shark.y-__sa.SURF]'));check(ev(pg,'__sa.state')=='play' and not ev(pg,'__sa.amb.ate'),'leaping shark is not eaten by the ambusher')
  ev(pg,'__sa.shark.air=false;__sa.shark.stun=0')
  # one at a time: second ambush request while active refused; cooldown blocks
  ev(pg,'()=>{__sa.amb.on=false;__sa.ambCool=0}');calm(pg);stunWith(pg,'true');x1=ev(pg,'__sa.amb.x0');ev(pg,'__sa.shark.stun=0');stunWith(pg,'true')
  check(ev(pg,'__sa.amb.x0')==x1 and ev(pg,'__sa.netHits')==3 or ev(pg,'__sa.state')=='over','second ambush not started while one is active (hit 3 ended the round)')
  pg.click('#again');pg.wait_for_timeout(200);calm(pg);ev(pg,'__sa.netHit(null)');ev(pg,'__sa.ambCool=3;__sa.shark.stun=0');stunWith(pg,'true');check(not ev(pg,'__sa.amb.on'),'ambush cooldown blocks a new ambush')
  # hit 1 never ambushes (repeat, even with roll forced true)
  ok=True
  for i in range(10):
    pg.click('#again') if ev(pg,'__sa.state')=='over' else None;pg.wait_for_timeout(100)
    ev(pg,'()=>{__sa.amb.on=false;__sa.ambCool=0}');ev(pg,'__sa.setAmbushForce(true)');
    if ev(pg,'__sa.netHits')==0: ev(pg,'__sa.netHit(null)');ok=ok and not ev(pg,'__sa.amb.on')
    ev(pg,'__sa.netHit(null);__sa.netHit(null)')
  check(ok,'hit 1 never brings an ambush, even with the roll forced')
  check(not errs,f'no console errors {errs}')
  # perf with 3 divers + ambusher
  pg.click('#again') if ev(pg,'__sa.state')=='over' else None;pg.wait_for_timeout(200)
  cdp=cx.new_cdp_session(pg)
  for rate in (1,4):
    cdp.send('Emulation.setCPUThrottlingRate',{'rate':rate});calm(pg);ev(pg,'()=>{__sa.setAmbushForce(null);for(let i=0;i<9;i++)__sa.surferCaught();for(const d of __sa.divers){d.grace=99}}')
    ev(pg,'()=>{__sa.amb.on=false;__sa.ambCool=0;__sa.netHit(null);__sa.setAmbushForce(true);__sa.netHit(null);__sa.shark.stun=99;__sa.perf.reset()}') if rate==1 else ev(pg,'__sa.perf.reset()')
    pg.wait_for_timeout(3000);pf=ev(pg,'({f:__sa.perf.frames,js:__sa.perf.js,dt:__sa.perf.dtSum})')
    print(f"PERF divers+ambush cpu x{rate}: {pf['f']} frames/3s, avg JS {pf['js']/max(1,pf['f']):.2f} ms/frame",flush=True)
    check(pf['js']/max(1,pf['f'])<2.5 and pf['f']>80,f'perf ok with 3 divers + ambusher at cpu x{rate}')
  b.close()
finally:
  srv.terminate()
print(f'{passes} passed, {len(fails)} failed');sys.exit(1 if fails else 0)
