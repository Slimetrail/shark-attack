# b50 title test (Jeremy via Eve, 5:22 PM): the whole SHARK ATTACK title stays whole; the shark swims in behind it, faces the camera with open jaws around
# the title, snaps once, then HOLDS that pose until any title button is tapped; then it glides to the swim line and cruises. Calm / reduced motion: gentle fade-in.
# b51: the 640x360 'button covers title' check is a real check now (was marked KNOWN in build 50).
# Run: /workspace/.pwvenv/bin/python tests/test_b50title.py (port 8903). Pretend phone (Chromium touch emulation), never a real phone. Screenshots -> art-shots-b50/ (not committed).
import os,sys,subprocess,time
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT50T','8903'));URL=f'http://127.0.0.1:{PORT}/'
SHOTS=os.path.join(ROOT,'art-shots-b50');os.makedirs(SHOTS,exist_ok=True);passes=0;fails=[]
def check(c,m):
  global passes
  if c: passes+=1;print('PASS',m)
  else: fails.append(m);print('FAIL',m)
BTNS=['start','snd','songs','fx','calm','cred','updb']
def ctx(b,w,h,rm=None):
  kw=dict(viewport={'width':w,'height':h},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block')
  if rm: kw['reduced_motion']=rm
  return b.new_context(**kw)
def tap_start(pg,w,h):
  pg.goto(URL+'?portrait' if h>w else URL);pg.wait_for_timeout(500)
  if h>w:  # the game is landscape-only: portrait shows the "Turn your phone sideways" cover. Record that, then hide the cover so the title layout is still checked on a tall screen.
    pg.evaluate('window.__rotShown=getComputedStyle(document.getElementById("rot")).display!=="none";document.getElementById("rot").style.display="none"')
  pg.evaluate('window.__saTitleLog=1');pg.touchscreen.tap(w/2,h/2);pg.wait_for_timeout(100)
  pg.evaluate('document.getElementById("updb").classList.remove("hide")')   # show the update button too so its spot is checked
def real_tap(pg,sel):
  pg.wait_for_timeout(700);r=pg.evaluate(f'(()=>{{const b=document.querySelector("{sel}").getBoundingClientRect();return [b.x+b.width/2,b.y+b.height/2]}})()');pg.touchscreen.tap(r[0],r[1]);pg.wait_for_timeout(250)
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
  # (a)+(b) full sequence, ink never changes, pose held for 12 s
  cx=ctx(b,915,412);pg=cx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));tap_start(pg,915,412)
  ink0=pg.evaluate('__sa.titleInk()');inks=[];t0=time.time();shot=0
  while not pg.evaluate('window.__saTitleDone') and time.time()-t0<12:
    inks.append(pg.evaluate('__sa.titleInk()'))
    if time.time()-t0>shot*0.7: pg.screenshot(path=f'{SHOTS}/seq-{shot:02d}.png');shot+=1
    pg.wait_for_timeout(150)
  st=pg.evaluate('__sa.titlePose');log=pg.evaluate('__sa.titleLog')
  check(pg.evaluate('window.__saTitleDone') and st['pose'] and st['sr']['front'],f'pose reached (head-on, at {pg.evaluate("window.__saPose.since")} s)')
  check(any(e[1]=='behind' and not e[1]=='front' for e in log) and not any(e[1]=='front' for e in log),'shark only ever behind the words before the pose (never in front, never over letters)')
  check(any(e[1]=='snap' for e in log),'one jaw snap before the hold')
  check(pg.evaluate('__sa.titleBite') is None and not pg.evaluate('__sa.titleTorn') and pg.evaluate('__sa.titleFrags')==0,'no bite/tear/fragments')
  pg.screenshot(path=f'{SHOTS}/pose-915x412.png');s1=pg.evaluate('__sa.titleShark');pg.wait_for_timeout(12000);s2=pg.evaluate('__sa.titleShark')
  inks.append(pg.evaluate('__sa.titleInk()'))
  check(set(inks)=={ink0},f'title canvas ink never changes during the sequence and 12 s hold ({ink0}, {len(inks)} samples)')
  check(pg.evaluate('__sa.titlePose.pose') and s2['front'] and abs(s2['x']-s1['x'])<.5 and abs(s2['y']-s1['y'])<.5 and abs(s2['s']-s1['s'])<.02,f'after 12 s with no input the pose is still held, no drift ({s1["x"]:.1f},{s1["y"]:.1f}) -> ({s2["x"]:.1f},{s2["y"]:.1f})')
  pg.screenshot(path=f'{SHOTS}/pose-hold12s-915x412.png')
  # mouth around title: anchor centred on title
  r=pg.evaluate('__sa.titleRect');check(abs(s2['x']-(r['x']+r['w']/2))<1,'head-on shark centred on the title')
  # (c) every non-Start button releases; shark cruises
  for sel in ['#snd','#songs','#fx','#calm','#cred','#updb']:
    pg.evaluate('__sa.state')
    tap_start(pg,915,412);pg.wait_for_function('window.__saTitleDone===true',timeout=12000)
    calm0=pg.evaluate('localStorage.getItem("sharkAttack_calm")')
    real_tap(pg,sel);pg.wait_for_timeout(1200)
    if sel=='#cred':
      check(pg.evaluate('__sa.state')=='credits','Credits opens');real_tap(pg,'#credBack');pg.wait_for_timeout(300)
    a=pg.evaluate('__sa.titleShark');pg.wait_for_timeout(500);c=pg.evaluate('__sa.titleShark')
    ok=pg.evaluate('__sa.titlePose.rel')!=None and not pg.evaluate('__sa.titlePose.pose') and not c['front'] and abs(c['x']-a['x'])>0.5 and pg.evaluate('__sa.state')=='title'
    extra=''
    if sel=='#calm': ok=ok and pg.evaluate('localStorage.getItem("sharkAttack_calm")')!=calm0;extra=' (Calm setting flipped)'
    check(ok,f'{sel} releases the pose; shark glides off and cruises{extra}')
    if sel=='#cred': pg.screenshot(path=f'{SHOTS}/after-release-915x412.png')
    if sel=='#calm': pg.evaluate('localStorage.setItem("sharkAttack_calm",'+('"0"' if calm0 in (None,'0') else '"1"')+')')
  tap_start(pg,915,412);pg.wait_for_function('window.__saTitleDone===true',timeout=12000);real_tap(pg,'#start')
  check(pg.evaluate('__sa.state')=='pick','Start goes straight on (pick screen) with no delay')
  pg.click('.pick[data-type=white]');pg.wait_for_timeout(300);check(pg.evaluate('__sa.state')=='play','game starts')
  check(not errs,f'no page errors {errs[:2]}');cx.close()
  # (d) calm + reduced motion
  for tag,rm,calmv in [('calm',None,'1'),('reduced motion',"reduce",None)]:
    cx=ctx(b,915,412,rm);pg=cx.new_page();pg.goto(URL)
    if calmv: pg.evaluate('localStorage.setItem("sharkAttack_calm","1")');pg.reload()
    pg.wait_for_timeout(400);pg.evaluate('window.__saTitleLog=1');pg.touchscreen.tap(457,206);pg.wait_for_timeout(100)
    pts=[];t0=time.time()
    while not pg.evaluate('window.__saTitleDone') and time.time()-t0<8: pts.append(pg.evaluate('__sa.titleShark'));pg.wait_for_timeout(100)
    log=pg.evaluate('__sa.titleLog');pts=[q for q in pts if q]
    check(pg.evaluate('window.__saTitleDone') and all(q['front'] for q in pts) and len({round(q['x']) for q in pts})==1,f'{tag}: head-on shark only fades in at its spot (no swim, no laps)')
    check(not any(e[1]=='snap' for e in log) and pg.evaluate('document.getElementById("cv")?getComputedStyle(document.getElementById("cv")).transform:"none"') in ('none',''),f'{tag}: no snap, no shake')
    a=pg.evaluate('__sa.titleShark');pg.wait_for_timeout(4000);c=pg.evaluate('__sa.titleShark')
    check(a['x']==c['x'] and a['s']==c['s'] and pg.evaluate('__sa.titlePose.pose'),f'{tag}: pose held still (no breathing)')
    pg.screenshot(path=f'{SHOTS}/{tag.replace(" ","-")}-pose-915x412.png')
    real_tap(pg,'#fx');pg.wait_for_timeout(1200);check(pg.evaluate('__sa.titlePose.rel')!=None and not pg.evaluate('__sa.titleShark.front'),f'{tag}: a button releases the pose')
    cx.close()
  # (e) sizes and orientations
  for w,h in [(360,640),(390,844),(412,915),(640,360),(844,390),(915,412),(768,1024),(1024,768)]:
    cx=ctx(b,w,h);pg=cx.new_page();tap_start(pg,w,h);pg.wait_for_function('window.__saTitleDone===true',timeout=12000);pg.wait_for_timeout(300)
    res=pg.evaluate('''(()=>{const r=__sa.titleRect,c=document.querySelector("canvas").getBoundingClientRect(),W=innerWidth,H=innerHeight,rot=__sa.rotPaused;
      const tb={l:r.x,t:r.y,r:r.x+r.w,b:r.y+r.h},hit=[...document.querySelectorAll("#titleUi button")].filter(e=>{const b=e.getBoundingClientRect();return b.width>0&&b.left<tb.r&&b.right>tb.l&&b.top<tb.b&&b.bottom>tb.t}).map(e=>e.id);
      const out={rot,hit,title:r.x>=0&&r.y>=0&&r.x+r.w<=c.width+.5&&r.y+r.h<=c.height+.5,bad:[]};
      for(const id of %s){const e=document.getElementById(id),b=e.getBoundingClientRect(),x=b.x+b.width/2,y=b.y+b.height/2,top=document.elementFromPoint(x,y);
        if(!(b.width>0&&b.height>0&&b.x>=0&&b.y>=0&&b.right<=W+.5&&b.bottom<=H+.5&&top&&(top===e||e.contains(top))))out.bad.push(id)}return out})()'''%BTNS)
    pg.screenshot(path=f'{SHOTS}/pose-{w}x{h}.png')
    if h>w: check(pg.evaluate('window.__rotShown'),f'{w}x{h}: portrait shows the "Turn your phone sideways" cover as before (game is landscape-only); layout below checked with the cover hidden')
    check(res['title'],f'{w}x{h}: whole title inside the canvas');(check if w>h else (lambda c,m: print(('PASS ' if c else 'NOTE (portrait is covered by the turn-phone screen in the real game) ')+m)))(not res['hit'],f'{w}x{h}: no button covers any part of the title {res["hit"]}');(check if w>h else (lambda c,m: print(('PASS ' if c else 'NOTE (portrait is covered by the turn-phone screen in the real game; same button CSS as build 48) ')+m)))(not res['bad'],f'{w}x{h}: every title button visible, inside the screen, on top (elementFromPoint) {res["bad"]}')
    cx.close()
  b.close()
finally: srv.terminate()
print(f'\n{passes} passed, {len(fails)} failed');sys.exit(1 if fails else 0)
