# b52 (Jeremy t1343u: "for shark no more divers"): divers, nets, the stun and the ambush are gone. This test asserts they NEVER appear.
# Run: /workspace/.pwvenv/bin/python tests/test_divers.py (port 8873, override with SA_PORT2). Pretend phone (Chromium touch emulation), never a real phone.
import subprocess,time,sys,os,re
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT2','8873'))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
URL=f'http://127.0.0.1:{PORT}/';fails=[];passes=0
def check(c,m):
    global passes
    print(('PASS ' if c else 'FAIL ')+m,flush=True)
    if c: passes+=1
    else: fails.append(m)
src=open(os.path.join(ROOT,'game.js'),encoding='utf8').read()
for w in ('drawDiver','spawnDiver','updDivers','netHit','startAmbush','struggle','DIVER_','AMBUSH_','"Caught!"','Nets stun','Divers are faster'):
    check(w not in src,f'game.js has no {w}')
try:
  with sync_playwright() as p:
    b=p.chromium.launch();cx=b.new_context(viewport={'width':844,'height':390},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block')
    pg=cx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(URL);pg.wait_for_timeout(500);pg.touchscreen.tap(422,195);pg.wait_for_timeout(300)
    for mode in ('timed','endless'):
        pg.evaluate(f'__sa.startAs("white","{mode}");__sa.god=true')
        r=pg.evaluate('''(()=>{for(let i=0;i<30;i++)__sa.surferCaught();let maxStun=0;__sa.sim(40,dt=>{maxStun=Math.max(maxStun,__sa.shark.stun||0)});return {st:__sa.state,why:__sa.endReason,maxStun,keys:["divers","amb","netHits","spawnDiver","DIV","struggle"].filter(k=>k in __sa)}})()''')
        check(r['keys']==[],f'{mode}: no diver/net/ambush hooks {r["keys"]}')
        check(r['maxStun']==0,f'{mode}: 30 surfers caught + 40 s of play, the shark is never stunned')
        check(r['why']!='caught',f'{mode}: never ends with Caught! ({r["st"]}/{r["why"]})')
    # b53: restored from the b51 test (e5e9b4f, ~118 lines cut in b52), adapted to "no divers ever": real UI flow, surfers caught one by one,
    # no Divers banner / net / stun / slow-down, never "Caught!", Play again resets, perf with many surfers caught (cpu x1 and x4).
    cx2=b.new_context(viewport={'width':915,'height':412},device_scale_factor=2,has_touch=True,is_mobile=True,bypass_csp=True,service_workers='block');pg=cx2.new_page()
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and 'Service Worker' not in m.text and errs.append(m.text))
    pg.goto(URL+'?round=300');pg.wait_for_timeout(300);pg.click('#tap');pg.wait_for_function('window.__saTitleDone===true',timeout=15000)
    pg.click('#start');pg.wait_for_timeout(150);pg.click('.pick[data-type=white]');pg.wait_for_timeout(250)
    check(pg.evaluate('__sa.state')=='play','real UI flow: Start, pick Great White, playing')
    how=pg.evaluate('document.body.innerText');check(re.search(r'\bdivers?\b|\bnets?\b|stun',how,re.I) is None,'no diver / net / stun words anywhere on the page')
    calm='()=>{__sa.clearFood();const s=__sa.shark;s.x=innerWidth/2;s.y=__sa.SURF+innerHeight*.45;s.spd=0;s.ang=0;__sa.touch.on=false}'
    pg.evaluate(calm);m0=pg.evaluate('__sa.maxSpeed()')
    for n in (3,6,18):
        while pg.evaluate('__sa.surfersCaught')<n: pg.evaluate('__sa.surferCaught()')
        pg.wait_for_timeout(250);txt=pg.evaluate('document.body.innerText')
        check('Diver' not in txt and pg.evaluate('(__sa.shark.stun||0)')==0 and pg.evaluate('__sa.state')=='play',f'{n} surfers caught: no Divers banner, no stun, still playing')
    check(abs(pg.evaluate('__sa.maxSpeed()')-m0)<1e-6,'catching surfers never slows the shark (no net)')
    pg.evaluate('__sa.timeLeft=0.01');pg.wait_for_selector('#again',state='visible',timeout=8000)
    check(pg.inner_text('#reason')!='Caught!' and pg.evaluate('__sa.endReason')!='caught' and pg.inner_text('#final')!='',f'round ends normally, never Caught! ({pg.inner_text("#reason")!r})')
    pg.click('#again');pg.wait_for_timeout(250);check(pg.evaluate('__sa.surfersCaught')==0 and pg.evaluate('__sa.state')=='play','Play again resets the surfer count')
    cdp=cx2.new_cdp_session(pg)
    for rate in (1,4):
        cdp.send('Emulation.setCPUThrottlingRate',{'rate':rate});pg.evaluate(calm);pg.evaluate('()=>{for(let i=0;i<9;i++)__sa.surferCaught();__sa.god=true;__sa.perf.reset()}')
        pg.wait_for_timeout(3000);pf=pg.evaluate('({f:__sa.perf.frames,js:__sa.perf.js,st:__sa.state})')
        print(f"PERF 9+ surfers caught cpu x{rate}: {pf['f']} frames/3s, avg JS {pf['js']/max(1,pf['f']):.2f} ms/frame",flush=True)
        check(pf['st']=='play' and pf['js']/max(1,pf['f'])<2.5 and pf['f']>80,f'perf ok after many surfers caught at cpu x{rate} (no diver/ambush cost)')
    cdp.send('Emulation.setCPUThrottlingRate',{'rate':1});cx2.close()
    check(not errs,f'no page errors {errs[:2]}');b.close()
finally:
    srv.terminate()
print(f'\n{passes} passed, {len(fails)} failed')
sys.exit(1 if fails else 0)
