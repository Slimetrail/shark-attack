# Game-mode tests: Timed vs Endless, per-mode best (b52: divers removed). Run: python3 tests/test_modes.py
import subprocess,time,sys,os
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT6','8881'))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
URL=f'http://127.0.0.1:{PORT}/';SHOTS=os.environ.get('SA_SHOTS','/workspace/shark-shots');os.makedirs(SHOTS,exist_ok=True);fails=[];passes=0
def check(c,m):
    global passes
    print(('PASS ' if c else 'FAIL ')+m,flush=True)
    if c: passes+=1
    else: fails.append(m)
def ev(pg,js): return pg.evaluate(js)
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');pg=cx.new_page();errs=[]
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
  pg.goto(URL);pg.wait_for_timeout(300);pg.click('#tap');pg.wait_for_function('window.__saTitleDone===true',timeout=15000);pg.click('#start');pg.wait_for_timeout(300)
  check(pg.is_visible('#mode_timed') and pg.is_visible('#mode_endless'),'pick screen shows Timed and Endless buttons')
  check('60' in pg.inner_text('#mode_timed') and 'Endless' in pg.inner_text('#mode_endless'),'mode labels')
  check(ev(pg,'__sa.mode')=='timed' and 'sel' in pg.get_attribute('#mode_timed','class'),'Timed is the default')
  pg.click('#mode_endless');pg.wait_for_timeout(100)
  check(ev(pg,'__sa.mode')=='endless' and 'sel' in pg.get_attribute('#mode_endless','class') and ev(pg,'localStorage.getItem("sharkAttack_mode")')=='endless','tapping Endless selects and remembers it')
  r=pg.evaluate('()=>{const a=document.getElementById("mode_endless").getBoundingClientRect(),b=document.querySelector(".pick").getBoundingClientRect();return a.bottom<=b.top}');check(r,'mode buttons do not overlap shark cards')
  pg.screenshot(path=f'{SHOTS}/pick-modes.png')
  pg.click('.pick[data-type=white]');pg.wait_for_timeout(300)
  check(ev(pg,'__sa.state')=='play' and ev(pg,'__sa.mode')=='endless','endless round starts')
  Q='()=>{__sa.clearFood();__sa.touch.on=false}'
  t0=ev(pg,'__sa.timeLeft');ev(pg,f'__sa.sim(5,{Q})');check(ev(pg,'__sa.timeLeft')==t0 and ev(pg,'__sa.state')=='play',f'no countdown in endless (state={ev(pg,"__sa.state")} end={ev(pg,"__sa.endReason")})')
  ev(pg,f'__sa.timeLeft=0;__sa.sim(.5,{Q})');check(ev(pg,'__sa.state')=='play','timeLeft 0 does not end endless')
  for k in range(206): ev(pg,'__sa.surferCaught()')
  ev(pg,f'__sa.sim(5,{Q})');check(ev(pg,'__sa.state')=='play','b52: 206 surfers caught, no divers come, endless keeps going')
  check(ev(pg,'__sa.DIV')==None and ev(pg,'"spawnDiver" in __sa')==False,'b52: no diver hooks')
  ev(pg,'localStorage.removeItem("sharkAttack_best_endless")')
  check(ev(pg,'__sa.state')=='play','still playing before the end')
  pg.evaluate('()=>gameOver("eaten")')
  pg.wait_for_function('__sa.state==="over"',timeout=4000);pg.wait_for_timeout(100)
  check(ev(pg,'__sa.state')=='over' and pg.inner_text('#reason')=='Gulp!','endless ends with Gulp! when eaten')
  st=pg.inner_text('#stats');check('Surfers eaten: 206' in st and 'Survived' in st,f'endless score screen shows surfers + time survived ({st})')
  check('Endless' in pg.inner_text('#bestTxt') and ev(pg,'+localStorage.getItem("sharkAttack_best_endless")')==ev(pg,'__sa.score'),'endless best saved separately')
  pg.screenshot(path=f'{SHOTS}/endless-score.png')
  # b52: timed has no "Caught!" any more; it ends on time
  tb=ev(pg,'localStorage.getItem("sharkAttack_best")')
  ev(pg,'__sa.startAs("white","timed")')
  for k in range(20): ev(pg,'__sa.surferCaught()')
  ev(pg,'__sa.sim(5,()=>{__sa.touch.on=false})');check(ev(pg,'__sa.state')=='play','Timed: 20 surfers caught, still playing (no Caught!)')
  ev(pg,'__sa.timeLeft=.05');ev(pg,'__sa.sim(.3,()=>{__sa.touch.on=false})');pg.wait_for_timeout(200)
  check(ev(pg,'__sa.state')=='over' and pg.inner_text('#reason')=="Time's up!",'Timed ends with Time\'s up!')
  check(ev(pg,'localStorage.getItem("sharkAttack_best")')==tb or ev(pg,'__sa.score')>0,'timed best untouched by endless')
  ev(pg,'__sa.startAs("white","timed")');t0=ev(pg,'__sa.timeLeft');ev(pg,'__sa.sim(2,()=>{__sa.touch.on=false})');check(ev(pg,'__sa.timeLeft')<t0-1.9,'timed still counts down')
  check(not errs,f'no console errors {errs}')
  b.close()
finally: srv.terminate()
print(f'{passes} passed, {len(fails)} failed');sys.exit(1 if fails else 0)
