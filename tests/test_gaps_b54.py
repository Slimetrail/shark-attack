# b54 test gaps (Skeptic/Jeremy via Eve): three mutations used to pass the whole suite. Each check below fails on its mutant (see tests/MUTATIONS-b54.md).
#  1 perf fix: the screen counts as "busy" (cheaper effects) while the waterline is on screen, even with few creatures
#  2 title head: the head-on shark is really drawn behind the title at the pose
#  3 boat size floor: sail boats / cargo ships never draw shorter than .55 / .85 x the shark's length at the size-10 cap
# Run: /workspace/.pwvenv/bin/python tests/test_gaps_b54.py (port SA_PORTG54, default 8958). Pretend phone (Chromium touch emulation), never a real phone.
import subprocess,sys,os,time
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORTG54','8958'));URL=f'http://127.0.0.1:{PORT}/'
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
ok=bad=0
def check(c,m):
  global ok,bad
  print(('PASS ' if c else 'FAIL ')+m);ok+=bool(c);bad+=not c
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,is_mobile=True,has_touch=True,bypass_csp=True,service_workers='block');pg=cx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(URL);pg.wait_for_timeout(400);pg.click('#tap');pg.wait_for_function('window.__saTitleDone===true',timeout=60000)
  pg.wait_for_function('__sa.titlePose.pose===true',timeout=30000);pg.wait_for_timeout(1500)
  # 2 title head: sample the snout area ABOVE the title words; it must be shark grey, not sky/water blue
  r=pg.evaluate('''(()=>{const c=document.getElementById("c"),g=c.getContext("2d"),L=__sa.titleLayout,d=c.width/innerWidth,S=L.S;let grey=0,n=0;
    for(let y=L.cy-S*.42;y<L.cy-S*.12;y+=S*.03)for(let x=L.cx-S*.22;x<=L.cx+S*.22;x+=S*.03){const q=g.getImageData(Math.round(x*d),Math.round(y*d),1,1).data;n++;if(Math.abs(q[2]-q[0])<45&&q[0]<170)grey++}
    return {grey,n}})()''')
  check(r['n']>0 and r['grey']>=r['n']*.6,f'title pose: head-on shark drawn behind the title ({r["grey"]}/{r["n"]} snout samples are shark grey)')
  cx.close()
  cx=b.new_context(viewport={'width':844,'height':390},device_scale_factor=2,is_mobile=True,has_touch=True,bypass_csp=True,service_workers='block');pg=cx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(URL);pg.wait_for_timeout(400);pg.touchscreen.tap(422,195);pg.wait_for_timeout(300)
  # 1 perf fix
  def busy(dep):
    return pg.evaluate(f'''new Promise(res=>{{__sa.startAs("white","endless");__sa.god=true;__sa.setLevel(0);const s=__sa.shark;s.y={dep};s.spd=0;__sa.clearFood();for(const f of __sa.fish)f.off=true;
      let n=0;const f=()=>{{for(const q of __sa.fish)q.off=true;if(++n<20)requestAnimationFrame(f);else res({{busy:__sa.busy,onWater:__sa.SURF>__sa.camY&&__sa.SURF<__sa.camY+innerHeight}})}};requestAnimationFrame(f)}})''')
  r=busy('__sa.SURF+innerHeight*.2');check(r['onWater'] and r['busy'] is True,f'waterline on screen, no creatures: busy (cheap effects) is on {r}')
  r=busy('__sa.SURF+(__sa.BED-__sa.SURF)*1.5');check((not r['onWater']) and r['busy'] is False,f'deep, no waterline, no creatures: busy is off {r}')
  # 3 boat floor at the cap
  r=pg.evaluate('''(()=>{__sa.startAs("white","endless");__sa.god=true;__sa.setLevel(9);const out={};for(const k of [2,3]){const s=__sa.surf[0];__sa.spawnSurf(s,true);s.k=k;out[k]=__sa.surfDrawK(s)*2*__sa.SURFERS[k].hw/__sa.shark.L}return out})()''')
  check(r['2']>=.55-1e-6,f'size 10: sail boat draws >= .55 x shark length ({r["2"]:.3f})')
  check(r['3']>=.85-1e-6,f'size 10: cargo ship draws >= .85 x shark length ({r["3"]:.3f})')
  # the floor does not bind at any reachable size in b54 (ratios above), so also check it directly with a 4x longer shark: it must hold the floor
  r=pg.evaluate('''(()=>{const sh=__sa.shark,L0=sh.L,out={};sh.L=L0*4;for(const k of [2,3]){const s=__sa.surf[0];s.k=k;out[k]=__sa.surfDrawK(s)*2*__sa.SURFERS[k].hw/sh.L}sh.L=L0;return out})()''')
  check(r['2']>=.55-1e-6 and r['3']>=.85-1e-6,f'boat floor holds when boats would otherwise draw small (sail {r["2"]:.3f}, cargo {r["3"]:.3f} x shark length)')
  check(not errs,f'no page errors {errs[:2]}')
  b.close()
finally: srv.terminate()
print(f'\n{ok} passed, {bad} failed');sys.exit(1 if bad else 0)
