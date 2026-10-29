#!/usr/bin/env python3
"""Build the separate "Shark Attack TEST" PWA from the committed files (git HEAD) into /workspace/shark-attack-test-deploy.
Usage: python3 tools/make_test_build.py [N] [--out DIR] [--build ID]
 - N is the TEST version number shown on the title screen ("TEST vN"); default: commits on this branch since v7.
 - Meant to be served at /shark-attack-test/ (manifest id, start_url and scope are relative to that folder).
 - Separate from the live game: cache prefix "sa-test-" (the live game uses "sharkattack-v…"; live v7 deletes every
   cache starting with "sharkattack-", so the test prefix must NOT start with that) and localStorage prefix "saTEST_".
Nothing is uploaded or pushed; this only writes local files."""
import os,re,sys,json,shutil,subprocess,io,tarfile,argparse
from PIL import Image,ImageDraw,ImageFont
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap=argparse.ArgumentParser();ap.add_argument('n',nargs='?',type=int);ap.add_argument('--out',default='/workspace/shark-attack-test-deploy');ap.add_argument('--build');ap.add_argument('--worktree',action='store_true',help='use working tree instead of HEAD (tests only)')
a=ap.parse_args()
git=lambda *x:subprocess.check_output(['git',*x],cwd=ROOT).decode().strip()
sha=git('rev-parse','--short','HEAD')
n=a.n if a.n is not None else int(git('rev-list','--count','08993fa..HEAD') or 0)
build=a.build or f't{n}-{sha}'
SHIP=['index.html','game.js','sw.js','manifest.webmanifest','version.json','icons/icon-192.png','icons/icon-512.png','icons/maskable-512.png','audio/title-cathedrale.ogg','audio/gameplay-chiptune.ogg','AUDIO-LICENSES.md']
out=a.out
if os.path.exists(out):shutil.rmtree(out)
os.makedirs(out)
def src(p):
 if a.worktree:return open(os.path.join(ROOT,p),'rb').read()
 return subprocess.check_output(['git','show','HEAD:'+p],cwd=ROOT)
for p in SHIP:
 try:data=src(p)
 except Exception:
  if p=='AUDIO-LICENSES.md':continue
  raise
 os.makedirs(os.path.dirname(os.path.join(out,p)) or out,exist_ok=True);open(os.path.join(out,p),'wb').write(data)
def edit(p,f):
 fp=os.path.join(out,p);s=open(fp,encoding='utf-8').read();t=f(s);assert t!=s,p+' unchanged';open(fp,'w',encoding='utf-8').write(t)
def rep(s,a,b):
 assert a in s,('missing',a);return s.replace(a,b)
edit('sw.js',lambda s:rep(s,'const PREFIX="sharkattack-v"','const PREFIX="sa-test-"'))
edit('game.js',lambda s:s.replace('"sharkAttack_','"saTEST_'))
edit('version.json',lambda s:json.dumps({"build":build})+"\n")
def idx(s):
 s=rep(s,'<title>Shark Attack</title>','<title>Shark Attack TEST</title>')
 s,k=re.subn(r'<meta name="build" content="[^"]*">','<meta name="build" content="%s">'%build,s);assert k==1
 s=rep(s,'<div id="titleUi" class="ui hide">','<div id="titleUi" class="ui hide"><div id="testTag" style="position:fixed;top:calc(env(safe-area-inset-top) + 6px);left:calc(env(safe-area-inset-left) + 8px);background:#ff7a00;color:#fff;border:3px solid #082a3d;border-radius:10px;padding:2px 10px;font:900 16px system-ui,sans-serif;pointer-events:none">TEST v%d</div>'%n)
 s=rep(s,'Shark Attack plays in landscape','Shark Attack TEST plays in landscape')
 return s
edit('index.html',idx)
def man(s):
 m=json.loads(s);m.update(name="Shark Attack TEST",short_name="SA TEST",id="/shark-attack-test/",start_url="./",scope="./",theme_color="#ff7a00",display="fullscreen",display_override=["fullscreen","standalone"]);return json.dumps(m)
edit('manifest.webmanifest',man)
FONT=next((f for f in['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'] if os.path.exists(f)),None)
def ribbon(p,mask):
 im=Image.open(os.path.join(out,p)).convert('RGBA');S=im.width
 band=Image.new('RGBA',(S*2,int(S*.2)),(0,0,0,0));d=ImageDraw.Draw(band)
 d.rectangle([0,0,band.width,band.height],fill=(255,122,0,255),outline=(8,42,61,255),width=max(2,S//64))
 fs=int(band.height*.72);font=ImageFont.truetype(FONT,fs) if FONT else ImageFont.load_default(size=fs)
 tw=d.textlength('TEST',font=font);d.text(((band.width-tw)/2,band.height*.1),'TEST',font=font,fill=(255,255,255,255),stroke_width=max(1,S//96),stroke_fill=(8,42,61,255))
 band=band.rotate(-35 if not mask else 0,expand=True,resample=Image.BICUBIC)
 if mask:# keep inside the maskable safe zone: horizontal band across the lower middle
  pos=((S-band.width)//2,int(S*.66))
 else:
  pos=(int(S*.62-band.width/2),int(S*.30-band.height/2))
 layer=Image.new('RGBA',im.size,(0,0,0,0));layer.paste(band,pos,band)
 if not mask:# clip to the rounded icon shape
  m=Image.new('L',im.size,0);ImageDraw.Draw(m).rounded_rectangle([S*.04,S*.04,S*.96,S*.96],radius=S*.2,fill=255);layer.putalpha(Image.fromarray(__import__('numpy').minimum(__import__('numpy').array(layer.getchannel('A')),__import__('numpy').array(m))))
 Image.alpha_composite(im,layer).save(os.path.join(out,p))
for p,mask in[('icons/icon-192.png',0),('icons/icon-512.png',0),('icons/maskable-512.png',1)]:ribbon(p,mask)
print(json.dumps({"out":out,"build":build,"n":n,"sha":sha}))
