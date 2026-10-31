# b47 tests: the intro shark circles the title twice, then BITES a tooth-edged scoop out of the title letters (Jeremy: circling does not count).
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
check('"build":"47"' in open(os.path.join(ROOT,'version.json')).read() and 'content="47"' in html and 'game.js?v=47' in html and 'game.js?v=47' in sw,'build 47 in version.json, index.html and sw.js')
check(not os.path.exists(os.path.join(ROOT,'art/title-art.webp')) and 'title-art' not in sw and 'title-art.webp' not in open(os.path.join(ROOT,'game.js')).read() and 'title-art' not in html,'title-art.webp removed: no file, not cached, not loaded')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');pg=cx.new_page()
  errs=[];reqs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
  pg.on('request',lambda r:reqs.append(r.url))
  pg.add_init_script('window.__saTitleLog=1');pg.goto(URL);pg.wait_for_timeout(300);pg.click('#tap')
  T=pg.evaluate('__sa.TITLE');biteAt=T['ENTER']+2*T['LAP']+T['LUNGE']
  ink0=None;shots={biteAt-.25:'1-before-bite',biteAt+.08:'2-at-bite',biteAt+.7:'3-after-bite'};pre_bite_none=True
  while True:
    st=pg.evaluate('({t:__sa.titleT,b:__sa.titleBite,ink:__sa.titleInk(),done:window.__saTitleDone})')
    if st['t']<biteAt-.05:
      ink0=st['ink'];pre_bite_none=pre_bite_none and st['b'] is None
    for k in sorted(shots):
      if st['t']>=k: pg.screenshot(path=f"{SHOTS}/{shots.pop(k)}.png")
    if st['done'] and not shots: break
    if st['t']>15: break
    pg.wait_for_timeout(25)
  log=pg.evaluate('__sa.titleLog');bt=pg.evaluate('__sa.titleBite')
  laps={(x[1],x[2]) for x in log}
  check(all((ly,k) in laps for ly in ('behind','front') for k in (1,2)),'intro circles the title twice (behind + in front, laps 1 and 2)')
  check(pre_bite_none,'no bite before the two laps finish')
  bi=[i for i,x in enumerate(log) if x[1]=='bite'];lap2=[i for i,x in enumerate(log) if x[2]==2]
  check(len(bi)==1 and bt is not None and lap2 and bi[0]>max(lap2),f'exactly one bite event fires, after lap 2 ({bt})')
  check(bt and bt['after']<bt['before']*0.97 and ink0 and pg.evaluate('__sa.titleInk()')<ink0*0.97,f"letters visibly reduced (title canvas opaque pixels {bt and bt['before']} -> {bt and bt['after']}, {100*(1-bt['after']/bt['before']):.1f}% gone)" if bt else 'letters reduced')
  check(any(x[1]=='front' and x[2]==3 and not x[3] for x in log),'jaw closes (closed sprite) on the letters at the bite')
  check(pg.evaluate('__sa.titleArt')==0,'no poster picture shown')
  pg.wait_for_function('window.__saTitleDone===true',timeout=5000);pg.wait_for_timeout(600)
  check(pg.is_visible('#start') and pg.is_visible('#titleUi'),'title menu (Start) appears after the intro');pg.screenshot(path=f'{SHOTS}/4-title-menu.png')
  check(not any('title-art' in u for u in reqs) and all(u.startswith(URL) for u in reqs),'no request for title-art.webp, no outside requests')
  check(not errs,f'no console errors {errs[:3]}');cx.close()
  # skip: Start mid-intro (after the 600 ms guard) goes straight to the shark pick, before and during the bite
  for at in (1.0,biteAt+.1):
    cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');pg=cx.new_page();e2=[];pg.on('pageerror',lambda e:e2.append(str(e)))
    pg.goto(URL);pg.wait_for_timeout(300);pg.click('#tap');pg.wait_for_function(f'__sa.titleT>{at}',timeout=15000);pg.tap('#start');pg.wait_for_timeout(300)
    check(pg.evaluate('__sa.state')=='pick' and pg.is_visible('.pick') and not e2,f'skip by tap: Start at {at:.1f}s skips the intro to the pick screen')
    cx.close()
  # perf: frame time of the title during the bite stays phone-safe
  cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,bypass_csp=True,service_workers='block');pg=cx.new_page();pg.goto(URL);pg.wait_for_timeout(300);pg.click('#tap')
  pg.wait_for_function(f'__sa.titleT>{biteAt-.3}',timeout=15000)
  ft=pg.evaluate('()=>new Promise(r=>{const a=[];let l=performance.now();const f=n=>{a.push(n-l);l=n;if(a.length<60)requestAnimationFrame(f);else r(a)};requestAnimationFrame(f)})')
  ft.sort();check(ft[int(len(ft)*.9)]<40,f'title frames around the bite: p90 {ft[int(len(ft)*.9)]:.1f} ms (<40)');cx.close()
  b.close()
finally: srv.terminate()
print(f'\n{passes} passed, {len(fails)} failed');sys.exit(1 if fails else 0)
