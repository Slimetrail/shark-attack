# b47 tests (updated for b50): build/no-poster/no-outside-request checks, Start skips the intro, phone-safe frames. b50 replaced the b47 letter-bite
# with the held head-on pose (Jeremy 5:22 PM), so the bite checks now assert the title is NEVER cut.
# Run: /workspace/.pwvenv/bin/python tests/test_b47.py  (port 8899). Screenshots -> art-shots-b47/ (not committed).
import os,sys,subprocess,time
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT47','8899'));URL=f'http://127.0.0.1:{PORT}/'
SHOTS=os.path.join(ROOT,'art-shots-b47');os.makedirs(SHOTS,exist_ok=True);passes=0;fails=[]
def check(c,m):
  global passes
  if c: passes+=1;print('PASS',m)
  else: fails.append(m);print('FAIL',m)
html=open(os.path.join(ROOT,'index.html')).read();sw=open(os.path.join(ROOT,'sw.js')).read()
check('"build":"50"' in open(os.path.join(ROOT,'version.json')).read() and 'content="50"' in html and 'game.js?v=50' in html and 'game.js?v=50' in sw,'build 50 in version.json, index.html and sw.js')
check(not os.path.exists(os.path.join(ROOT,'art/title-art.webp')) and 'title-art' not in sw and 'title-art.webp' not in open(os.path.join(ROOT,'game.js')).read() and 'title-art' not in html,'title-art.webp removed: no file, not cached, not loaded')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');pg=cx.new_page()
  errs=[];reqs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
  pg.on('request',lambda r:reqs.append(r.url))
  pg.add_init_script('window.__saTitleLog=1');pg.goto(URL);pg.wait_for_timeout(300);pg.click('#tap')
  # b50 (Jeremy, 5:22 PM): the b47 letter-bite is replaced. The title is never cut; the shark swims in behind, faces the camera, snaps once and holds the pose.
  T=pg.evaluate('__sa.TITLE');biteAt=T['SWIM']-T['SNAP']   # the snap moment (name kept so the skip and perf checks below still aim at the jaw action)
  ink0=pg.evaluate('__sa.titleInk()');inks=[];shots={biteAt-.25:'1-before-snap',biteAt+.1:'2-at-snap',biteAt+.7:'3-pose'}
  while True:
    st=pg.evaluate('({t:__sa.titleT,ink:__sa.titleInk(),done:window.__saTitleDone})');inks.append(st['ink'])
    for k in sorted(shots):
      if st['t']>=k: pg.screenshot(path=f"{SHOTS}/{shots.pop(k)}.png")
    if st['done'] and not shots: break
    if st['t']>15: break
    pg.wait_for_timeout(25)
  log=pg.evaluate('__sa.titleLog')
  check(set(inks)=={ink0},f'b50: title letters never reduced (title canvas opaque pixels stay {ink0} over {len(inks)} samples)')
  check(pg.evaluate('__sa.titleBite') is None and not any(x[1]=='bite' for x in log),'b50: no bite event (no letters carved)')
  check(sum(1 for x in log if x[1]=='snap')==1 and any(x[1]=='pose' for x in log),'b50: one jaw snap, then the held pose')
  check(pg.evaluate('__sa.titleArt')==0,'no poster picture shown')
  pg.wait_for_function('window.__saTitleDone===true',timeout=5000);pg.wait_for_timeout(600)
  check(pg.is_visible('#start') and pg.is_visible('#titleUi'),'title menu (Start) shown at the held pose');pg.screenshot(path=f'{SHOTS}/4-title-menu.png')
  check(not any('title-art' in u for u in reqs) and all(u.startswith(URL) for u in reqs),'no request for title-art.webp, no outside requests')
  check(not errs,f'no console errors {errs[:3]}');cx.close()
  # skip: Start mid-intro (after the 600 ms guard) goes straight to the shark pick, before and during the bite
  for at in (1.0,biteAt+.1):
    cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');pg=cx.new_page();e2=[];pg.on('pageerror',lambda e:e2.append(str(e)))
    pg.goto(URL);pg.wait_for_timeout(300);pg.click('#tap');pg.wait_for_function(f'__sa.titleT>{at}',timeout=15000);pg.tap('#start');pg.wait_for_timeout(300)
    check(pg.evaluate('__sa.state')=='pick' and pg.is_visible('.pick') and not e2,f'skip by tap: Start at {at:.1f}s goes straight to the pick screen')
    cx.close()
  # perf: frame time of the title during the bite stays phone-safe
  cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,bypass_csp=True,service_workers='block');pg=cx.new_page();pg.goto(URL);pg.wait_for_timeout(300);pg.click('#tap')
  pg.wait_for_function(f'__sa.titleT>{biteAt-.3}',timeout=15000)
  ft=pg.evaluate('()=>new Promise(r=>{const a=[];let l=performance.now();const f=n=>{a.push(n-l);l=n;if(a.length<60)requestAnimationFrame(f);else r(a)};requestAnimationFrame(f)})')
  ft.sort();check(ft[int(len(ft)*.9)]<40,f'title frames around the snap: p90 {ft[int(len(ft)*.9)]:.1f} ms (<40)');cx.close()
  b.close()
finally: srv.terminate()
print(f'\n{passes} passed, {len(fails)} failed');sys.exit(1 if fails else 0)
