# b51 tests (QA on build 50, via Eve): whole head-on shark on screen, buttons clear of the shark, title never covered (640x360 too),
# Install hint does not move anything, cruising shark stays behind the words, chomp on every title visit.
# Run: /workspace/.pwvenv/bin/python tests/test_b51.py (port 8904). Pretend phone (Chromium touch emulation), never a real phone.
import os,sys,subprocess,time,json
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT51','8904'));URL=f'http://127.0.0.1:{PORT}/'
passes=0;fails=[]
def check(c,m):
  global passes
  if c: passes+=1;print('PASS',m)
  else: fails.append(m);print('FAIL',m)
def ctx(b,w,h):return b.new_context(viewport={'width':w,'height':h},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block')
def tap_start(pg,w,h,updb=True):
  pg.goto(URL);pg.wait_for_timeout(500);pg.touchscreen.tap(w/2,h/2);pg.wait_for_timeout(100)
  if updb: pg.evaluate('document.getElementById("updb").classList.remove("hide")')
  pg.wait_for_function('window.__saTitleDone===true',timeout=12000);pg.wait_for_timeout(400)
MEASURE='''(()=>{const L=__sa.titleLayout||null,W=innerWidth,H=innerHeight;const k=1.01,L0=L||{cx:0,cy:0,box:{x:0,y:-1e4,w:0,h:0},head:{x:0,y:-1e4,w:0,h:0}},bx=L0.box,hd=L0.head;if(!L)console.log("no titleLayout");
 const box={l:L0.cx-(L0.cx-bx.x)*k,r:L0.cx+(bx.x+bx.w-L0.cx)*k,t:L0.cy-(L0.cy-bx.y)*k,b:L0.cy+(bx.y+bx.h-L0.cy)*k},r=__sa.titleRect,tb={l:r.x,t:r.y,r:r.x+r.w,b:r.y+r.h};
 const ov=(a,b)=>a.left<b.r&&a.right>b.l&&a.top<b.b&&a.bottom>b.t,btn=[...document.querySelectorAll("#titleUi button")].map(e=>[e.id,e.getBoundingClientRect()]).filter(x=>x[1].width>0);
 return {none:!L,box,head:{l:hd.x,t:hd.y,r:hd.x+hd.w,b:hd.y+hd.h},W,H,title:r,onShark:btn.filter(x=>ov(x[1],box)).map(x=>x[0]),onTitle:btn.filter(x=>ov(x[1],tb)).map(x=>x[0]),start:document.getElementById("start").getBoundingClientRect().top,sr:__sa.titleShark}})()'''
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
  for w,h in [(640,360),(844,390),(915,412),(1024,600),(1280,720),(740,360),(667,375)]:
    cx=ctx(b,w,h);pg=cx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));tap_start(pg,w,h);m=pg.evaluate(MEASURE)
    if m['none']: check(False,f'{w}x{h}: shark box readable (__sa.titleLayout missing, so head-on-screen and buttons-clear-of-shark cannot pass)')
    bx=m['box'];check(bx['t']>=0 and bx['l']>=0 and bx['r']<=w and bx['b']<=h,f'{w}x{h}: whole head-on shark (head, eyes, fins) inside the screen, top y={bx["t"]:.1f}')
    check(not m['onShark'],f'{w}x{h}: no title button overlaps the shark box {m["onShark"]}')
    check(not m['onTitle'],f'{w}x{h}: no title button covers the title {m["onTitle"]}')
    t=m['title'];check(t['w']>=100 and t['x']>=0 and t['x']+t['w']<=w,f'{w}x{h}: title whole and readable size ({t["w"]:.0f}px wide)')
    # Install hint
    r0=m['title'];s0=m['start'];pg.evaluate('document.getElementById("instb").click()');pg.wait_for_timeout(400);m2=pg.evaluate(MEASURE);r1=m2['title']
    vis=pg.evaluate('(()=>{const e=document.getElementById("insth");return !e.classList.contains("hide")&&e.textContent.length>0})()')
    check(vis and all(abs(r0[k]-r1[k])<.5 for k in 'xywh') and abs(m2['start']-s0)<.5 and not m2['onTitle'],f'{w}x{h}: Install hint shown, title and Start stay exactly in place {r0["y"]:.1f}->{r1["y"]:.1f}, w {r0["w"]:.1f}->{r1["w"]:.1f}')
    # after release: cruising side shark is behind the words
    pg.wait_for_timeout(1500);lay=[];
    for i in range(10): lay.append(pg.evaluate('__sa.titleShark&&__sa.titleShark.layer'));pg.wait_for_timeout(200)
    check(pg.evaluate('__sa.titlePose.rel')!=None and all(l=='behind' for l in lay),f'{w}x{h}: after a button the cruising shark is drawn behind the title {set(lay)}')
    check(not errs,f'{w}x{h}: no page errors {errs[:1]}');cx.close()
  # chomp every title visit
  cx=ctx(b,915,412);pg=cx.new_page();tap_start(pg,915,412,False);pg.wait_for_timeout(600);c1=pg.evaluate('__sa.sfxCount.chomp')
  pg.click('#start');pg.wait_for_timeout(300);pg.click('.pick[data-type=white]');pg.wait_for_timeout(600);pg.evaluate('__sa.timeLeft=0.01');pg.wait_for_selector('#home',state='visible',timeout=8000);pg.wait_for_timeout(800)
  c2=pg.evaluate('__sa.sfxCount.chomp');pg.click('#home');pg.wait_for_timeout(300);pg.wait_for_function('window.__saTitleDone===true',timeout=12000);pg.wait_for_timeout(600);c3=pg.evaluate('__sa.sfxCount.chomp')
  check(c1>=1 and c3==c2+1,f'chomp plays again on the second title visit after Home (counts {c1}, {c2} -> {c3})');cx.close()
  # b53 (Skeptic gap): the layout is recalculated on resize (915x412 -> 915x330): buttons stay clear of the shark and the title
  cx=ctx(b,915,412);pg=cx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));tap_start(pg,915,412,False);m0=pg.evaluate(MEASURE)
  pg.set_viewport_size({'width':915,'height':330});pg.wait_for_timeout(700);m=pg.evaluate(MEASURE);bx=m['box']
  check(m['H']==330 and not m['onShark'] and not m['onTitle'],f'resize 915x412 -> 915x330: no button over the shark {m["onShark"]} or the title {m["onTitle"]}')
  check(bx['t']>=0 and bx['b']<=330 and bx['b']<=m['start']+1,f'resize 915x412 -> 915x330: whole head-on shark on screen and above Start (box {bx["t"]:.0f}-{bx["b"]:.0f}, Start top {m["start"]:.0f})')
  check(m['title']['h']<m0['title']['h']-1 or m['title']['y']<m0['title']['y']-1,f'resize: title re-laid out (y {m0["title"]["y"]:.0f}->{m["title"]["y"]:.0f}, h {m0["title"]["h"]:.0f}->{m["title"]["h"]:.0f})')
  check(not errs,f'resize: no page errors {errs[:1]}');cx.close()
  b.close()
finally: srv.terminate()
print(f'\n{passes} passed, {len(fails)} failed');sys.exit(1 if fails else 0)
