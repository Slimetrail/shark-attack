# Renders the PWA icons from the game's own shark drawing code. Run: python3 tools/make_icons.py
import subprocess,sys,time,os,base64
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=8871
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page();pg.goto(f'http://localhost:{PORT}/');pg.wait_for_timeout(300)
  for name,size,mask in [('icon-192',192,0),('icon-512',512,0),('maskable-512',512,1)]:
   d=pg.evaluate('''([S,mask])=>{const c=document.createElement('canvas');c.width=c.height=S;const g=c.getContext('2d');
    if(mask){g.fillStyle='#1aa0d6';g.fillRect(0,0,S,S)}else{g.fillStyle='#1aa0d6';g.beginPath();g.roundRect(S*.04,S*.04,S*.92,S*.92,S*.2);g.fill();g.lineWidth=S*.03;g.strokeStyle='#082a3d';g.stroke()}
    g.strokeStyle='rgba(220,248,255,.5)';g.lineWidth=S*.02;g.lineCap='round';for(const y of[.25,.75]){g.beginPath();g.moveTo(S*.2,S*y);g.quadraticCurveTo(S*.3,S*(y-.04),S*.4,S*y);g.stroke()}
    const L=S*(mask?.5:.62);g.translate(S*.53,S*.5);g.rotate(-Math.PI/4);g.save();g.translate(-L*.42,0);g.rotate(.25);drawTail(g,L);g.restore();drawTopShark(g,L);return c.toDataURL()}''',[size,mask])
   open(f'{ROOT}/icons/{name}.png','wb').write(base64.b64decode(d.split(',')[1]))
  b.close()
finally: srv.terminate()
