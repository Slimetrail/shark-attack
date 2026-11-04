# b49 test (Jeremy's card t1310s5174): the Shark credit line is exactly "A Slimetrail production"; the old wording "Slimetrail Productions" is gone from the screen.
# Only text and the build number changed. Run: python3 tests/test_b49.py (port 8902). Pretend phone (Chromium touch emulation), never a real phone.
import os,sys,subprocess,time,json,re
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT49','8902'));URL=f'http://127.0.0.1:{PORT}/';passes=0;fails=[]
def check(c,m):
  global passes
  if c: passes+=1;print('PASS',m)
  else: fails.append(m);print('FAIL',m)
rd=lambda f:open(os.path.join(ROOT,f)).read()
check(json.loads(rd('version.json'))['build']=="56",'version.json says build 56')
check('<meta name="build" content="56">' in rd('index.html') and 'game.js?v=56' in rd('index.html') and 'game.js?v=56' in rd('sw.js'),'index.html and sw.js name build 56 (cache name follows version.json)')
check('v=50' not in rd('index.html')+rd('sw.js'),'no leftover build 50 file names in index.html or sw.js')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
  cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');pg=cx.new_page()
  errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(URL);pg.wait_for_timeout(500)
  pg.touchscreen.tap(457,206);pg.wait_for_timeout(1500)
  pg.evaluate('document.getElementById("cred").click()');pg.wait_for_timeout(300)
  vis=pg.evaluate('!document.getElementById("credUi").classList.contains("hide")')
  txt=pg.evaluate('document.getElementById("credUi").innerText')
  check(vis,'Credits screen opens')
  check(txt.count('A Slimetrail production')==1,'Credits screen shows "A Slimetrail production" exactly once')
  check('Slimetrail Productions' not in txt,'old wording "Slimetrail Productions" is not on the Credits screen')
  check('No ads, no tracking, works offline.' in txt,'"No ads, no tracking, works offline." is still shown')
  check('original, made for this game' in txt and 'VSCO-2' in txt,'own-work and piano licence lines are still shown')
  big=pg.evaluate('(()=>{const e=[...document.querySelectorAll("#credUi p")].find(x=>x.innerText.trim()==="A Slimetrail production");return !!e&&e.innerText.trim()==="A Slimetrail production"})()')
  check(big,'the credit line is exactly "A Slimetrail production" with nothing added')
  check(not errs,f'no page errors {errs}')
  b.close()
finally: srv.terminate()
print(f'{passes} passed, {len(fails)} failed');sys.exit(1 if fails else 0)
