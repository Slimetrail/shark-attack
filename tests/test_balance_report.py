# b54 (QA): a failing balance run must never be reported as BALANCE OK.
# Runs tests/balance.py --selftest (fake rows: hammerhead survives 8/25 = 32% in the no-wiggle rows, like the QA runs) and checks the verdict.
import subprocess,sys,os
R=os.path.dirname(os.path.abspath(__file__));ok=0;bad=0
def check(c,m):
  global ok,bad
  print(('PASS ' if c else 'FAIL ')+m);ok+=c;bad+=not c
p=subprocess.run([sys.executable,os.path.join(R,'balance.py'),'--selftest'],capture_output=True,text=True,timeout=60)
check(p.returncode!=0,f'failing balance run exits non-zero (exit {p.returncode})')
check('BALANCE OK' not in p.stdout,'failing balance run never prints BALANCE OK')
check('BALANCE FAILED' in p.stdout and 'no-wiggle/hammer' in p.stdout,'the no-wiggle hammerhead survival failure is named')
s=open(os.path.join(R,'balance_endless.py')).read()
check("print('ISSUES' if bad else 'ENDLESS BALANCE OK',bad);sys.exit(1 if bad else 0)" in s,'balance_endless.py prints OK only with no issues and exits non-zero otherwise')
check(' OK' not in open(os.path.join(R,'balance_v9.py')).read(),'balance_v9.py is a report table only and never claims OK')
print(f'{ok} passed, {bad} failed');sys.exit(1 if bad else 0)
