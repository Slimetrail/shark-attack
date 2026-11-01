# Turn filmstrip (pretend phone, Chromium touch emulation): holds the shark's head/tail yaw at the values a real 180 deg turn passes through
# (same easing as game.js TURN3D: head at PI/SEC rad/s, tail follows at TAIL/s) and grabs 10 frames at 2x, side by side.
# Usage: /workspace/.pwvenv/bin/python tools/turn_filmstrip.py OUT.png [ROOT] [PORT]
import sys,os,subprocess,time,base64,math,json
from playwright.sync_api import sync_playwright
out=sys.argv[1];root=sys.argv[2] if len(sys.argv)>2 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)));port=sys.argv[3] if len(sys.argv)>3 else '8966'
srv=subprocess.Popen([sys.executable,'-m','http.server',port,'--bind','127.0.0.1'],cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();cx=b.new_context(viewport={'width':844,'height':390},device_scale_factor=2,has_touch=True,is_mobile=True,service_workers='block',bypass_csp=True);pg=cx.new_page()
  pg.goto(f'http://127.0.0.1:{port}/');pg.wait_for_timeout(600);pg.touchscreen.tap(422,195);pg.wait_for_timeout(300)
  pg.evaluate('__sa.startAs("white","endless");__sa.god=true;__sa.setLevel(3);__sa.clearFood();const s=__sa.shark;s.air=false;s.y=__sa.SURF+(__sa.BED-__sa.SURF)*.3;s.ang=0;s.spd=0')
  pg.wait_for_timeout(400);T=pg.evaluate('__sa.TURN3D');sec=T['SEC'];tail=T['TAIL']
  yaw=0;yt=0;dt=1/240;seq=[];t=0
  while t<sec+.6:
    yaw=min(math.pi,yaw+math.pi/sec*dt);yt+= (yaw-yt)*min(1,dt*tail);seq.append((t,yaw,yt));t+=dt
  total=seq[-1][0];frames=[seq[min(len(seq)-1,int(k/9*(sec+.25)/dt))] for k in range(10)]
  shots=[]
  for (t,y,yt_) in frames:
    pg.evaluate(f'window.__saYawHold=[{y},{yt_}];__sa.shark.spd=0;__sa.shark.ang={math.pi if y>math.pi/2 else 0}');pg.wait_for_timeout(120)
    r=pg.evaluate('({x:__sa.shark.x-__sa.camX,y:__sa.shark.y-__sa.camY,L:__sa.shark.L})')
    w=r['L']*1.7;h=r['L']*.95
    shots.append((t,y,yt_,base64.b64encode(pg.screenshot(clip={'x':r['x']-w/2,'y':r['y']-h/2,'width':w,'height':h})).decode()))
  pg.evaluate('window.__saYawHold=null')
  html='<body style="margin:0;background:#061b26;color:#cde;font:12px sans-serif;display:flex;flex-wrap:wrap;width:{int(w*5)+2}px">'+''.join(f'<div><img src="data:image/png;base64,{d}" style="width:{w}px;display:block"><div>{t:.2f}s head {math.degrees(y):.0f}&deg; tail {math.degrees(yt_):.0f}&deg;</div></div>' for (t,y,yt_,d) in shots)+'</body>'
  pg2=b.new_page(viewport={"width":int(w*5)+2,"height":int(h*2)+44},device_scale_factor=2);pg2.set_content(html);pg2.wait_for_timeout(300);pg2.screenshot(path=out,full_page=True)
  print(json.dumps([(round(t,2),round(math.degrees(y)),round(math.degrees(yt_))) for (t,y,yt_,d) in shots]))
finally: srv.terminate()
