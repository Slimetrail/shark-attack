# Update mechanism + TEST build tests. Builds the TEST app (tools/make_test_build.py --worktree) and serves it at
# /shark-attack-test/ next to a copy of the live game at /shark-attack/ on one origin (like GitHub Pages).
# Run: python3 tests/test_update.py   (port 8891)
import os,sys,subprocess,time,json,shutil,tempfile,re
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORTU','8891'))
ORIGIN=f'http://127.0.0.1:{PORT}';URL=ORIGIN+'/shark-attack-test/';LIVE=ORIGIN+'/shark-attack/';passes=0;fails=[]
def check(c,m):
  global passes
  if c: passes+=1;print('PASS',m)
  else: fails.append(m);print('FAIL',m)
WEB=tempfile.mkdtemp(prefix='sa-upd-');TD=os.path.join(WEB,'shark-attack-test')
subprocess.check_call([sys.executable,os.path.join(ROOT,'tools/make_test_build.py'),'--worktree','--out',TD,'--build','b1','7'],stdout=subprocess.DEVNULL)
os.makedirs(os.path.join(WEB,'shark-attack'))
for f in ['index.html','game.js','sw.js','manifest.webmanifest','version.json']:shutil.copy(os.path.join(ROOT,f),os.path.join(WEB,'shark-attack',f))
for d in ['icons','audio','art']:shutil.copytree(os.path.join(ROOT,d),os.path.join(WEB,'shark-attack',d))
def set_build(b,marker=None):
  open(os.path.join(TD,'version.json'),'w').write(json.dumps({"build":b}))
  p=os.path.join(TD,'index.html');s=open(p).read();s=re.sub(r'<meta name="build" content="[^"]*">',f'<meta name="build" content="{b}">',s);open(p,'w').write(s)
  if marker:open(os.path.join(TD,'game.js'),'a').write(f'\nwindow.__saCode="{marker}";\n')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=WEB,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2.6,has_touch=True,is_mobile=True,bypass_csp=True)
  outside=[];reqs=[];errs=[];navs=[]
  def onreq(r):
    reqs.append(r.url)
    if not r.url.startswith(ORIGIN) and not r.url.startswith('data:') and not r.url.startswith('blob:'):outside.append(r.url)
  cx.on('request',onreq)
  pg=cx.new_page();ev=pg.evaluate
  pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.on('framenavigated',lambda f:f==pg.main_frame and navs.append(f.url))
  keys=lambda:ev('caches.keys()')
  def launch():
    pg.goto(URL);pg.wait_for_function('document.readyState==="complete"');pg.wait_for_timeout(300)
  def play():
    pg.click('#tap');pg.wait_for_function('window.__saTitleDone===true',timeout=8000);pg.click('#start');pg.wait_for_timeout(200);pg.click('.pick[data-type=white]');pg.wait_for_timeout(300);ev('__sa.god=true;__sa.timeLeft=999')
  def upd_shown():return ev('!document.getElementById("upd").classList.contains("hide")')
  # 1) install
  launch();pg.wait_for_function('navigator.serviceWorker.controller||navigator.serviceWorker.ready.then(()=>true)',timeout=8000)
  pg.wait_for_function('caches.keys().then(k=>k.includes("sa-test-b1"))',timeout=10000)
  reg=ev('navigator.serviceWorker.getRegistration().then(r=>r&&r.scope)')
  check(reg==URL,f'SW scope is {reg}')
  check(ev('document.title')=='Shark Attack TEST' and 'TEST v7' in ev('document.getElementById("testTag").textContent'),'title "Shark Attack TEST" + "TEST v7" label')
  check(ev('fetch("manifest.webmanifest").then(r=>r.json()).then(m=>m.name+"|"+m.short_name+"|"+m.id)')=='Shark Attack TEST|SA TEST|/shark-attack-test/','manifest name/short_name/id')
  n=ev('caches.open("sa-test-b1").then(c=>c.keys()).then(k=>k.length)');check(n==10,f"installed cache sa-test-b1 holds all 10 files ({n})")
  check(not any(k.startswith('sharkattack-') for k in keys()) and not ev('Object.keys(localStorage).some(k=>k.startsWith("sharkAttack_"))'),'no live cache or storage names used by TEST')
  check(not ev('caches.open("sa-test-b1").then(c=>c.keys()).then(k=>k.some(r=>r.url.includes("version.json")))'),'version.json never cached')
  pg.reload();pg.wait_for_function('navigator.serviceWorker.controller!==null',timeout=8000);pg.wait_for_timeout(300)
  check(not upd_shown(),'first install: no "Updated!" note')
  # 2) offline reload plays
  cx.set_offline(True);n0=len(reqs);pg.reload();pg.wait_for_timeout(400);play();pg.wait_for_timeout(800)
  check(ev('__sa.state')=='play' and ev('__sa.BUILD')=='b1','offline reload starts and plays (build b1)')
  # 3) simulated update
  cx.set_offline(False);set_build('b2','b2');launch()
  check(ev('__sa.BUILD')=='b1' and ev('window.__saCode||""')=='','online launch with a new build on the server still runs the cached b1')
  play();ev('window.__keep=1');nv=len(navs);t0=time.time();ok=False;st=[]
  while time.time()-t0<15:
    st.append(ev('__sa.state'));
    if 'sa-test-b2' in keys() and ev('caches.open("sa-test-b2").then(c=>c.keys()).then(k=>k.length)')==10:ok=True;break
    pg.wait_for_timeout(200)
  pg.wait_for_timeout(500)
  print('  meta:',ev('caches.open("sa-test-meta").then(c=>c.match("meta")).then(r=>r.text())'))
  check(ok,'new build b2 downloaded in the background into sa-test-b2')
  check(len(navs)==nv and ev('window.__keep')==1 and all(s=='play' for s in st) and ev('__sa.state')=='play','play not interrupted during the download (no reload, still in play)')
  check('sa-test-b1' in keys() and ev('__sa.BUILD')=='b1','old cache kept until next launch')
  launch()
  check(ev('__sa.BUILD')=='b2' and ev('window.__saCode')=='b2','next launch runs b2')
  check(upd_shown(),'"Updated!" shown on first b2 launch');pg.wait_for_timeout(2300);check(not upd_shown(),'"Updated!" gone after 2 s')
  pg.wait_for_timeout(300);k=keys();check('sa-test-b1' not in k and 'sa-test-b2' in k,f'old cache removed ({k})')
  launch();check(not upd_shown(),'"Updated!" shown only once')
  # 4) failed partial update keeps b2
  set_build('b3','b3');os.rename(os.path.join(TD,'audio/play-swim-piano.ogg'),os.path.join(WEB,'hidden.ogg'))
  launch();pg.wait_for_timeout(2500);launch();pg.wait_for_timeout(1500)
  k=keys();check('sa-test-b3' not in k and ev('__sa.BUILD')=='b2' and ev('window.__saCode')=='b2' and not upd_shown(),f'partial download (1 file 404) never replaces b2 ({k})')
  cx.set_offline(True);pg.reload();pg.wait_for_timeout(400);play();pg.wait_for_timeout(500)
  check(ev('__sa.state')=='play' and ev('__sa.BUILD')=='b2','still plays offline on b2 after the failed update')
  os.rename(os.path.join(WEB,'hidden.ogg'),os.path.join(TD,'audio/play-swim-piano.ogg'));cx.set_offline(False)
  # 5) offline: zero network
  cx.set_offline(True);seen=[];h=lambda r:seen.append(r.url);srvlog_before=len(reqs);pg.reload();pg.wait_for_timeout(1500)
  check(ev('__sa.BUILD')=='b2','offline launch served from cache');cx.set_offline(False)
  # 5b) TEST manifest is fullscreen-ready; every SHELL file sits in the offline cache; game starts from the cache with the network off
  import json as _j,re as _re;mf=_j.load(open(os.path.join(TD,'manifest.webmanifest')))
  check(mf.get('display')=='fullscreen' and mf.get('display_override')==['fullscreen','standalone'] and mf.get('orientation')=='landscape' and mf.get('id')=='/shark-attack-test/' and len(mf.get('icons',[]))>=3,f"TEST manifest: fullscreen + display_override, landscape, id, icons ({mf.get('display')},{mf.get('display_override')})")
  ih=open(os.path.join(TD,'index.html')).read();check('apple-mobile-web-app-capable' in ih and 'viewport-fit=cover' in ih,'index.html: apple-mobile-web-app-capable + viewport-fit=cover')
  shell=_j.loads(_re.search(r'const SHELL=(\[.*?\]);',open(os.path.join(TD,'sw.js')).read()).group(1))
  miss=ev('async(sh)=>{const ks=await caches.keys(),out=[];for(const u of sh){let ok=false;for(const k of ks){const c=await caches.open(k);if(await c.match(u,{ignoreSearch:true})){ok=true;break}}if(!ok)out.push(u)}return out}',shell)
  check(len(shell)>=9 and not miss,f'every SHELL file is in the offline cache ({len(shell)} files, missing {miss})')
  cx.set_offline(True);pg.reload();pg.wait_for_timeout(400);play();pg.wait_for_timeout(600);check(ev('__sa.state')=='play','game starts offline from the cache');cx.set_offline(False)
  # 6) live game separate
  pg2=cx.new_page();pg2.goto(LIVE);pg2.wait_for_function('caches.keys().then(k=>k.includes("sharkattack-v8"))',timeout=10000);pg2.wait_for_timeout(500)
  r2=pg2.evaluate('navigator.serviceWorker.getRegistration().then(r=>r&&r.scope)');k=keys()
  check(r2==LIVE and ('sa-test-b2' in k or 'sa-test-b3' in k),f'live game has its own scope {r2}; TEST caches untouched {k}')
  pg2.close();launch();check(ev('__sa.BUILD')in('b2','b3') and ev('localStorage.getItem("saTEST_build")')==ev('__sa.BUILD'),'TEST still runs after live SW activated; own storage key')
  check(not outside,f'no outside requests {outside[:3]}')
  check(not errs,f'no console errors {errs[:3]}')
  # 6) install button (like Dino Colossus): repo manifest fullscreen; button + apple-touch-icon present in a browser tab; hidden when installed
  rm=json.load(open(os.path.join(ROOT,'manifest.webmanifest'))) if 'json' in dir() else __import__('json').load(open(os.path.join(ROOT,'manifest.webmanifest')))
  check(rm.get('display')=='fullscreen' and rm.get('display_override')==['fullscreen','standalone'] and rm.get('orientation')=='landscape','repo manifest: display fullscreen + display_override, landscape')
  for mode,want in [(None,True),('standalone',False),('fullscreen',False)]:
    c2=b.new_context(viewport={'width':915,'height':412},has_touch=True,is_mobile=True,bypass_csp=True)
    if mode: c2.add_init_script("(()=>{const o=matchMedia.bind(window);window.matchMedia=q=>q.includes('display-mode: %s')?{matches:true,media:q,addEventListener(){},removeEventListener(){},addListener(){},removeListener(){}}:o(q)})()"%mode)
    p2=c2.new_page();p2.goto(URL);p2.wait_for_timeout(300);p2.click('#tap');p2.wait_for_timeout(750)
    vis=p2.evaluate("(()=>{const b=document.getElementById('instb');return !!b&&getComputedStyle(b).display!=='none'&&!b.classList.contains('hide')})()")
    if mode is None:
      ati=p2.evaluate("!!document.querySelector('link[rel=apple-touch-icon]')&&!!document.querySelector('meta[name=apple-mobile-web-app-capable]')")
      p2.click('#instb');p2.wait_for_timeout(100);hint=p2.evaluate("document.getElementById('insth').textContent")
      check(ati and 'Install' in hint,f'browser tab: apple-touch-icon + capable meta; Install button with no prompt shows the hint ("{hint}")')
    check(vis==want,f'Install button {"shown" if want else "hidden"} when display-mode is {mode or "browser"}')
    c2.close()
  b.close()
finally:
 srv.terminate();shutil.rmtree(WEB,ignore_errors=True)
print(f'\n{passes} passed, {len(fails)} failed');sys.exit(1 if fails else 0)
