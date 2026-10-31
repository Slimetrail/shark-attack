# b48/b49 update-path test (Skeptic, c0fbb57): a phone on the LIVE build (47, commit 040bcbb, offline worker running, saved settings) must be offered the new build,
# move to it after the "update ready" tap, keep its saved settings, and still work offline afterwards.
# The "live" files are a git archive of 040bcbb; the "new" files are a git archive of the commit being checked (HEAD of this repo). Served from one local port (same
# origin, so the worker and localStorage carry over, like the real site). Pretend phone (Chromium with touch), never a real phone.
# Run: python3 tests/test_b48update.py   (port 8902; NEW_REF env var = commit to test, default HEAD; LIVE_REF default 040bcbb)
import os,sys,subprocess,tempfile,threading,http.server,functools,json,time,tarfile,io
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT48U','8902'));URL=f'http://127.0.0.1:{PORT}/'
NEW_REF=os.environ.get('NEW_REF','HEAD');LIVE_REF=os.environ.get('LIVE_REF','040bcbb')
passes=0;fails=[]
def check(c,m):
  global passes
  if c: passes+=1;print('PASS',m)
  else: fails.append(m);print('FAIL',m)
TMP=tempfile.mkdtemp(prefix='sa-b48u-')
def archive(ref,name):
  d=os.path.join(TMP,name);os.makedirs(d);data=subprocess.check_output(['git','-C',ROOT,'archive',ref]);tarfile.open(fileobj=io.BytesIO(data)).extractall(d,filter="data");return d
LIVE=archive(LIVE_REF,'live');NEW=archive(NEW_REF,'new');cur={'d':LIVE}
class H(http.server.SimpleHTTPRequestHandler):
  def translate_path(self,path):
    self.directory=cur['d'];return super().translate_path(path)
  def log_message(self,*a):pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',PORT),H);threading.Thread(target=srv.serve_forever,daemon=True).start()
lv=json.load(open(os.path.join(LIVE,'version.json')))['build'];nv=json.load(open(os.path.join(NEW,'version.json')))['build']
check(lv!=nv,f'live build {lv} differs from new build {nv} (the worker decides by version.json)')
SET={'sharkAttack_best':'1234','sharkAttack_sound':'0','sharkAttack_songs':'0','sharkAttack_sfx':'0','sharkAttack_calm':'1','sharkAttack_type':'hammer','sharkAttack_mode':'endless'}
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--autoplay-policy=document-user-activation-required'])
  cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True);pg=cx.new_page()
  errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(URL);pg.evaluate('navigator.serviceWorker.ready.then(()=>1)');pg.wait_for_timeout(2500)
  pg.reload();pg.wait_for_timeout(1500)
  keys=pg.evaluate('caches.keys()');ctl=pg.evaluate('!!navigator.serviceWorker.controller')
  check(ctl and f'sharkattack-v{lv}' in keys,f'phone on live build {lv}: offline worker is running and in control, cache {sorted(keys)}')
  pg.evaluate('s=>{for(const k in s)localStorage.setItem(k,s[k])}',SET)
  g0=pg.evaluate("fetch('game.js?v='+%s).then(r=>r.text())"%lv)
  check('tapArmed' not in g0,'phone is running the old game code (no finger-up fix yet)')
  cur['d']=NEW   # publish the new build
  pg.reload();pg.wait_for_timeout(1000)
  for i in range(60):
    keys=pg.evaluate('caches.keys()')
    if f'sharkattack-v{nv}' in keys:break
    pg.wait_for_timeout(500)
  check(f'sharkattack-v{nv}' in keys,f'new build {nv} was downloaded in the background (all files) while the old one kept running {sorted(keys)}')
  g1=pg.evaluate("fetch('game.js?v='+%s).then(r=>r.text())"%lv)
  check(g1==open(os.path.join(LIVE,'game.js')).read(),'until the player taps "update", the phone still runs the old build (never switched mid-play)')
  pg.click('#tap');pg.wait_for_timeout(1500)
  for i in range(20):
    vis=pg.evaluate('()=>[...document.querySelectorAll("#updr,#updb")].filter(e=>!e.classList.contains("hide")&&/Update ready/.test(e.textContent)).map(e=>e.id)')
    if vis:break
    pg.wait_for_timeout(500)
  check(bool(vis),f'phone shows "Update ready" on the title screen {vis}')
  pg.click('#'+vis[0]);pg.wait_for_timeout(6000)
  vj=pg.evaluate("fetch('version.json').then(r=>r.json())");keys=pg.evaluate('caches.keys()')
  g2=pg.evaluate("fetch('game.js?v='+%s).then(r=>r.text())"%nv);h2=pg.evaluate("fetch('index.html').then(r=>r.text())")
  check(str(vj['build'])==str(nv) and g2==open(os.path.join(NEW,'game.js')).read() and h2==open(os.path.join(NEW,'index.html')).read(),f'after the tap the phone runs the new build (version.json {vj}, new game.js and index.html match the new build)')
  check(f'sharkattack-v{lv}' not in keys and f'sharkattack-v{nv}' in keys,f'old cache removed, new cache kept {sorted(keys)}')
  got=pg.evaluate('s=>Object.fromEntries(Object.keys(s).map(k=>[k,localStorage.getItem(k)]))',SET)
  check(got==SET,f'saved settings and best score kept {got}')
  cx.set_offline(True);pg.reload();pg.wait_for_timeout(1500)
  st=pg.evaluate('()=>({state:__sa.state,code:typeof startTitle})');g3=pg.evaluate("fetch('game.js?v='+%s).then(r=>r.text())"%nv)
  check(st['state']=='tap' and 'tapArmed' in g3,f'new build starts and runs fully offline {st}')
  check(not errs,f'no page errors {errs[:2]}')
finally: srv.shutdown()
print(f'{passes} passed, {len(fails)} failed')
for f in fails: print('FAILED:',f)
sys.exit(1 if fails else 0)
