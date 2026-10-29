# v10 ANALOG steering + "the shark never tires" tests. Run: python3 tests/test_steer.py
# speed = distance of the finger from its FIXED first touch point (item 7: dragging back slows); direction = finger movement, used at once; top speed only by size.
import subprocess,time,sys,os,math
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORTS','8896'))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
URL=f'http://127.0.0.1:{PORT}/';fails=[];passes=0
def check(c,m):
  global passes
  print(('PASS ' if c else 'FAIL ')+m,flush=True)
  if c: passes+=1
  else: fails.append(m)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');pg=cx.new_page();ev=pg.evaluate;errs=[]
  pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(URL+'?round=300');pg.wait_for_timeout(300);ev('()=>{__sa.startAs("white","endless");__sa.god=true}');pg.wait_for_timeout(200)
  W=915;FULL=ev('__sa.STEER.FULL');check(ev('__sa.STEER.TURN')>=10 and 0.15<=FULL<=0.4,f'STEER: TURN {ev("__sa.STEER.TURN")}, full speed at {FULL} screen widths ({FULL*W:.0f}px)')
  def stage(): ev('()=>{__sa.clearFood();const s=__sa.shark;s.x=__sa.camX+innerWidth/2;s.y=__sa.SURF+(__sa.BED-__sa.SURF)*.5;__sa.camY=s.y-innerHeight/2;s.ang=0;s.spd=0;s.stun=0;__sa.touch.on=false;__sa.touch.drive=0;__sa.timeLeft=999}')
  res={}
  for name,L in [('tiny',4),('short',40),('medium',110),('long',300)]:
    stage();pg.mouse.move(300,200);pg.mouse.down()
    for i in range(1,6): pg.mouse.move(300+L*i/5,200);pg.wait_for_timeout(16)
    pg.wait_for_timeout(1800);mx=ev('__sa.maxSpeed()');sp=[]
    for _ in range(8): sp.append(ev('__sa.shark.spd')/mx);pg.wait_for_timeout(50)
    pg.mouse.up();res[name]=(sum(sp)/len(sp),max(sp))
  print('  swipe speed (fraction of top speed, avg/max):',{k:(round(a,3),round(m,3)) for k,(a,m) in res.items()})
  v=[res[k][0] for k in ('tiny','short','medium','long')]
  check(all(v[i]<v[i+1] for i in range(3)),f'speed rises with swipe distance {[round(x,3) for x in v]}')
  check(v[0]<.3 and v[3]>.95,f'tiny move = slow ({v[0]:.2f}), long drag = top speed ({v[3]:.2f})')
  check(all(m<=1.0+1e-6 for _,m in res.values()),'top speed is never exceeded')
  # v10 item 7: the start point stays FIXED; out-and-back drags: speed rises going out, falls coming back toward the start
  def hold_speed(ms=1800):
    pg.wait_for_timeout(ms);mx=ev('__sa.maxSpeed()');sp=[]
    for _ in range(8): sp.append(ev('__sa.shark.spd')/mx);pg.wait_for_timeout(50)
    return sum(sp)/len(sp)
  ob={}
  for back in (40,0):
    stage();pg.mouse.move(300,200);pg.mouse.down()
    for i in range(1,6): pg.mouse.move(300+300*i/5,200);pg.wait_for_timeout(16)
    out_sp=hold_speed();x0=ev('__sa.touch.x0');d_out=ev('__sa.touch.drive')
    for i in range(1,11): pg.mouse.move(600-(300-back)*i/10,200);pg.wait_for_timeout(16)
    dirb=ev('__sa.touch.dir');d_back=ev('__sa.touch.drive');x0b=ev('__sa.touch.x0');back_sp=hold_speed(2500);pg.mouse.up()
    ob[back]=dict(out=out_sp,back=back_sp,d_out=d_out,d_back=d_back,dir=dirb,fixed=abs(x0b-x0)<1e-6)
    print(f'  out 300px then back to {back}px from start: speed out {out_sp:.3f} -> back {back_sp:.3f} of top; drive {d_out:.3f} -> {d_back:.3f}; start point fixed {abs(x0b-x0)<1e-6}')
  check(all(q['fixed'] for q in ob.values()),'start point stays fixed where the finger first touched (out-and-back drags)')
  check(ob[40]['out']>.95 and abs(ob[40]['d_back']-40/(W*FULL))<.01 and ob[40]['back']<res['short'][0]+.08,f"out 300px and back to 40px: speed falls {ob[40]['out']:.2f} -> {ob[40]['back']:.2f} (short swipe gives {res['short'][0]:.2f})")
  check(ob[0]['d_back']<.01 and ob[0]['back']<ev('__sa.STEER.MIN')+.05,f"back onto the start point: drive {ob[0]['d_back']:.3f}, speed {ob[0]['back']:.2f} (idle drift {ev('__sa.STEER.MIN')})")
  check(all(abs(abs(q['dir'])-math.pi)<1e-6 for q in ob.values()),'dragging back points the shark back toward the start at once (finger movement direction)')
  # STEER.FULL is one easy knob: doubling it halves the drive for the same drag
  ev('__sa.STEER.FULL=__sa.STEER.FULL*2');stage();pg.mouse.move(300,200);pg.mouse.down();pg.mouse.move(410,200,steps=5);pg.wait_for_timeout(40);dh=ev('__sa.touch.drive');pg.mouse.up();ev(f'__sa.STEER.FULL={FULL}')
  check(abs(dh-110/(W*FULL*2))<.01,f'STEER.FULL x2 -> a 110px drag gives drive {dh:.3f} (expected {110/(W*FULL*2):.3f})')
  # direction follows the finger at once, even for a tiny move; no twitch while held
  stage();pg.mouse.move(300,200);pg.mouse.down();pg.mouse.move(300,197);pg.wait_for_timeout(40)
  d=ev('__sa.touch.dir');check(abs(d-(-math.pi/2))<1e-6,f'a 3 px move up turns the steering straight up at once (dir {math.degrees(d):.1f} deg)')
  pg.wait_for_timeout(300);a=ev('__sa.shark.ang');check(abs(a-(-math.pi/2))<math.radians(12),f'shark faces the finger within 0.3 s ({math.degrees(a):.1f} deg)')
  pg.mouse.move(380,197);pg.wait_for_timeout(40);d2=ev('__sa.touch.dir');check(abs(d2)<1e-6,f'moving the finger right turns the steering right at once ({math.degrees(d2):.1f} deg)')
  angs=[]
  pg.wait_for_timeout(500)
  for _ in range(20): angs.append(ev('__sa.shark.ang'));pg.wait_for_timeout(30)
  check(max(angs)-min(angs)<math.radians(2),f'no twitch while the finger is held still (heading spread {math.degrees(max(angs)-min(angs)):.2f} deg)')
  pg.mouse.up()
  # the shark never tires: holding a long drag keeps top speed for 10 s (real time)
  stage();pg.mouse.move(200,200);pg.mouse.down();pg.mouse.move(200+W*.4,200,steps=5);pg.wait_for_timeout(4000);mx=ev('__sa.maxSpeed()');sp=[]
  for _ in range(40): sp.append(ev('__sa.shark.spd')/mx);ev('()=>{__sa.clearFood();__sa.shark.y=__sa.SURF+(__sa.BED-__sa.SURF)*.5}');pg.wait_for_timeout(200)
  pg.mouse.up();check(min(sp)>.97 and all(sp[i+1]>=sp[i]-.003 for i in range(len(sp)-1)),f'held drag keeps top speed for 8 s, never slows down over time ({min(sp):.3f}-{max(sp):.3f}; the start is just the weighty speed-up)')
  # sim: 60 s at full drive at sizes 1, 3, 6 -> top speed never drops (except net stun / surface bump, which are excluded)
  r=ev('''()=>{const out=[];for(const lv of [0,2,5]){__sa.startAs("white","endless");__sa.god=true;__sa.setLevel(lv);const s=__sa.shark,top0=__sa.maxSpeed();let mn=9,mxs=0,t=0,skip=0,top=top0;
     s.y=__sa.SURF+(__sa.BED-__sa.SURF)*.5;__sa.camY=s.y-innerHeight/2;
     __sa.sim(60,dt=>{t+=dt;__sa.timeLeft=999;s.meter=0;if(s.lvl!==lv)__sa.setLevel(lv);top=Math.max(top,__sa.maxSpeed());const y=s.y-__sa.SURF,deep=(__sa.BED-__sa.SURF);
       Object.assign(__sa.touch,{on:true,dir:Math.sin(t*.3)*.3+(y<deep*.3?.5:y>deep*.7?-.5:0),drive:1});if(s.stun>0||s.air||y<s.L*.5)skip=1.5;
       if(skip>0){skip-=dt;return}if(t>3){mn=Math.min(mn,s.spd/top0);mxs=Math.max(mxs,s.spd/top0)}});out.push({lv,mn,mxs,same:__sa.maxSpeed()===top0})}return out}''')
  for q in r: check(q['mn']>.97 and q['mxs']<=1+1e-6 and q['same'],f"size {q['lv']+1}: 60 s at full drive, speed stays at top ({q['mn']:.3f}-{q['mxs']:.3f}), top speed unchanged over time")
  # struggle still works while netted
  stage();ev('()=>{__sa.shark.stun=3}');s0=ev('__sa.shark.stun');pg.mouse.move(300,200);pg.mouse.down()
  for i in range(30): pg.mouse.move(300+(60 if i%2 else -60),200);pg.wait_for_timeout(16)
  pg.mouse.up();s1=ev('__sa.shark.stun');check(s1<s0-.5,f'netted: wiggling the finger still shortens the stun ({s0:.2f} -> {s1:.2f} s)')
  check(not errs,f'no page errors {errs[:2]}')
  b.close()
finally: srv.kill()
print(f'{passes} passed, {len(fails)} failed');sys.exit(1 if fails else 0)
