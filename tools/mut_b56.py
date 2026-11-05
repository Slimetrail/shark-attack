# b56 mutation checks: each broken copy of game.js/version.json must make tests/test_b56.py FAIL; the real tree must PASS.
# Usage: /workspace/.pwvenv/bin/python tools/mut_b56.py
import os,sys,shutil,subprocess,tempfile
HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PY=sys.executable
M=[('body kills again (b55 rule)','game.js','&&mouthHit(f)){gameOver','&&d2<(L*.32+f.s*(f.kind==="shark"?.9:.4))**2){gameOver'),
   ('mouth kills without body contact','game.js','else{const rr=L*.32+f.s*(f.kind==="shark"?.9:.4);','else{if(eater&&!godMode&&elapsed>EAT.GRACE&&mouthHit(f)){gameOver("eaten");return}const rr=L*.32+f.s*(f.kind==="shark"?.9:.4);'),
   ('mouth never kills','game.js','function mouthHit(f){','function mouthHit(f){return false;'),
   ('mouth on the wrong end (tail)','game.js','dir=f.vx<0?-1:1;return','dir=f.vx<0?1:-1;return'),
   ('no late cap (CAP 2 at max size)','game.js','chaseCap=()=>shark.lvl>=CHASE.MAX_FROM?CHASE.CAP_MAX:CHASE.CAP','chaseCap=()=>CHASE.CAP'),
   ('deep sharks back to b55','game.js','SHARK_P_DEEP:.38,','SHARK_P_DEEP:.45,'),
   ('your body no longer eats prey','game.js','if(ex*ex+ey*ey<rr*rr||onBody(f)){','if(ex*ex+ey*ey<rr*rr){'),
   ('sail boats back to HUD 8','game.js','SAIL_LVL:6','SAIL_LVL:7'),
   ('build still 56','version.json','"58"','"56"')]
def run(root):
  e=dict(os.environ,SA_ROOT=root,SA_PORT56='8962');r=subprocess.run([PY,os.path.join(HERE,'tests','test_b56.py')],env=e,capture_output=True,text=True,timeout=300);return r.returncode,r.stdout.strip().splitlines()[-1:]
bad=0;c,l=run(HERE);print('REAL tree:', 'PASS' if c==0 else 'FAIL',l);bad+=c!=0
for name,fn,a,b in M:
  d=tempfile.mkdtemp();shutil.copytree(HERE,d+'/t',ignore=shutil.ignore_patterns('.git','art-shots-*','*.png'));p=d+'/t/'+fn;s=open(p).read()
  if a not in s: print('MUTATION NOT APPLIED',name);bad+=1;continue
  open(p,'w').write(s.replace(a,b,1));c,l=run(d+'/t');print(f'mutant "{name}":','caught (test fails)' if c!=0 else 'NOT CAUGHT',l);bad+=c==0;shutil.rmtree(d)
print('mutations ok' if not bad else f'{bad} problems');sys.exit(1 if bad else 0)
