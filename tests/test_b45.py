# b45 tests: ghost-click fix (Tap to start must not press Start), "Sound is off" hint, corner "Update ready - tap to reload" button.
# Run: python3 tests/test_b45.py  (ports 8895/8896). Screenshots -> /workspace/intro-shots/shark-b45
import os,sys,subprocess,time,json,shutil,tempfile,re
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=8895;PORT2=8896
URL=f'http://127.0.0.1:{PORT}/';URL2=f'http://127.0.0.1:{PORT2}/';SHOTS=os.environ.get('SA_B45_SHOTS','/workspace/intro-shots/shark-b45');os.makedirs(SHOTS,exist_ok=True);passes=0;fails=[]
def check(c,m):
  global passes
  if c: passes+=1;print('PASS',m)
  else: fails.append(m);print('FAIL',m)
TMP=tempfile.mkdtemp(prefix='sa-b45-');APP=os.path.join(TMP,'app')
shutil.copytree(ROOT,APP,ignore=shutil.ignore_patterns('.git','tests','tools','V9C-NOTES.txt','title-art-crop-preview.png'))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
srv2=subprocess.Popen([sys.executable,'-m','http.server',str(PORT2),'--bind','127.0.0.1'],cwd=APP,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
html=open(os.path.join(ROOT,'index.html')).read()
check('A Slimetrail production' in html and 'SlimeTrail' not in html and 'Game, music and sound effects' not in html,'credits: one line "A Slimetrail production"')
check('"build":"47"' in open(os.path.join(ROOT,'version.json')).read() and 'content="47"' in html and 'game.js?v=47' in html,'build 47')
def ctx(b,**k): return b.new_context(viewport={'width':915,'height':412},device_scale_factor=2.6,has_touch=True,is_mobile=True,service_workers='block',bypass_csp=True,**k)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
  errs=[]
  def page(cx):
    pg=cx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));return pg
  cx=ctx(b);pg=page(cx)
  # 1 tap at the screen centre (where Start sits) must not press Start
  for tag,pt in [('centre',(457,206)),('start button',None),('lower left',(200,330))]:
    pg.goto(URL);pg.wait_for_timeout(300)
    if pt is None:
      pg.evaluate('document.getElementById("titleUi").classList.remove("hide")');bb=pg.locator('#start').bounding_box();pg.evaluate('document.getElementById("titleUi").classList.add("hide")');pt=(bb['x']+bb['width']/2,bb['y']+bb['height']/2)
    if tag=='centre': pg.screenshot(path=f'{SHOTS}/01-tap-to-start.png')
    pg.touchscreen.tap(*pt);pg.wait_for_timeout(1000)
    check(pg.evaluate('__sa.state')=='title' and not pg.evaluate('window.__saTitleDone') and pg.evaluate('__sa.titleShark')!=None,f'tap at {tag} {tuple(round(v) for v in pt)}: still on the title after 1 s, intro runs')
  check(pg.evaluate('__sa.titleMusicPlaying') or not pg.evaluate('__sa.musOn'),'tap still unlocks audio (intro music playing)')
  # 2 deliberate Start tap after 1 s still works
  pg.touchscreen.tap(*[v for v in (pg.locator('#start').bounding_box()['x']+60,pg.locator('#start').bounding_box()['y']+20)]);pg.wait_for_timeout(400)
  check(pg.evaluate('__sa.state')=='pick','a real Start tap after 1 s opens the shark pick')
  # 3 slow press (down, 300 ms hold, up) in the centre with a mouse-like pointer
  pg.goto(URL);pg.wait_for_timeout(300);pg.mouse.move(457,206);pg.mouse.down();pg.wait_for_timeout(300);pg.mouse.up();pg.wait_for_timeout(700)
  check(pg.evaluate('__sa.state')=='title' and not pg.evaluate('window.__saTitleDone'),'slow press (300 ms hold) in the centre: intro keeps playing')
  pg.wait_for_function('window.__saTitleDone===true',timeout=9000);pg.click('#start');pg.wait_for_timeout(300);check(pg.evaluate('__sa.state')=='pick','Start works after the intro')
  # 4 hold longer than 600 ms then release over Start: still no ghost press
  pg.goto(URL);pg.wait_for_timeout(300);pg.mouse.move(457,206);pg.mouse.down();pg.wait_for_timeout(900);pg.mouse.up();pg.wait_for_timeout(300)
  check(pg.evaluate('__sa.state')=='title','long press (900 ms) on Tap to start: release does not press Start')
  # 5 Sound is off hint
  check(not pg.is_visible('#sndOff'),'sound on: no "Sound is off" hint')
  pg.evaluate('localStorage.setItem("sharkAttack_sound","0")');pg.goto(URL);pg.wait_for_timeout(300)
  check(pg.is_visible('#sndOff') and 'Sound is off' in pg.inner_text('#sndOff'),'saved sound off: "Sound is off" shows on Tap to start')
  pg.screenshot(path=f'{SHOTS}/02-sound-is-off.png')
  hb=pg.locator('#sndOff').bounding_box();check(hb and hb['height']>=18 and hb['y']+hb['height']<412,f'hint readable and on screen {hb}')
  pg.touchscreen.tap(457,206);pg.wait_for_timeout(300);check(pg.evaluate('localStorage.getItem("sharkAttack_sound")')=='0','tap does not change the saved sound setting')
  pg.evaluate('localStorage.setItem("sharkAttack_sound","1")');pg.goto(URL);pg.wait_for_timeout(300);check(not pg.is_visible('#sndOff'),'sound back on: hint hidden')
  cx.close()
  # 6 update button with a simulated newer build
  cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True);pg=page(cx)
  pg.goto(URL2);pg.wait_for_function('navigator.serviceWorker.controller!==null',timeout=15000);pg.wait_for_timeout(1500)
  check(not pg.is_visible('#updr'),'first install: no Update ready button')
  pg.reload();pg.wait_for_timeout(2000);check(not pg.is_visible('#updr'),'same build re-open: no Update ready button')
  open(os.path.join(APP,'version.json'),'w').write('{"build":"48"}')
  p_=os.path.join(APP,'index.html');s=open(p_).read().replace('<meta name="build" content="47">','<meta name="build" content="48">');open(p_,'w').write(s)
  pg.reload();pg.wait_for_selector('#updr',state='visible',timeout=40000)
  check(pg.evaluate('__saUpd.pending')=='48','button appears once build 48 is fully downloaded (pending)')
  bb=pg.locator('#updr').bounding_box();sb=pg.evaluate('(()=>{const r=document.getElementById("tap").getBoundingClientRect();return 1})()')
  check(bb and bb['x']+bb['width']>=900 and bb['y']<20 and bb['height']>=44,f'button in the top-right corner, tappable {bb}')
  pg.wait_for_timeout(1500);check(pg.evaluate('document.querySelector("meta[name=build]").content')=='47','never reloads by itself')
  pg.screenshot(path=f'{SHOTS}/03-update-ready.png')
  with pg.expect_navigation(timeout=10000): pg.click('#updr')
  pg.wait_for_timeout(800);check(pg.evaluate('document.querySelector("meta[name=build]").content')=='48','tap reloads into build 48 right away')
  pg.wait_for_timeout(1000);check(not pg.is_visible('#updr'),'after the update: button gone')
  cx.close()
  # 7 phones that never tap: next open still switches (build 49)
  cx=b.new_context(viewport={'width':915,'height':412},bypass_csp=True);pg=page(cx);pg.goto(URL2);pg.wait_for_function('navigator.serviceWorker.controller!==null',timeout=15000);pg.wait_for_timeout(1000)
  open(os.path.join(APP,'version.json'),'w').write('{"build":"49"}');s=open(p_).read().replace('content="48"','content="49"');open(p_,'w').write(s)
  pg.reload();pg.wait_for_function('__saUpd.pending==="49"',timeout=20000);pg.reload();pg.wait_for_timeout(800)
  check(pg.evaluate('document.querySelector("meta[name=build]").content')=='49','never tapped: the second open applies the new build as before')
  cx.close();b.close()
  check(not errs,f'no page errors {errs}')
finally: srv.kill();srv2.kill();shutil.rmtree(TMP,ignore_errors=True)
print(f'{passes} passed, {len(fails)} failed');sys.exit(1 if fails else 0)
