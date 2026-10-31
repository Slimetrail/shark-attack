# b46 tests: intro circles the title twice (behind + in front, mouth open); sound unlocks with Chrome's REAL autoplay rule (finger-DOWN is not a gesture; finger-UP/click is).
# Run: python3 tests/test_b46.py  (ports 8897/8898). Pass 1: service worker blocked. Pass 2: served copy with the service worker in control.
import os,sys,subprocess,time,shutil,tempfile
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=8897;PORT2=8898;passes=0;fails=[]
def check(c,m):
  global passes
  if c: passes+=1;print('PASS',m)
  else: fails.append(m);print('FAIL',m)
TMP=tempfile.mkdtemp(prefix='sa-b46-');APP=os.path.join(TMP,'app')
shutil.copytree(ROOT,APP,ignore=shutil.ignore_patterns('.git','tests','tools','V9C-NOTES.txt','title-art-crop-preview.png'))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
srv2=subprocess.Popen([sys.executable,'-m','http.server',str(PORT2),'--bind','127.0.0.1'],cwd=APP,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
ST='({ac:AC?AC.state:"none",paused:music.title?music.title.paused:null,t:music.title?music.title.currentTime:-1,chip:!!chip.src,state:state,cur:music.cur===music.title})'
def tapc(pg,sel):
  bb=pg.locator(sel).first.bounding_box();pg.touchscreen.tap(bb['x']+bb['width']/2,bb['y']+bb['height']/2)
def run(b,url,sw,tag):
  cx=b.new_context(viewport={'width':915,'height':412},has_touch=True,is_mobile=True,bypass_csp=True,service_workers='allow' if sw else 'block')
  pg=cx.new_page();pg.goto(url)
  if sw:
    pg.wait_for_function('navigator.serviceWorker.controller!==null',timeout=15000);pg.reload()
    check(pg.evaluate('!!navigator.serviceWorker.controller'),f'{tag}: page controlled by the service worker')
  pg.wait_for_timeout(500)
  pg.touchscreen.tap(457,206);pg.wait_for_timeout(1500);s=pg.evaluate(ST);print(tag,'after tap',s)
  check(s['ac']=='running',f'{tag}: AudioContext running after Tap to start')
  check(s['paused'] is False and s['t']>0.3,f'{tag}: intro music plays after Tap to start')
  t1=s['t'];pg.wait_for_timeout(800);t2=pg.evaluate(ST)['t'];check(t2>t1+0.4,f'{tag}: intro music time advances {t1:.2f}->{t2:.2f}')
  pg.wait_for_timeout(700);pg.touchscreen.tap(20,380);pg.wait_for_timeout(400);t3=pg.evaluate(ST)['t'];check(t3>t2,f'{tag}: a second tap does not restart the intro ({t2:.2f}->{t3:.2f})')
  pg.wait_for_selector('#start',state='visible',timeout=60000);pg.wait_for_timeout(700);tapc(pg,'#start');pg.wait_for_timeout(500)
  check(pg.is_visible('#pickUi'),f'{tag}: Start opens the shark picker')
  tapc(pg,'#pickUi button.pick');pg.wait_for_timeout(2500);s=pg.evaluate(ST);print(tag,'after pick',s)
  check(s['state']=='play' and s['chip'] and s['ac']=='running',f'{tag}: gameplay song starts with AudioContext running')
  check(s['paused'] is True or not s['cur'],f'{tag}: intro music not playing during the game')
  pg.evaluate('document.getElementById("home").click()');pg.wait_for_timeout(1500);s=pg.evaluate(ST)
  check(s['state']=='title' and s['paused'] is False and not s['chip'],f'{tag}: back to home plays the title music again {s}')
  cx.close()
def run_fresh_start(b,url):
  # fresh load where only a click (no prior unlock) reaches the game: gameplay song still starts
  cx=b.new_context(viewport={'width':915,'height':412},has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');pg=cx.new_page();pg.goto(url);pg.wait_for_timeout(400)
  pg.evaluate('document.getElementById("tap").classList.add("hide");startTitle();document.getElementById("titleUi").classList.remove("hide")')
  pg.wait_for_timeout(300);check(pg.evaluate('AC?AC.state:"none"')!='running','fresh: no sound before any tap')
  pg.wait_for_selector('#start',state='visible',timeout=60000);pg.wait_for_timeout(700);tapc(pg,'#start');pg.wait_for_timeout(400);tapc(pg,'#pickUi button.pick');pg.wait_for_timeout(2500);s=pg.evaluate(ST)
  check(s['state']=='play' and s['chip'] and s['ac']=='running',f'fresh: gameplay song starts from a click-only path {s}');cx.close()
def run_mute(b,url):
  cx=b.new_context(viewport={'width':915,'height':412},has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');pg=cx.new_page();pg.goto(url)
  pg.evaluate('localStorage.setItem("sharkAttack_sound","0")');pg.goto(url);pg.wait_for_timeout(400)
  pg.touchscreen.tap(457,206);pg.wait_for_timeout(1200);pg.touchscreen.tap(20,380);pg.wait_for_timeout(600);s=pg.evaluate(ST)
  check(s['paused'] is not False,f'mute: sound off -> intro music stays silent after taps {s}')
  pg.wait_for_selector('#start',state='visible',timeout=60000);pg.wait_for_timeout(700);tapc(pg,'#start');pg.wait_for_timeout(400);tapc(pg,'#pickUi button.pick');pg.wait_for_timeout(1500);s=pg.evaluate(ST)
  check(s['paused'] is not False,f'mute: no intro music during the game {s}');cx.close()
def run_intro(b,url):
  cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,bypass_csp=True,service_workers='block');pg=cx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script('window.__saTitleLog=1');pg.goto(url);pg.wait_for_timeout(400);pg.click('#tap');c0=pg.evaluate('__sa.sfxCount.chomp')
  pg.wait_for_function('window.__saTitleDone===true',timeout=20000);log=pg.evaluate('__sa.titleLog');pg.wait_for_timeout(500)
  laps=lambda ly,k:[x for x in log if x[1]==ly and x[2]==k]
  for k in (1,2):
    for ly in ('behind','front'): check(len(laps(ly,k))>5,f'intro lap {k}: shark drawn {ly} the title ({len(laps(ly,k))} frames)')
  seq=[];[seq.append((x[1],x[2])) for x in log if not seq or seq[-1]!=(x[1],x[2])]
  check(seq[:5]==[('behind',0),('behind',1),('front',1),('behind',2),('front',2)],f'intro order: in behind, then behind/front x2 {seq[:6]}')
  check(all(x[3] for x in log),'intro: open-mouth (teeth) sprite used on every frame')
  check(not pg.evaluate('__sa.titleTorn') and pg.evaluate('__sa.sfxCount.chomp')==c0,'intro: never bites, tears or chomps')
  check(pg.evaluate('__sa.TITLE.SWIM')<=20 and pg.evaluate('__sa.titleArt')==0,'intro under 20 s, ends on the blue-sea title')
  check(not errs,f'intro: no page errors {errs}');cx.close()
try:
  with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=document-user-activation-required'])
    run_intro(b,f'http://127.0.0.1:{PORT}/')
    run(b,f'http://127.0.0.1:{PORT}/',False,'no-SW')
    run_mute(b,f'http://127.0.0.1:{PORT}/')
    run_fresh_start(b,f'http://127.0.0.1:{PORT}/')
    run(b,f'http://127.0.0.1:{PORT2}/',True,'SW')
    b.close()
finally:
  srv.kill();srv2.kill();shutil.rmtree(TMP,ignore_errors=True)
print(f'{passes} passed, {len(fails)} failed');[print(' -',f) for f in fails];sys.exit(1 if fails else 0)
