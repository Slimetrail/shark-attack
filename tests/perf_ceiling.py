# v8 G: render-scale x effects grid (a desktop-Chromium PROXY for a phone, not a phone measurement).
# Run: python3 tests/perf_ceiling.py CPU [adapt]   e.g. 1 / 4 / 6 ; port 8896 (SA_PORTG). Prints one JSON line per config.
import os,sys,json,subprocess,time
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORTG','8896'));URL=f'http://127.0.0.1:{PORT}/'
CPU=float(sys.argv[1]);ADAPT=int(sys.argv[2]) if len(sys.argv)>2 else 0
RS=[float(x) for x in os.environ.get('SA_RS','0.5,0.75,1,1.5,2').split(',')];FXS=[int(x) for x in os.environ.get('SA_FX','0,1,2,3').split(',')]
SCN={'deep':('8','__sa.SURF+(__sa.BED-__sa.SURF)*.8'),'surface':('9','__sa.SURF+innerHeight*.3')}
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
MEAS='''()=>new Promise(res=>{const d=[];let last=performance.now();const t0=last;const f=n=>{d.push(n-last);last=n;if(n-t0<5000)requestAnimationFrame(f);else res(d)};requestAnimationFrame(f)})'''
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2.625,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');pg=cx.new_page();ev=pg.evaluate
  cdp=cx.new_cdp_session(pg)
  for scn,(lvl,yy) in SCN.items():
   for rs in RS:
    for fx in FXS:
     cdp.send('Emulation.setCPUThrottlingRate',{'rate':1})
     pg.goto(f'{URL}?rs={rs}&fx={fx}&adapt={ADAPT}&dprcap=2.625');pg.wait_for_timeout(250);pg.click('#tap');pg.wait_for_timeout(150);pg.click('#start');pg.wait_for_timeout(150);pg.click('.pick[data-type=tiger]');pg.wait_for_timeout(250)
     ev('__sa.god=true;__sa.timeLeft=999')
     ev(f'()=>{{__sa.setLevel({lvl});const s=__sa.shark;s.y={yy};s.x=__sa.camX+innerWidth/2;__sa.camX=s.x-innerWidth/2;__sa.camY=s.y-innerHeight/2;__sa.respawnAll();for(const f of __sa.fish){{if(f.kind!=="star")f.y=s.y+(Math.random()-.5)*innerHeight*.8;f.x=__sa.camX+Math.random()*innerWidth}}}}')
     cdp.send('Emulation.setCPUThrottlingRate',{'rate':CPU});pg.wait_for_timeout(400);ev('__sa.perf.reset()')
     d=sorted(ev(MEAS)[1:]);n=len(d);js=ev('__sa.perf.js/Math.max(1,__sa.perf.frames)');st=ev('__sa.state')
     fps=[1000/x for x in d];lo=lambda q:sum(fps[n-max(1,int(n*q)):])/max(1,int(n*q))  # avg fps of the slowest q of frames
     r=dict(scene=scn,cpu=CPU,adapt=ADAPT,rs=rs,fx=fx,frames=n,avg_fps=round(n/(sum(d)/1000),1),low1=round(lo(.01),1),low5=round(lo(.05),1),p99_ms=round(d[min(n-1,int(n*.99))],1),
            over16=sum(x>16.7 for x in d),over8=sum(x>8.3 for x in d),spikes33=sum(x>33.4 for x in d),js_ms=round(js,2),state=st)
     print(json.dumps(r),flush=True)
  b.close()
finally: srv.terminate()
