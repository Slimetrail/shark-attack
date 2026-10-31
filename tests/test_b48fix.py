# b48-fix tests (QA verdict on 8ab7259): the sound/intro must not start on finger DOWN, only when the finger comes UP; update/install buttons >= 44 px tall in landscape;
# AUDIO-LICENSES.md has an entry for the "Art, sound effects and code: original" credit.
# Run: python3 tests/test_b48fix.py  (port 8901). Pretend phone (Chromium touch emulation), never a real phone.
import os,sys,subprocess,time
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT48F','8901'));URL=f'http://127.0.0.1:{PORT}/';passes=0;fails=[]
def check(c,m):
  global passes
  if c: passes+=1;print('PASS',m)
  else: fails.append(m);print('FAIL',m)
lic=open(os.path.join(ROOT,'AUDIO-LICENSES.md')).read()
check('Art, sound effects and code: original' in lic and 'CC0' in lic.split('Art, sound effects and code: original')[-1] and '2026-10-31' in lic,'AUDIO-LICENSES.md has a dated own-work CC0 entry for the "Art, sound effects and code: original" credit')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
ST='({ac:AC?AC.state:"none",paused:music.title?music.title.paused:null,state:state,t:music.title?music.title.currentTime:-1})'
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--autoplay-policy=document-user-activation-required'])
  for how in ('touch','mouse'):
   cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');pg=cx.new_page()
   errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(URL);pg.wait_for_timeout(500)
   s0=pg.evaluate(ST)
   check(s0['state']=='tap' and s0['ac']=='none' and s0['paused'] is not False,f'{how}: starts on "Tap to start", audio engine not created, no music {s0}')
   if how=='touch':
    cd=cx.new_cdp_session(pg);cd.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':457,'y':206}]})
   else:
    pg.mouse.move(457,206);pg.mouse.down()
   pg.wait_for_timeout(1500)
   s1=pg.evaluate(ST)
   check(s1['state']=='tap' and s1['ac']=='none' and s1['paused'] is not False,f'{how}: finger held DOWN 1.5 s -> still "Tap to start", no sound started {s1}')
   if how=='touch': cd.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
   else: pg.mouse.up()
   for _ in range(30):  # wait until the music has really started (no fixed timing guess)
    pg.wait_for_timeout(200)
    if pg.evaluate(ST)['t']>0.1:break
   s2=pg.evaluate(ST)
   check(s2['state']=='title' and s2['ac']=='running' and s2['paused'] is False and s2['t']>0.1,f'{how}: finger UP -> intro starts and title music plays {s2}')
   if how=='touch':
    # a cancelled press starts nothing
    pg2=cx.new_page();pg2.goto(URL);pg2.wait_for_timeout(500);c2=cx.new_cdp_session(pg2)
    c2.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':457,'y':206}]});pg2.wait_for_timeout(200);c2.send('Input.dispatchTouchEvent',{'type':'touchCancel','touchPoints':[]});pg2.wait_for_timeout(800)
    s3=pg2.evaluate(ST)
    check(s3['state']=='tap' and s3['ac']=='none' and s3['paused'] is not False,f'touch: a cancelled press starts nothing {s3}')
   check(not errs,f'{how}: no page errors {errs[:2]}')
   cx.close()
  # button heights in landscape (phone 915x412): force them visible and measure
  cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');pg=cx.new_page();pg.goto(URL);pg.wait_for_timeout(500)
  h=pg.evaluate('()=>{const o={};for(const id of["updb","instb"]){const e=document.getElementById(id);if(!e){o[id]=null;continue}let n=e;const hid=[];while(n&&n!==document.body){if(n.classList&&n.classList.contains("hide")){hid.push(n);n.classList.remove("hide")}n=n.parentElement}o[id]=e.getBoundingClientRect().height;hid.forEach(x=>x.classList.add("hide"))}return o}')
  check(all(v is not None and v>=44 for v in h.values()),f'landscape: "Check for update" and "Install app" buttons are at least 44 px tall {h}')
finally: srv.terminate()
print(f'{passes} passed, {len(fails)} failed')
for f in fails: print('FAILED:',f)
sys.exit(1 if fails else 0)
