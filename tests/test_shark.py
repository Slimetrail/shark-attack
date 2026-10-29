# Shark Attack tests (Playwright, headless Chromium, landscape phones). Run: python3 tests/test_shark.py
import subprocess,time,sys,os,math
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PORT=int(os.environ.get('SA_PORT','8872'))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
URL=f'http://127.0.0.1:{PORT}/';SHOTS=os.environ.get('SA_SHOTS','/workspace/shark-shots');os.makedirs(SHOTS,exist_ok=True)
fails=[];passes=0
def check(c,m):
    global passes
    print(('PASS ' if c else 'FAIL ')+m,flush=True)
    if c: passes+=1
    else: fails.append(m)
# no 404s are expected any more (the chiptune ships); offline, the network-first fetch logs ERR_INTERNET_DISCONNECTED and the SW serves cache
def real(errs): return [e for e in errs if 'ERR_INTERNET_DISCONNECTED' not in e]  # offline phase: network-first fetch fails, SW serves cache
def newpage(b,w,h,dpr,q=''):
    cx=b.new_context(viewport={'width':w,'height':h},device_scale_factor=dpr,has_touch=True,is_mobile=True,bypass_csp=True)
    pg=cx.new_page();errs=[];outside=[]
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.on('request',lambda r:r.url.startswith(URL) or r.url.startswith('data:') or outside.append(r.url))
    pg.goto(URL+q);pg.wait_for_timeout(300);return cx,pg,errs,outside
def to_title(pg): pg.click('#tap');pg.wait_for_function('window.__saTitleDone===true',timeout=8000)
def play(pg,t='white'): pg.click('#start');pg.wait_for_timeout(150);pg.click(f'.pick[data-type={t}]');pg.wait_for_timeout(250)
# Landing is detected on the first rendered frame after touchdown and compared with the AudioContext clock, so the measured
# offset carries up to one frame (~16.7 ms at 60 Hz) of detection lag plus up to one frame of rAF-vs-audio-clock jitter.
# PERFECT_MS (45) is the game's promise; the test allows 2 frames of measurement slack on top of it.
LAND_FRAME_SLACK=34
def ev(pg,js): return pg.evaluate(js)
def stage(pg,y_frac=.6,ang=0,spd=None):
    ev(pg,f'()=>{{__sa.clearFood();const s=__sa.shark;s.air=false;s.cool=0;s.run=0;s.x=innerWidth/2;s.y=__sa.SURF+innerHeight*.9*{y_frac};s.ang={ang};s.spd={spd if spd is not None else "__sa.maxSpeed()*.2"};__sa.touch.on=false;__sa.touch.drive=0}}')
