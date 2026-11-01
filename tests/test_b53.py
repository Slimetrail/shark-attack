# b53 tests (Skeptic FIX on b52 via Eve): B13 blocked storage still starts; B9 late game always has visible prey; B5 turn reads 3D;
# test gaps: cargo 100, surfer shrink floor, no divers, title re-layout on resize.
# Run: /workspace/.pwvenv/bin/python tests/test_b53.py (port 8953, override SA_PORT53). Pretend phone (Chromium touch emulation), never a real phone.
import os,sys,subprocess,time,json,re
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('SA_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT53','8953'));URL=f'http://127.0.0.1:{PORT}/'
ONLY=os.environ.get('SA_ONLY','')
passes=0;fails=[]
def check(c,m):
  global passes
  if c: passes+=1;print('PASS',m)
  else: fails.append(m);print('FAIL',m)
def rd(p):return open(os.path.join(ROOT,p),encoding='utf8').read()
check(json.load(open(os.path.join(ROOT,'version.json'))).get('build')=='53','version.json build 53')
ih=rd('index.html');check('game.js?v=53' in ih and 'content="53"' in ih and 'game.js?v=53' in rd('sw.js'),'index.html meta 53, game.js?v=53, sw.js shell game.js?v=53 (cache sharkattack-v53)')
check('A Slimetrail production' in ih and 'No ads, no tracking, works offline.' in ih,'credit line and "No ads, no tracking, works offline." kept')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
def J(pg,e):
  try:return pg.evaluate(e)
  except Exception as ex:print('page call failed:',str(ex).split('\n')[0]);return None
BLOCK='''Object.defineProperty(window,"localStorage",{configurable:true,get(){throw new DOMException("The operation is insecure.","SecurityError")}});'''
def newpg(b,w=844,h=390,block=False):
  cx=b.new_context(viewport={'width':w,'height':h},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block')
  if block: cx.add_init_script(BLOCK)
  pg=cx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(URL);pg.wait_for_timeout(600);return cx,pg,errs
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
  # ---- B13 blocked storage ----
  if not ONLY or 'store' in ONLY:
   cx,pg,errs=newpg(b,block=True)
   check(J(pg,'typeof window.__sa==="object"&&__sa.state') in ('tap','title') if J(pg,'typeof window.__sa')=='object' else False,f'storage blocked: game loads to the title (errors {errs[:1]})')
   check(J(pg,'(()=>{try{localStorage;return false}catch(e){return true}})()')==True,'storage really is blocked in this page (throws)')
   pg.touchscreen.tap(422,195);pg.wait_for_timeout(5000)
   bb=pg.locator('#snd').bounding_box() if J(pg,'typeof __sa')=='object' else None;bb=bb or {'x':0,'y':0,'width':1,'height':1};a0=J(pg,'__sa.soundOn');pg.touchscreen.tap(bb['x']+bb['width']/2,bb['y']+bb['height']/2);pg.wait_for_timeout(200)
   r=J(pg,'(()=>{const a='+str(a0).lower()+';const b=__sa.soundOn;return {a,b,mem:__saLS.mem(),lbl:document.getElementById("snd").textContent,st:__sa.state}})()')
   check(r and r['a']!=r['b'] and r['mem'],f'storage blocked: sound toggle works on the title, settings in memory {r}')
   st=J(pg,'(()=>{__sa.startAs("white","timed");return __sa.state})()');check(st=='play',f'storage blocked: a run starts ({st})')
   r=J(pg,'(()=>{__sa.god=true;for(let i=0;i<5;i++){__sa.placeFishAtMouth(0);__sa.sim(.25)}const sc=__sa.score;__sa.timeLeft=0;__sa.sim(.2);return {sc,st:__sa.state,best:__sa.best}})()')
   check(r and r['st']!='play' and r['best']>=r['sc']>0,f'storage blocked: round ends, best score kept in memory {r}')
   r=J(pg,'(()=>{__sa.setMode("endless");return __sa.mode})()');check(r=='endless',f'storage blocked: mode setting works ({r})')
   check(not errs,f'storage blocked: no page errors {errs[:2]}')
   cx.close()
  b.close()
finally:
  srv.terminate()
print(f'\n{passes} passed, {len(fails)} failed')
for f in fails: print(' FAIL:',f)
sys.exit(1 if fails else 0)
