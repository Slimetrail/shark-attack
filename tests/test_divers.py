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
    check(not errs,f'no page errors {errs[:2]}');b.close()
finally:
    srv.terminate()
print(f'\n{passes} passed, {len(fails)} failed')
sys.exit(1 if fails else 0)
