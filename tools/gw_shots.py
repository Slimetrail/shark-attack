# v10 step 1 screenshots: great white sprite alone, in game at size 1 and 6, side by side with poster crop. Phone portrait 412x915 (desktop Chromium, not a phone).
import os,sys,subprocess,time
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));OUT='/workspace/shark-shots/v10-gw';PORT=8931;U=f'http://127.0.0.1:{PORT}/'
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
POSTER='file:///workspace/shark-attack-v10/title-art-crop-preview.png'
try:
 with sync_playwright() as p:
  b=p.chromium.launch();cx=b.new_context(viewport={'width':412,'height':915},device_scale_factor=2.625,has_touch=True,is_mobile=True,service_workers='block');pg=cx.new_page();ev=pg.evaluate
  pg.goto(U);pg.wait_for_timeout(400)
  ev('''()=>{const d=document.createElement("div");d.id="gwv";d.style.cssText="position:fixed;inset:0;z-index:9999;background:linear-gradient(#123a5c,#06172a);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:30px";
   for(const o of [false,true]){const c=__sa.render3DShark(400*2.625,o,__sa.TYPES.white);c.style.width="400px";const l=document.createElement("div");l.textContent=o?"mouth open":"mouth closed";l.style.cssText="color:#9cc;font:16px sans-serif";d.appendChild(c);d.appendChild(l)}document.body.appendChild(d)}''')
  pg.wait_for_timeout(200);pg.screenshot(path=f'{OUT}/a-great-white-alone.png')
  for side,old in (('new',''),('old','?oldgw')):
   pg.goto(U+old);pg.wait_for_timeout(300)
   ev(f'''()=>new Promise(r=>{{const d=document.createElement("div");d.style.cssText="position:fixed;inset:0;z-index:9999;background:linear-gradient(#123a5c,#06172a);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;color:#9cc;font:15px sans-serif";
    const im=new Image();im.src="{'/'}poster.png";d.innerHTML="";const t=document.createElement("div");t.textContent="Jeremy's poster (reference)";const c=__sa.render3DShark(400*2.625,false,__sa.TYPES.white);c.style.width="400px";const t2=document.createElement("div");t2.textContent="{'new great white sprite' if side=='new' else 'old build 10 sprite'}";
    d.append(t,im,t2,c);im.style.width="380px";im.onload=im.onerror=()=>r();document.body.appendChild(d)}})''')
   pg.wait_for_timeout(200);pg.screenshot(path=f'{OUT}/c-side-by-side-poster-{side}.png')
  cx2=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2.625,has_touch=True,is_mobile=True,service_workers='block');pg=cx2.new_page();ev=pg.evaluate  # game is landscape-only (portrait shows a rotate prompt)
  for lvl in (1,6):
   pg.goto(U);pg.wait_for_timeout(300);pg.click('#tap');pg.wait_for_timeout(150);pg.click('#start');pg.wait_for_timeout(150);pg.click('.pick[data-type=white]');pg.wait_for_timeout(300)
   ev('__sa.god=true;__sa.timeLeft=999')
   ev(f'()=>{{__sa.setLevel({lvl});const s=__sa.shark;s.y=__sa.SURF+innerHeight*.6;__sa.camX=s.x-innerWidth/2;__sa.camY=s.y-innerHeight/2;__sa.respawnAll();for(const f of __sa.fish){{if(f.kind!=="star")f.y=s.y+(Math.random()-.5)*innerHeight*.7;f.x=__sa.camX+Math.random()*innerWidth}}}}')
   pg.wait_for_timeout(600);pg.screenshot(path=f'{OUT}/b-ingame-size{lvl}.png')
  b.close()
finally: srv.terminate()
