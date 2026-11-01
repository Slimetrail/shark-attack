# b54 tests on a pretend phone (Playwright Chromium, touch): QA #3 quick "Sound on" tap right after the start tap.
# Run: python3 tests/test_b54.py  (port SA_PORT54, default 8954)
import subprocess,sys,os,time
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT54','8954'));URL=f'http://127.0.0.1:{PORT}/'
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
ok=bad=0
def check(c,m):
  global ok,bad
  print(('PASS ' if c else 'FAIL ')+m);ok+=bool(c);bad+=not c
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  for delay in (100,200):
   cx=b.new_context(viewport={'width':844,'height':390},device_scale_factor=2,is_mobile=True,has_touch=True,bypass_csp=True,service_workers='block');pg=cx.new_page()
   pg.goto(URL);pg.evaluate('localStorage.setItem("sharkAttack_sound","0")');pg.reload();pg.wait_for_timeout(800)
   pg.touchscreen.tap(422,195);pg.wait_for_timeout(delay)
   bb=pg.locator('#snd').bounding_box()
   if bb: pg.touchscreen.tap(bb['x']+bb['width']/2,bb['y']+bb['height']/2)
   pg.wait_for_timeout(300)
   check(bb is not None and 'on' in pg.inner_text('#snd') and pg.evaluate('localStorage.sharkAttack_sound')=='1',f'Sound on tap {delay} ms after the start tap turns sound on ({pg.inner_text("#snd")!r})')
   cx.close()
  # the start tap itself still never presses a title button (ghost click guard kept)
  cx=b.new_context(viewport={'width':844,'height':390},device_scale_factor=2,is_mobile=True,has_touch=True,bypass_csp=True,service_workers='block');pg=cx.new_page()
  pg.goto(URL);pg.evaluate('localStorage.setItem("sharkAttack_sound","0")');pg.reload();pg.wait_for_timeout(800)
  bb=pg.locator('#tap').bounding_box();pg.wait_for_timeout(50)
  pg.evaluate('()=>{window.__clk=0;document.getElementById("snd").addEventListener("click",()=>{window.__clk++})}')
  pg.touchscreen.tap(422,195);pg.wait_for_timeout(700)
  check(pg.evaluate('localStorage.sharkAttack_sound')=='0','start tap alone does not toggle sound (ghost guard kept)')
  b.close()
finally: srv.terminate()
print(f'{ok} passed, {bad} failed');sys.exit(1 if bad else 0)
