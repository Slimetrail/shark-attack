# b55 screenshots (desktop Chromium touch emulation, not a real phone): 1 outgrown top band, tiny fish beside a HUD 6 shark; 2 late game (HUD 9, mid depth).
# Usage: /workspace/.pwvenv/bin/python tools/b55_shots.py [OUT dir]
import os,sys,subprocess,time
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));OUT=sys.argv[1] if len(sys.argv)>1 else '/workspace/shark-b55-runs/shots';os.makedirs(OUT,exist_ok=True)
PORT=8990;U=f'http://127.0.0.1:{PORT}/'
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  for w,h in [(844,390),(915,412)]:
   for name,lvl,dep in [('tiny-fish-hud6',5,.12),('late-hud9',8,1.2)]:
    cx=b.new_context(viewport={'width':w,'height':h},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');pg=cx.new_page()
    pg.goto(U);pg.wait_for_timeout(300);pg.touchscreen.tap(w//2,h//2);pg.wait_for_timeout(300)
    info=pg.evaluate(f'''()=>{{__sa.startAs("white","endless");__sa.god=true;__sa.setLevel({lvl});const s=__sa.shark,S=__sa.SURF,D=__sa.BED-S;s.y=S+D*{dep};s.spd=0;__sa.respawnAll();__sa.sim(3);
      const v=__sa.fish.filter(f=>!f.off&&Math.abs(f.x-s.x)<innerWidth/2&&Math.abs(f.y-s.y)<innerHeight/2);return {{lvl:s.lvl+1,tiny:v.filter(f=>f.tiny).length,food:v.filter(f=>!f.tiny&&__sa.rel(f)<0).length,danger:v.filter(f=>f.danger).length}}}}''')
    pg.wait_for_timeout(700);fn=f'{OUT}/b55-{name}-{w}x{h}.png';pg.screenshot(path=fn);print(fn,info);cx.close()
  b.close()
finally: srv.terminate()
