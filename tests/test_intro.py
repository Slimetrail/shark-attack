# b44 tests: the title intro plays at EVERY launch (Jeremy: "Shark game needs to do the intro every time").
# Run: python3 tests/test_intro.py   (port 8893). Screenshots -> SA_INTRO_SHOTS (default /workspace/intro-shots/shark)
import os,sys,subprocess,time
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORTI','8893'))
URL=f'http://127.0.0.1:{PORT}/';SHOTS=os.environ.get('SA_INTRO_SHOTS','/workspace/intro-shots/shark');os.makedirs(SHOTS,exist_ok=True);passes=0;fails=[]
def check(c,m):
  global passes
  if c: passes+=1;print('PASS',m)
  else: fails.append(m);print('FAIL',m)
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
def intro_runs(pg,tag,shots=False):
  check(pg.evaluate('__sa.state')=='tap' and pg.is_visible('#tap'),f'{tag}: opens on Tap to start')
  pg.click('#tap');pg.wait_for_timeout(200)
  check(pg.evaluate('__sa.state')=='title' and pg.evaluate('window.__saTitleDone')==False and pg.evaluate('__sa.titleT')<1,f'{tag}: intro starts from the beginning')
  if shots: pg.screenshot(path=f'{SHOTS}/intro-1-swim-past.png')
  pg.wait_for_timeout(1100)
  if shots: pg.screenshot(path=f'{SHOTS}/intro-2-around-title.png')
  check(pg.evaluate('__sa.titleShark')!=None and pg.evaluate('__sa.titleShark.open')==True,f'{tag}: shark swims in the intro, mouth wide open (b46)')
  check(pg.evaluate('__sa.TITLE.SWIM')<=20,f'{tag}: b46 intro swim part is at most 20 s')
  check(pg.evaluate('__sa.titleMusicPlaying'),f'{tag}: intro music plays')
  pg.wait_for_function('window.__saTitleDone===true',timeout=15000)
  if shots: pg.wait_for_timeout(400);pg.screenshot(path=f'{SHOTS}/intro-3-dive-done.png')
  check(True,f'{tag}: intro finishes')
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
  cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');errs=[]
  for n in (1,2,3):
    pg=cx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(URL);pg.wait_for_timeout(300);intro_runs(pg,f'launch {n}',shots=(n==1));
    if n<3: pg.close()
  pg.reload();pg.wait_for_timeout(300);intro_runs(pg,'after reload')
  pg.evaluate('dispatchEvent(new PageTransitionEvent("pageshow",{persisted:true}))');pg.wait_for_timeout(100)
  check(not pg.evaluate('__sa.titleMusicPlaying'),'bfcache restore: old intro music stopped');intro_runs(pg,'after pageshow persisted')
  ls=pg.evaluate('Object.keys(localStorage)');check(not any('intro' in k.lower() or 'title' in k.lower() or 'seen' in k.lower() for k in ls),f'no intro/seen flag stored ({ls})')
  pg.close()
  # music switch respected: songs off -> intro runs, music silent
  pg=cx.new_page();pg.goto(URL);pg.wait_for_timeout(300);pg.evaluate('localStorage.setItem("sharkAttack_songs","0")');pg.reload();pg.wait_for_timeout(300)
  pg.click('#tap');pg.wait_for_timeout(300);check(pg.evaluate('__sa.state')=='title' and not pg.evaluate('__sa.titleMusicPlaying'),'music off: intro still runs, no music')
  pg.wait_for_function('window.__saTitleDone===true',timeout=15000);check(True,'music off: intro finishes')
  # calm mode: intro still runs
  pg.evaluate('localStorage.setItem("sharkAttack_calm","1")');pg.reload();pg.wait_for_timeout(300);pg.click('#tap');pg.wait_for_function('window.__saTitleDone===true',timeout=15000);check(True,'calm mode: intro runs')
  check(not errs,f'no page errors {errs[:2]}')
  b.close()
finally: srv.terminate()
print(f'\n{passes} passed, {len(fails)} failed');sys.exit(1 if fails else 0)
