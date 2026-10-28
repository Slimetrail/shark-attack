# v8 tests: minnow start + growth gates, world scale (shark drawn same size, world shrinks), dead shark + red puff, perf at CPU x4.
# Run: python3 tests/test_v8.py   (port 8887)
import os,sys,subprocess,time
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT8','8887'))
URL=f'http://127.0.0.1:{PORT}/';SHOTS=os.environ.get('SA_SHOTS','/workspace/shark-shots');os.makedirs(SHOTS,exist_ok=True);passes=0;fails=[]
def check(c,m):
  global passes
  if c: passes+=1;print('PASS',m)
  else: fails.append(m);print('FAIL',m)
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.8)
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  for w,h in [(915,412),(844,390)]:
    tag=f'{w}x{h}';cx=b.new_context(viewport={'width':w,'height':h},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');pg=cx.new_page();errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)));ev=pg.evaluate
    pg.goto(URL);pg.wait_for_timeout(300);pg.click('#tap');pg.wait_for_function('window.__saTitleDone===true',timeout=8000)
    pg.click('#start');pg.wait_for_timeout(200);pg.click('.pick[data-type=white]');pg.wait_for_timeout(400);ev('__sa.god=true;__sa.timeLeft=999')
    G=ev('__sa.GROW');L0=ev('__sa.shark.L')
    check(ev('__sa.shark.lvl')==0 and abs(ev('__sa.worldK')-1/G['START'])<1e-6,f'{tag}: starts as a minnow (world drawn {1/G["START"]:.1f}x big)')
    if w==915: pg.wait_for_timeout(600);pg.screenshot(path=f'{SHOTS}/v8-minnow-start.png')
    # world scale: monotonic + shark drawn size fixed
    ks=ev('()=>{const o=[];for(let l=0;l<=__sa.MAX_LEVEL;l++)o.push(1/__sa.trueGrow(l));return o}')
    check(all(ks[i+1]<ks[i] for i in range(len(ks)-1)),f'{tag}: world scale shrinks every stage ({ks[0]:.2f} -> {ks[-1]:.2f})')
    # no popping: grow one level during play, sample per-frame change
    r=ev('''()=>{__sa.clearFood();const s=__sa.shark;s.x=innerWidth/2;s.y=__sa.SURF+innerHeight*.45;s.spd=0;const f=__sa.fish[3];__sa.setCreature(f,20,"fish");f.x=s.x+300;f.y=s.y;f.vx=0;
      const s0=f.s,k0=__sa.worldK;__sa.feed(__sa.need(0)/__sa.trait("grow")+.01);let mx=0,prev=__sa.worldK,Ls=[];for(let i=0;i<180;i++){__sa.sim(1/60);const k=__sa.worldK;mx=Math.max(mx,Math.abs(k/prev-1));prev=k;Ls.push(__sa.shark.L)}
      return {lvl:s.lvl,k0,k1:__sa.worldK,mx,ratio:f.s/s0,Lconst:Ls.every(x=>x===Ls[0])}}''')
    check(r['lvl']==1 and r['k1']<r['k0'] and r['mx']<.06,f'{tag}: growing eases the world smaller with no pop (max {r["mx"]*100:.1f}% per frame)')
    check(r['Lconst'] and ev('__sa.shark.L')==L0,f'{tag}: shark drawn size stays fixed while growing')
    check(abs(r['ratio']-r['k1']/r['k0'])<.01,f'{tag}: other creatures shrink by the same world factor')
    # eat rules use relative size: same true-size fish stays food/not-food across world scale
    rr=ev('''()=>{const f=__sa.fish[4];__sa.setLevel(2);__sa.setCreature(f,__sa.bite()*.8,"fish");const a=__sa.rel(f);__sa.setLevel(2);const b=__sa.rel(f);__sa.setCreature(f,__sa.bite()*1.3,"fish");const c=__sa.rel(f);__sa.setLevel(5);const d=__sa.rel(f);return [a,b,c,d]}''')
    check(rr[0]==-1 and rr[1]==-1 and rr[2]==1 and rr[3]==-1,f'{tag}: eat rules follow true relative size (rel {rr})')
    # surfers gated
    def leap(lvl):
      ev(f'''()=>{{__sa.setLevel({lvl});__sa.clearFood();const s=__sa.shark;s.x=innerWidth*.3;s.y=__sa.SURF+innerHeight*.06;s.ang=-Math.PI/2;s.spd=__sa.maxSpeed();s.run=innerHeight*.5;s.cool=0;Object.assign(__sa.touch,{{on:true,dir:-Math.PI/2,drive:1,lastMove:performance.now()+9e9}})}}''')
      pg.wait_for_function('__sa.shark.air',timeout=2000);ev('__sa.touch.on=false;__sa.surf[0].zip=0');s0=ev('__sa.surfersCaught')
      for i in range(40):
        ev('__sa.surf[0].zip>0||__sa.placeSurfer(0,__sa.shark.x+Math.cos(__sa.shark.ang)*__sa.shark.L*.48,0)');pg.wait_for_timeout(20)
        if ev('__sa.surfersCaught')>s0: break
      got=ev('__sa.surfersCaught')>s0;pg.wait_for_function('!__sa.shark.air',timeout=4000);return got
    check(not leap(0),f'{tag}: minnow leaping into a surfer cannot eat it ("Too small!")')
    check(not leap(G['SURF_LVL']-1),f'{tag}: one stage below the surfer size still cannot')
    check(leap(G['SURF_LVL']),f'{tag}: at stage {G["SURF_LVL"]} the shark eats a surfer')
    check(ev('__sa.canLaunch')!=None,'leap works at minnow size (checked above)')
    # screenshots mid + huge
    if w==915:
      ev('()=>{__sa.setLevel(4);const s=__sa.shark;s.y=__sa.SURF+innerHeight*.5;for(const f of __sa.fish)__sa.spawnFish(f,false)}');pg.wait_for_timeout(700);pg.screenshot(path=f'{SHOTS}/v8-mid-size.png')
      ev('()=>{__sa.setLevel(9);const s=__sa.shark;s.y=__sa.SURF+innerHeight*.2;s.x=innerWidth*.4;for(const f of __sa.fish)__sa.spawnFish(f,false);__sa.placeSurfer(0,innerWidth*.6,1);__sa.placeSurfer(1,innerWidth*.8,0)}');pg.wait_for_timeout(500);pg.screenshot(path=f'{SHOTS}/v8-huge-near-surfers.png')
      ev('()=>{__sa.setLevel(3);const s=__sa.shark;s.y=__sa.SURF+innerHeight*1.6;s.x=innerWidth*.35;s.spd=0;const c=__sa.fish[0];__sa.setCreature(c,__sa.bite()*2.2,"shark");c.x=s.x+260;c.y=s.y;c.vx=0}');pg.wait_for_timeout(500);pg.screenshot(path=f'{SHOTS}/v8-bigger-shark.png')
    # death: limp shark + red puff
    ev('__sa.god=false');ev('()=>{__sa.setLevel(1);const s=__sa.shark;s.spd=0;s.safe=0;s.ang=0;s.x=innerWidth*.4;s.y=__sa.SURF+innerHeight*.5;const c=__sa.fish[0];__sa.setCreature(c,__sa.bite()*2.5,"shark");c.x=s.x+60;c.y=s.y;c.vx=-200}')
    pg.wait_for_function('__sa.state==="dead"',timeout=3000);check(ev('__sa.endReason')=='eaten' and ev('__sa.shark.dead'),f'{tag}: touching a bigger shark -> dead state (no bouncing)')
    y0=ev('__sa.shark.y');pg.wait_for_timeout(450)
    red=ev('''()=>{const c=document.getElementById("c"),g=c.getContext("2d"),s=__sa.shark,d=devicePixelRatio,cy=(s.y-__sa.camY)*d,cx=s.x*d,R=s.L*.7*d;const im=g.getImageData(cx-R,cy-R,R*2,R*2).data;let n=0;for(let i=0;i<im.length;i+=16)if(im[i]>140&&im[i+1]<90&&im[i+2]<100)n++;return n}''')
    if w==915: pg.screenshot(path=f'{SHOTS}/v8-dead-red-puff.png')
    check(red>30,f'{tag}: red puff visible around the dead shark ({red} red samples)')
    check(ev('__sa.shark.y')>y0 and ev('__sa.state')=='dead',f'{tag}: dead shark sinks slowly')
    pg.wait_for_function('__sa.state==="over"',timeout=3000);check(pg.inner_text('#reason')=='Gulp!',f'{tag}: then the plain "Gulp!" end screen')
    check(not errs,f'{tag}: no page errors {errs[:2]}');cx.close()
  # perf at minnow start, busy screen, CPU x4 (same limits as before)
  cx=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,bypass_csp=True,service_workers='block');pg=cx.new_page();ev=pg.evaluate
  pg.goto(URL);pg.wait_for_timeout(300);pg.click('#tap');pg.wait_for_function('window.__saTitleDone===true',timeout=8000);pg.click('#start');pg.wait_for_timeout(200);pg.click('.pick[data-type=tiger]');pg.wait_for_timeout(300)
  ev('__sa.god=true;__sa.timeLeft=999');cdp=cx.new_cdp_session(pg);cdp.send('Emulation.setCPUThrottlingRate',{'rate':4})
  for lvl,name in [(0,'minnow'),(9,'huge')]:
    ev(f'()=>{{__sa.setLevel({lvl});const s=__sa.shark;s.y=__sa.SURF+innerHeight*.5;for(const f of __sa.fish){{__sa.spawnFish(f,false);f.y=s.y+(Math.random()-.5)*innerHeight*.8;f.x=Math.random()*innerWidth}}}}');pg.wait_for_timeout(400);ev('__sa.perf.reset()');pg.wait_for_timeout(3000)
    fr,js,st=ev('[__sa.perf.frames,__sa.perf.js/__sa.perf.frames,__sa.state]');print(f'PERF v8 {name} cpu x4: {fr} frames/3s, avg JS {js:.2f} ms/frame')
    check(st=='play' and fr>80 and js<2.5,f'perf at CPU x4 ({name}, busy screen): {fr} frames/3s, {js:.2f} ms/frame')
  b.close()
finally: srv.terminate()
print(passes,'passed,',len(fails),'failed');sys.exit(1 if fails else 0)
