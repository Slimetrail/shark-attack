# v10 graphics steps: screenshots (landscape 915x412 + phone 844x390), side-by-side with Jeremy's poster, and a 4x slow-CPU perf run.
# Usage: python3 tools/gfx_shots.py <label> [--perf-only]   (desktop Chromium, not a real phone)
import os,sys,subprocess,time,json
from playwright.sync_api import sync_playwright
from PIL import Image
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));OUT='/workspace/shark-shots/v10-gfx';os.makedirs(OUT,exist_ok=True)
LBL=sys.argv[1];PORT=int(os.environ.get('GFX_PORT','8941'));U=f'http://127.0.0.1:{PORT}/';POSTER=os.environ.get('GFX_POSTER','/workspace/shark-feedback/jeremy-screenshot-t747.jpg')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
def game(b,w,h,dpr,typ='white'):
  cx=b.new_context(viewport={'width':w,'height':h},device_scale_factor=dpr,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');pg=cx.new_page()
  pg.goto(U);pg.wait_for_timeout(300);pg.evaluate(f'()=>{{__sa.startAs("{typ}","endless");__sa.god=true;__sa.timeLeft=999}}');pg.wait_for_timeout(200);return cx,pg
def place(pg,frac,lvl=2):
  pg.evaluate(f'''()=>{{__sa.setLevel({lvl});const s=__sa.shark;s.x=__sa.camX+innerWidth/2;s.y=__sa.SURF+(__sa.BED-__sa.SURF)*{frac}+40;s.ang=0;s.spd=0;__sa.camX=s.x-innerWidth/2;__sa.camY=Math.max(0,s.y-innerHeight/2);__sa.respawnAll();__sa.timeLeft=999;
    for(const f of __sa.fish){{if(f.kind==="star"||f.off)continue;f.y=Math.max(__sa.SURF+20,s.y+(Math.random()-.5)*innerHeight*.8);f.x=__sa.camX+Math.random()*innerWidth}}}}''');pg.wait_for_timeout(700)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();res={}
  if '--perf-only' not in sys.argv:
   cx,pg=game(b,915,412,2.625)
   for name,frac in (('shallow',.0),('mid',.45),('deep',.85)):place(pg,frac);pg.screenshot(path=f'{OUT}/{LBL}-915x412-{name}.png')
   pg.evaluate('()=>{__sa.setLevel(5)}');place(pg,.2,5);pg.screenshot(path=f'{OUT}/{LBL}-915x412-size6.png');cx.close()
   cx,pg=game(b,844,390,3,'tiger');place(pg,.25);pg.screenshot(path=f'{OUT}/{LBL}-phone-844x390-mid.png');cx.close()
   po=Image.open(POSTER).convert('RGB');sh=Image.open(f'{OUT}/{LBL}-915x412-mid.png').convert('RGB');H=sh.height;po=po.resize((round(po.width*H/po.height),H))
   sb=Image.new('RGB',(po.width+sh.width+20,H),(10,10,14));sb.paste(po,(0,0));sb.paste(sh,(po.width+20,0));sb.save(f'{OUT}/{LBL}-side-by-side-poster.png')
   ta=os.path.join(ROOT,'title-art-crop-preview.png')
   if os.path.exists(ta):
    po=Image.open(ta).convert('RGB');po=po.resize((round(po.width*H/po.height),H));sb=Image.new('RGB',(po.width+sh.width+20,H),(10,10,14));sb.paste(po,(0,0));sb.paste(sh,(po.width+20,0));sb.save(f'{OUT}/{LBL}-side-by-side-title-art.png')
  for (VW,VH,VD) in ((915,412,2.625),(844,390,3)):
   res={}
   cx,pg=game(b,VW,VH,VD);cdp=cx.new_cdp_session(pg);cdp.send('Emulation.setCPUThrottlingRate',{'rate':4})
   for name,frac in (('mid',.45),('deep',.85)):
    place(pg,frac);pg.mouse.move(400,200);pg.mouse.down();pg.mouse.move(520,205,steps=4);pg.wait_for_timeout(800);pg.evaluate('__sa.perf.reset()')
    for i in range(25):pg.mouse.move(520+(i%5)*10,205+((i//5)%2)*40-20);pg.wait_for_timeout(200)
    pg.mouse.up();r=pg.evaluate('({f:__sa.perf.frames,js:__sa.perf.js,dt:__sa.perf.dtSum})');res[name]={'fps':round(r['f']/max(r['dt'],1e-6),1),'ms_per_frame_js':round(r['js']/max(r['f'],1),2)}
   print(LBL,f'4x slow CPU, {VW}x{VH} @{VD}:',json.dumps(res));cx.close()
  b.close()
finally: srv.kill()