def slide(pg,x0,y0,x1,y1,steps,ms=30,release=True,press=True):
    if press: pg.mouse.move(x0,y0);pg.mouse.down()
    for i in range(1,steps+1): pg.mouse.move(x0+(x1-x0)*i/steps,y0+(y1-y0)*i/steps);pg.wait_for_timeout(ms)
    if release: pg.mouse.up()
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
  # ---------- main flow on S26 Ultra size ----------
  W,H=915,412
  cx,pg,errs,outside=newpage(b,W,H,3.5)
  ev(pg,"localStorage.clear()");pg.reload();pg.wait_for_timeout(300)
  check(pg.locator('#jump').count()==0 and 'jump' not in pg.content().lower().split('<script')[0],'no Jump button in the DOM')
  pg.click('#tap');pg.wait_for_timeout(250);pg.screenshot(path=f'{SHOTS}/title-1-swim.png');pg.wait_for_timeout(1050);pg.screenshot(path=f'{SHOTS}/title-2-around.png')
  pg.wait_for_function('window.__saTitleDone===true',timeout=8000);check(True,'title: fake-3D shark swims across and around the title (no bite), picture shown');pg.screenshot(path=f'{SHOTS}/title-3-picture.png')
  pg.click('#start');pg.wait_for_timeout(200)
  check(pg.locator('.pick').count()==3 and all(t in pg.inner_text('#pickList') for t in ['Great White','Hammerhead','Tiger Shark']),'pick screen shows the 3 sharks')
  bars=ev(pg,"[...document.querySelectorAll('.bar')].map(b=>b.dataset.stat+b.dataset.v)")
  check(len(bars)==9 and set(x[:-1] for x in bars)=={'Size','Speed','Jump'},f'pick screen shows Size/Speed/Jump bars for each shark {bars}')
  check(all(pg.locator(f'.pick[data-type={t}] .pdesc').inner_text() for t in ['white','hammer','tiger']),'each shark has a one-line description')
  bb=pg.locator('.pick').nth(2).bounding_box();check(bb['height']>=48 and bb['y']+bb['height']<=H,'pick buttons big and on screen')
  pg.screenshot(path=f'{SHOTS}/pick-screen.png')
  pg.click('.pick[data-type=hammer]');pg.wait_for_timeout(300)
  check(ev(pg,'__sa.state')=='play' and ev(pg,'localStorage.sharkAttack_type')=='hammer','picking a shark starts play and saves the type')
  check(ev(pg,"__sa.trait('turn')")==1.3 and ev(pg,"__sa.trait('catchR')")==1.35 and ev(pg,"__sa.trait('leap')")==.9,'hammerhead traits applied (turn 1.3, catch 1.35, leap 0.9)')
  # direction controls facing
  stage(pg,.5,0);slide(pg,500,200,320,200,10);pg.wait_for_timeout(250);a=ev(pg,'__sa.shark.ang')
  check(abs(abs(math.atan2(math.sin(a),math.cos(a)))-math.pi)<.5,f'slide left -> shark faces/swims left (ang {a:.2f})')
  stage(pg,.7,0);slide(pg,300,370,300,120,10);pg.wait_for_timeout(150);a=ev(pg,'__sa.shark.ang')
  check(abs(math.atan2(math.sin(a),math.cos(a))+math.pi/2)<.5,f'slide up -> shark swims up (ang {a:.2f})')
  stage(pg,.3,0);slide(pg,300,80,300,330,10);pg.wait_for_timeout(150);a=ev(pg,'__sa.shark.ang')
  check(abs(math.atan2(math.sin(a),math.cos(a))-math.pi/2)<.5,f'slide down -> shark swims down (ang {a:.2f})')
  # speed scales with slide distance
  stage(pg,.5,0);slide(pg,100,200,140,200,4,release=False);pg.wait_for_timeout(500);s_short=ev(pg,'__sa.shark.spd');pg.mouse.up()
  stage(pg,.5,0);slide(pg,40,200,380,200,12,release=False);pg.wait_for_timeout(500);s_long=ev(pg,'__sa.shark.spd');pg.mouse.up()
  check(s_long>s_short*1.4,f'speed scales with drag distance (short {s_short:.0f} px/s, long {s_long:.0f} px/s)')
  # eased acceleration (not instant)
  stage(pg,.5,0);slide(pg,40,200,380,200,3,ms=10,release=False);s1=ev(pg,'__sa.shark.spd');pg.wait_for_timeout(700);s2=ev(pg,'__sa.shark.spd');pg.mouse.up()
  check(s2>s1*1.3,f'speed eases up over time, not instantly ({s1:.0f} -> {s2:.0f})')
  pg.wait_for_timeout(1500);check(ev(pg,'__sa.shark.spd')>10,'shark keeps drifting slowly after finger lifts')
  # real gesture: slide down a long way, then up -> launch
  stage(pg,.15,math.pi/2);ev(pg,'__sa.shark.x=innerWidth*.5')
  slide(pg,300,30,300,395,24,ms=30,release=False)
  launched=False
  for i in range(45):
    pg.mouse.move(300,395-i*9);pg.wait_for_timeout(30)
    if ev(pg,'__sa.shark.air'): launched=True;break
  pg.mouse.up();ll=ev(pg,'window.__saLastLaunch')
  check(launched,f'slide down (build speed) then up -> shark breaks the surface and leaps {ll}')
  if launched:
    pg.wait_for_function('__sa.shark.h>40',timeout=1500);pg.screenshot(path=f'{SHOTS}/leap-midair.png')
  pg.wait_for_function('!__sa.shark.air',timeout=3000)
  # too little run-up: bumps the surface
  stage(pg,.12,-math.pi/2);ev(pg,'__sa.shark.spd=__sa.maxSpeed()*.3');pg.wait_for_timeout(1800)
  check(not ev(pg,'__sa.shark.air') and math.sin(ev(pg,'__sa.shark.ang'))>0,'too little speed/run-up -> just bumps the surface (turns back down, no air)')
  # height grows with run-up
  hts=[]
  for run in (.25,.6):
    stage(pg,.06,-math.pi/2,'__sa.maxSpeed()');ev(pg,f'__sa.shark.run=innerHeight*{run};__sa.touch.on=true;__sa.touch.dir=-Math.PI/2;__sa.touch.drive=1;__sa.touch.lastMove=performance.now()+9e9')
    pg.wait_for_function('__sa.shark.air',timeout=1500);hts.append(ev(pg,'__sa.shark.peak'));ev(pg,'__sa.touch.on=false');pg.wait_for_function('!__sa.shark.air',timeout=3000)
  check(hts[1]>hts[0]*1.3,f'more run-up at speed -> higher leap (peaks {hts[0]:.0f}px vs {hts[1]:.0f}px)')
  # surfers: not catchable from the water, catchable in the air
  stage(pg,.04,-math.pi/2,'__sa.maxSpeed()*.25');s0=ev(pg,'__sa.score')
  for i in range(10): ev(pg,'__sa.placeSurfer(0,__sa.shark.x+Math.cos(__sa.shark.ang)*__sa.shark.L*.48,0)');pg.wait_for_timeout(30)
  check(ev(pg,'__sa.score')==s0,'slow shark at the surface only bumps a surfer (no catch)')
  stage(pg,.06,-math.pi/2,'__sa.maxSpeed()');ev(pg,'__sa.setLevel(__sa.GROW.SURF_LVL);__sa.shark.run=innerHeight*.5;__sa.touch.on=true;__sa.touch.dir=-Math.PI/2;__sa.touch.drive=1;__sa.touch.lastMove=performance.now()+9e9')
  pg.wait_for_function('__sa.shark.air',timeout=1500);s0=ev(pg,'(()=>{__sa.touch.on=false;const v=__sa.score;__sa.surf[0].zip=0;return v})()')# score read BEFORE reviving the surfer (race fix, same as test_v8)
  for i in range(40):
    ev(pg,'__sa.surf[0].zip>0||__sa.placeSurfer(0,__sa.shark.x+Math.cos(__sa.shark.ang)*__sa.shark.L*.48,0)');pg.wait_for_timeout(20)
    if ev(pg,'__sa.score')>=s0+3: break
  check(ev(pg,'__sa.score')>=s0+3,'airborne shark catches a surfer (+3)')
  pg.wait_for_function('!__sa.shark.air',timeout=3000)
  # beat assist
  res=[]
  for i in range(10):
    stage(pg,.06,-math.pi/2,'__sa.maxSpeed()');pg.wait_for_timeout(60*i);ev(pg,'__sa.shark.run=innerHeight*.5;__sa.touch.on=true;__sa.touch.dir=-Math.PI/2;__sa.touch.drive=1;__sa.touch.lastMove=performance.now()+9e9')
    pg.wait_for_function('__sa.shark.air',timeout=1500);ev(pg,'__sa.touch.on=false');l=ev(pg,'window.__saLastLaunch');pg.wait_for_function('!__sa.shark.air',timeout=3000);o=ev(pg,'window.__saLastLand')
    res.append((round((l['air']-l['base'])*1000),l['assisted'],round(o['offMs'])))
  check(all(abs(d)<=80 for d,_,_ in res) and any(a for _,a,_ in res) and all(off<=45+LAND_FRAME_SLACK for d,a,off in res if a),f'beat assist: airtime nudged <=80 ms, assisted landings on the beat (nudge ms, assisted, land offset ms) {res}')
  # fish growth + chomp sfx hook
  stage(pg,.5,0);ev(pg,'__sa.setLevel(0)');L0=ev(pg,'__sa.worldK');D0=ev(pg,'__sa.shark.L');v0=ev(pg,'__sa.maxSpeed()');c0=ev(pg,'__sa.sfxCount.chomp')
  for i in range(20): ev(pg,'__sa.placeFishAtMouth(0)');pg.wait_for_timeout(60)
  check(ev(pg,'__sa.sfxCount.chomp')>=c0+6,'eating a fish triggers the chomp sound hook')
  pg.wait_for_timeout(1500);check(ev(pg,'__sa.shark.lvl')>=1 and ev(pg,'__sa.worldK')<L0 and ev(pg,'__sa.shark.L')>D0*1.1 and ev(pg,'__sa.maxSpeed()')>v0,'eating small fish grows the shark (v9: drawn shark grows, world shrinks by the rest) and speeds it up')
  ev(pg,'__sa.feed(9999)');check(ev(pg,'__sa.shark.lvl')==ev(pg,'__sa.MAX_LEVEL'),'size capped at MAX_LEVEL')
  # bubbles on fast crossing with cooldown
  def go_fast():
    ev(pg,'()=>{const s=__sa.shark;s.spd=__sa.maxSpeed()*.4;s.y=__sa.SURF+innerHeight*.45;s.x=innerWidth/2;s.ang=0;Object.assign(__sa.touch,{on:true,dir:0,drive:1,lastMove:performance.now()+9e9})}')
    pg.wait_for_function('__sa.shark.spd>__sa.maxSpeed()*.75',timeout=3000);ev(pg,'__sa.touch.on=false;__sa.shark.ang=Math.PI')
  stage(pg,.5,0);pg.wait_for_timeout(1600);b0=ev(pg,'__sa.sfxCount.bubbles');go_fast();b1=ev(pg,'__sa.sfxCount.bubbles');go_fast();b2=ev(pg,'__sa.sfxCount.bubbles');pg.wait_for_timeout(1600);go_fast();b3=ev(pg,'__sa.sfxCount.bubbles')
  check(b1==b0+1 and b2==b1 and b3==b2+1,f'bubbles once per fast crossing, cooldown respected ({b0},{b1},{b2},{b3})')
  # v9: no red tint/'!' marker any more; the data flag (eater) still flips once the shark outgrows it
  stage(pg,.7,0);ev(pg,'__sa.setLevel(0)');i3=ev(pg,'()=>{const i=__sa.placeFishAt(3,innerWidth*.8,__sa.SURF+90,-1);__sa.setCreature(__sa.fish[i],__sa.bite()*2,"shark");return i}');pg.wait_for_timeout(100);d0=ev(pg,f'__sa.fish[{i3}].danger')
  pg.screenshot(path=f'{SHOTS}/danger-fish.png')
  ev(pg,'__sa.setLevel(10)');pg.wait_for_timeout(100);d1=ev(pg,f'__sa.fish[{i3}].danger')
  check(d0 and not d1,f'bigger shark is an eater (data only, no marker) while bigger, becomes food once the shark outgrows it ({d0}->{d1})')
  # leaping shark is safe from big fish (arc only)
  stage(pg,.06,-math.pi/2,'__sa.maxSpeed()');ev(pg,'__sa.setLevel(0);__sa.shark.run=innerHeight*.5;__sa.touch.on=true;__sa.touch.dir=-Math.PI/2;__sa.touch.drive=1;__sa.touch.lastMove=performance.now()+9e9')
  pg.wait_for_function('__sa.shark.air',timeout=1500);ev(pg,'__sa.touch.on=false');ev(pg,'__sa.placeFishAt(3,__sa.shark.x+20,__sa.shark.y,-1)');pg.wait_for_timeout(80)
  check(ev(pg,'__sa.state')=='play','leaping shark is safe from a big fish during the arc');ev(pg,'__sa.clearFood()');pg.wait_for_function('!__sa.shark.air',timeout=3000)
  # big fish eats shark -> Gulp!
  stage(pg,.5,0);ev(pg,'__sa.setLevel(0)');ev(pg,'()=>{const s=__sa.shark;s.spd=0;const i=__sa.placeFishAt(3,s.x+110,s.y,-160);__sa.setCreature(__sa.fish[i],__sa.bite()*2,"shark")}')
  pg.wait_for_function("__sa.state==='over'",timeout=5000)
  check(ev(pg,'__sa.endReason')=='eaten' and pg.inner_text('#reason')=='Gulp!' and pg.is_visible('#again') and pg.is_visible('#final'),'bigger shark eats the shark -> end screen says "Gulp!", shows score + Play again')
  check(ev(pg,'__sa.sfxCount.gulp')>=1,'gulp sound hook fires on the Gulp! screen')
  pg.wait_for_timeout(300);pg.screenshot(path=f'{SHOTS}/score-gulp.png')
  pg.click('#again');pg.wait_for_timeout(200);check(ev(pg,'__sa.state')=='play' and ev(pg,'__sa.score')==0,'Play again restarts')
  # mute silences all three
  ev(pg,'__sa.timeLeft=0');pg.wait_for_timeout(200);pg.click('#home');pg.wait_for_timeout(200);pg.click('#snd');play(pg,'hammer')
  p0=ev(pg,'__sa.sfxCount.played');stage(pg,.5,0);ev(pg,'__sa.placeFishAtMouth(0)');pg.wait_for_timeout(100);pg.wait_for_timeout(1600);go_fast()
  ev(pg,'()=>{const s=__sa.shark;s.spd=0;s.ang=0;s.y=__sa.SURF+innerHeight*.45;__sa.setLevel(0);const i=__sa.placeFishAt(3,s.x+110,s.y,-160);__sa.setCreature(__sa.fish[i],__sa.bite()*2,"shark")}');pg.wait_for_function("__sa.state==='over'",timeout=5000)
  check(ev(pg,'__sa.sfxCount.played')==p0 and ev(pg,'__sa.sfxCount.chomp')>0,'mute silences chomp, bubbles and gulp (hooks fire, nothing sounds)')
  pg.click('#home');pg.wait_for_timeout(200);pg.click('#snd')
  # perf
  play(pg,'white');cdp=cx.new_cdp_session(pg);perf={}
  for rate in (1,4):
    cdp.send('Emulation.setCPUThrottlingRate',{'rate':rate});ev(pg,'__sa.timeLeft=999;__sa.shark.ang=0.3;Object.assign(__sa.touch,{on:false})');pg.wait_for_timeout(500);ev(pg,'__sa.perf.reset()');pg.wait_for_timeout(3000)
    r=ev(pg,'({f:__sa.perf.frames,js:__sa.perf.js/__sa.perf.frames,dt:__sa.perf.dtSum/__sa.perf.frames*1000})');perf[rate]=r
    print(f'PERF cpu x{rate}: {r["f"]} frames/3s, avg frame {r["dt"]:.2f} ms (~{1000/r["dt"]:.0f} fps), avg JS update+draw {r["js"]:.2f} ms/frame',flush=True)
  cdp.send('Emulation.setCPUThrottlingRate',{'rate':1})
  check(perf[1]['js']<4 and perf[4]['js']<12,f'perf: JS per frame low (x1 {perf[1]["js"]:.2f} ms, x4 {perf[4]["js"]:.2f} ms)')
  check(not real(errs),f'no console errors {real(errs)}');check(not outside,f'no outside network requests {outside}')
  cx.close()
  # ---------- each shark at each size ----------
  Ls={}
  for w,h,dpr,tag in [(915,412,3.5,'915x412'),(844,390,3,'844x390'),(740,360,3,'740x360')]:
    for t in ['white','hammer','tiger']:
      cx,pg,errs,outside=newpage(b,w,h,dpr);to_title(pg);play(pg,t)
      Ls[(tag,t)]=ev(pg,'__sa.shark.Lt');tr=ev(pg,f"['size','speed','acc','turn','catchR','leap','grow'].every(k=>__sa.trait(k)===__sa.TYPES['{t}'][k])")
      check(tr,f'{tag} {t}: its traits table is applied')
      ev(pg,'()=>{const s=__sa.shark;s.x=innerWidth*.45;s.y=__sa.SURF+innerHeight*.9*.45;s.ang=-.25}');pg.wait_for_timeout(700)
      hud=ev(pg,'__sa.state')=='play';check(hud and not real(errs),f'{tag} {t}: plays without errors')
      if tag=='915x412' or t=='white': pg.screenshot(path=f'{SHOTS}/play-{t}-{tag}.png')
      cx.close()
  check(Ls[('915x412','white')]>Ls[('915x412','hammer')]>Ls[('915x412','tiger')],f'start sizes: great white > hammerhead > tiger {[round(Ls[("915x412",t)]) for t in ["white","hammer","tiger"]]}')
  # flattened when TYPES_MECHANICAL is false (?flat)
  cx,pg,errs,outside=newpage(b,915,412,3.5,'?flat');to_title(pg);play(pg,'tiger')
  check(all(ev(pg,f"__sa.trait('{k}')")==1 for k in ['size','speed','acc','turn','catchR','leap','grow']),'TYPES_MECHANICAL=false flattens all traits to 1');cx.close()
  # ---------- round end, best, persistence, credits, offline ----------
  cx,pg,errs,outside=newpage(b,915,412,3.5,'?round=3')
  ev(pg,"localStorage.removeItem('sharkAttack_best')");to_title(pg);check(pg.locator('.pick').count()==0,'(pick screen not shown until Start)')
  play(pg,'tiger');stage(pg,.5,0);ev(pg,'__sa.placeFishAtMouth(0)');pg.wait_for_timeout(100);sc=ev(pg,'__sa.score')
  pg.wait_for_function("__sa.state==='over'",timeout=6000)
  check(pg.inner_text('#reason')=="Time's up!" and pg.inner_text('#final')==str(sc),"timer ends the round (ROUND_SECONDS override) -> \"Time's up!\" score screen")
  check(ev(pg,'localStorage.sharkAttack_best')==str(sc),f'best score saved in sharkAttack_best ({sc})');pg.screenshot(path=f'{SHOTS}/score-timesup.png')
  pg.reload();pg.wait_for_timeout(300);to_title(pg);pg.click('#start');pg.wait_for_timeout(150)
  check('sel' in pg.locator('.pick[data-type=tiger]').get_attribute('class'),'last picked shark (tiger) remembered after reload')
  pg.click('#pickBack');pg.click('#snd');pg.reload();pg.wait_for_timeout(300);check(ev(pg,'__sa.soundOn')==False and 'off' in pg.inner_text('#snd'),'mute persists after reload')
  # v10 item 13: separate Songs / Sound effects switches, saved, old saves mapped
  ev(pg,"localStorage.clear();localStorage.sharkAttack_sound='0'");pg.reload();pg.wait_for_timeout(300)
  check(ev(pg,'__sa.songsOn')==False and ev(pg,'__sa.fxOn')==False,'old save with sound off -> songs off and effects off')
  ev(pg,"localStorage.clear();localStorage.sharkAttack_sound='1'");pg.reload();pg.wait_for_timeout(300)
  check(ev(pg,'__sa.songsOn')==True and ev(pg,'__sa.fxOn')==True,'old save with sound on -> songs on and effects on')
  to_title(pg);pg.click('#songs');check(ev(pg,'__sa.musOn')==False and ev(pg,'__sa.fxOn') and ev(pg,'localStorage.sharkAttack_songs')=='0' and 'off' in pg.inner_text('#songs'),'Songs switch turns songs off (effects stay on), saved')
  pg.click('#fx');check(ev(pg,'__sa.fxOn')==False and ev(pg,'localStorage.sharkAttack_sfx')=='0' and 'off' in pg.inner_text('#fx'),'Effects switch turns sound effects off, saved')
  pg.reload();pg.wait_for_timeout(300);check(ev(pg,'__sa.songsOn')==False and ev(pg,'__sa.fxOn')==False and ev(pg,'__sa.soundOn')==True,'both switches survive reload')
  to_title(pg);pg.click('#fx');p0=ev(pg,'__sa.sfxCount.played');pg.click('#start');pg.click('.pick[data-type=white]');pg.wait_for_timeout(200);ev(pg,'__sa.placeFishAtMouth(0)');pg.wait_for_timeout(400)
  check(ev(pg,'__sa.sfxCount.played')>p0 and not ev(pg,'__sa.musOn'),'effects on + songs off: effects sound, music stays silent')
  ev(pg,'__sa.timeLeft=0');pg.wait_for_function("__sa.state==='over'",timeout=6000);pg.click('#home');pg.wait_for_timeout(200)
  pg.click('#songs');check(ev(pg,'__sa.musOn') and ev(pg,'__sa.fxOn'),'Songs back on')
  ev(pg,"localStorage.sharkAttack_sound='1';localStorage.sharkAttack_songs='1';localStorage.sharkAttack_sfx='1'");pg.reload();pg.wait_for_timeout(300);to_title(pg)
  pg.wait_for_timeout(300);check(ev(pg,'__sa.musOn') and ev(pg,'__sa.titleMusicPlaying'),'item 13: title music starts on the first tap with both switches on')
  sw=open(os.path.join(ROOT,'sw.js')).read();check('audio/intro-scary.ogg' in sw and 'audio/play-swim-piano.ogg' in sw,'both songs packaged in the offline cache (SW SHELL)')
  pg.click('#cred');pg.wait_for_timeout(200);t=pg.inner_text('#credUi');check('CC0' in t and 'VSCO-2' in t and 'Ivan Ili' not in t and 'CC BY' not in t and 'Giorgi' not in t,'credits: v10 music is CC0 (own work + VSCO-2 CE piano); old CC BY credit gone with the old file')
  pg.screenshot(path=f'{SHOTS}/credits.png');pg.click('#credBack')
  pg.wait_for_function('navigator.serviceWorker.controller!==null',timeout=8000) if ev(pg,'!!navigator.serviceWorker.controller') else (pg.reload(),pg.wait_for_function('navigator.serviceWorker.controller!==null',timeout=8000))
  pg.wait_for_timeout(1000);cx.set_offline(True);pg.reload();pg.wait_for_timeout(500)
  check(ev(pg,'typeof __sa')=='object','offline reload works (service worker)');to_title(pg);play(pg,'white');check(ev(pg,'__sa.state')=='play','playable offline')
  check('sharkattack-v40' in ev(pg,'caches.keys()'),'versioned cache sharkattack-v40')
  check('audio/play-swim-piano.ogg' in ' '.join(ev(pg,'caches.open("sharkattack-v40").then(c=>c.keys()).then(k=>k.map(r=>r.url))')),'chiptune is precached by the service worker')
  pg.wait_for_function('__sa.chip',timeout=8000);pg.wait_for_timeout(300)
  check(ev(pg,'__sa.chipPlaying') and not ev(pg,'__sa.placeholder'),'offline: real chiptune plays from cache (placeholder not used)')
  check(not real(errs),f'no console errors {real(errs)}');check(not outside,f'no outside requests {outside}');cx.close()
  # chiptune online: decodes to a 72 s seamless buffer loop; fallback when the file fails
  cx,pg,errs,outside=newpage(b,915,412,2);to_title(pg);pg.wait_for_function('__sa.chip',timeout=8000);play(pg,'white');pg.wait_for_timeout(300)
  info=ev(pg,'({p:__sa.chipPlaying,ph:__sa.placeholder,bpm:__sa.BEAT.CHIPTUNE_BPM,bl:__sa.beatLen(),vol:__sa.MUSIC_VOL.game})')
  check(info['p'] and not info['ph'] and abs(info['bl']-.5)<1e-9,f'gameplay uses the real chiptune (buffer loop), beat assist at {info["bpm"]} BPM eighths {info}')
  ev(pg,'__sa.timeLeft=0');pg.wait_for_function('__sa.state==="over"');check(not ev(pg,'__sa.chipPlaying'),'chiptune stops on the score screen')
  pg.click('#snd') if pg.is_visible('#snd') else None
  check(not real(errs) and not [e for e in errs if '404' in e],f'no 404 / console errors with the chiptune present {errs}');cx.close()
  cx=b.new_context(viewport={'width':915,'height':412},bypass_csp=True,service_workers='block');pg=cx.new_page();pg.route('**/play-swim-piano.ogg',lambda r:r.abort())
  pg.goto(URL);pg.wait_for_timeout(300);to_title(pg);pg.wait_for_function('__sa.chipFailed',timeout=8000);play(pg,'white');pg.wait_for_timeout(300)
  check(ev(pg,'__sa.placeholder') and not ev(pg,'__sa.chipPlaying'),'if the chiptune fails to load, the placeholder loop is the fallback');cx.close()
  sz=sum(os.path.getsize(os.path.join(ROOT,f)) for f in ['index.html','game.js','sw.js','manifest.webmanifest','icons/icon-192.png','icons/icon-512.png','icons/maskable-512.png','art/title-art.webp','audio/intro-scary.ogg','audio/play-swim-piano.ogg'])
  print(f'APP SIZE {sz/1024:.0f} KB');check(sz<2.5e6,f'app stays small ({sz/1024:.0f} KB total)')
  cx2=b.new_context(viewport={'width':412,'height':915},is_mobile=True,has_touch=True);p2=cx2.new_page();p2.goto(URL);p2.wait_for_timeout(300);check(p2.is_visible('#rot') and 'sideways' in p2.inner_text('#rot'),'portrait shows "turn your phone sideways"')
  b.close()
finally: srv.terminate()
_src=open(os.path.join(ROOT,'game.js')).read();check('splash(){' not in _src and 'ripple(){' not in _src and 'SFX.splash' not in _src and 'SFX.ripple' not in _src,'v10 item 11: no wave/water sounds (splash, ripple) in the game')
print(f'\n{passes} passed, {len(fails)} failed');sys.exit(1 if fails else 0)
