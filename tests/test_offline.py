# v7-fs: fullscreen install bits + offline start from the service-worker cache. Run: python3 tests/test_offline.py (port 8871)
import os,sys,subprocess,time,json,re
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORTO','8871'));URL=f'http://127.0.0.1:{PORT}/';passes=0;fails=[]
def check(c,m):
  global passes
  if c: passes+=1;print('PASS',m)
  else: fails.append(m);print('FAIL',m)
m=json.load(open(os.path.join(ROOT,'manifest.webmanifest')))
check(m.get('display')=='fullscreen' and m.get('display_override')==['fullscreen','standalone'] and m.get('orientation')=='landscape','manifest fullscreen + display_override + landscape')
ih=open(os.path.join(ROOT,'index.html')).read()
check('apple-touch-icon' in ih and 'apple-mobile-web-app-capable' in ih and 'id="instb"' in ih,'index: apple-touch-icon, capable meta, Install button')
shell=json.loads(re.search(r'const SHELL=(\[.*?\]);',open(os.path.join(ROOT,'sw.js')).read()).group(1))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();cx=b.new_context(viewport={'width':915,'height':412},has_touch=True,is_mobile=True,bypass_csp=True);pg=cx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(URL);pg.wait_for_function('navigator.serviceWorker.controller||false',timeout=15000) if False else pg.wait_for_timeout(300)
  pg.evaluate('navigator.serviceWorker.ready');pg.wait_for_timeout(2500)
  miss=pg.evaluate('async(sh)=>{const ks=await caches.keys(),o=[];for(const u of sh){let ok=false;for(const k of ks)if(await (await caches.open(k)).match(u,{ignoreSearch:true})){ok=true;break}if(!ok)o.push(u)}return o}',shell)
  check(not miss,f'every SHELL file cached ({len(shell)}, missing {miss})')
  cx.set_offline(True);pg.reload();pg.wait_for_timeout(500);pg.click('#tap');pg.wait_for_timeout(600);pg.click('#start');pg.wait_for_timeout(300);pg.click('.pick');pg.wait_for_timeout(600)
  check(pg.evaluate('__sa.state')=='play','game starts offline from the cache')
  check(not errs,f'no page errors {errs[:2]}');b.close()
finally: srv.terminate()
print(f'\n{passes} passed, {len(fails)} failed');sys.exit(1 if fails else 0)
