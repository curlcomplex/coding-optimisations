#!/usr/bin/env python3
from __future__ import annotations
import json,os,subprocess,sys,uuid
from pathlib import Path
MODEL='gpt-5.6-luna'; REASONING='medium'
TASKS={'cpp':('''double smooth(double current,double target,double amount){ return current + (target-current)*amount; }\ndouble release(double x){ return smooth(x,0.0,1.0); }\n''','''#include <cassert>\ndouble release(double); int main(){double x=release(1.0); assert(x>0.0 && x<1.0);}\n''','Fix the release smoothing bug. Preserve the API. Run the test and make the smallest correct change.'),'ui':('''export function heldRow(startRow, currentRow, held) { return held ? startRow : currentRow; }\n''','''import {heldRow} from "./logic.mjs"; if(heldRow(2,7,true)!==7) throw Error("held row must follow current row"); if(heldRow(2,7,false)!==7) throw Error("unheld current row"); console.log("ok");\n''','Fix held-row automation targeting. When held, writes must follow the current row rather than the original press row. Run the test and make the smallest correct change.')}
def run(cmd,cwd,env,timeout=180):return subprocess.run(cmd,cwd=cwd,env=env,text=True,capture_output=True,timeout=timeout)
def usage(home,tid):
 files=list(home.glob('sessions/**/*'+tid+'*.jsonl'))
 if len(files)!=1:return None
 total=None;req=0
 for line in files[0].read_text(errors='replace').splitlines():
  try:r=json.loads(line);p=r.get('payload',{})
  except:continue
  if r.get('type')=='event_msg' and p.get('type')=='token_count' and p.get('info'):
   i=p['info'];t=i.get('total_token_usage');last=i.get('last_token_usage')
   if t and t!=total:total=t;req+=1 if last else 0
 return {'total':total,'requests':req}
def fixture(root,kind):
 root.mkdir();src,test,prompt=TASKS[kind]
 if kind=='cpp':(root/'voice.cpp').write_text(src);(root/'test.cpp').write_text(test);testcmd=['sh','-lc','clang++ -std=c++17 voice.cpp test.cpp -o test && ./test']
 else:(root/'logic.mjs').write_text(src);(root/'test.mjs').write_text(test);testcmd=['node','test.mjs']
 for c in (['git','init','-q'],['git','config','user.email','fixture@example.invalid'],['git','config','user.name','Fixture'],['git','add','.'],['git','commit','-qm','fixture']):run(c,root,os.environ)
 return prompt,testcmd
def arm(codex,home,root,kind,rep,hook,hookbin):
 cwd=root/(f'{kind}-{rep}-'+('on' if hook else 'off'));prompt,testcmd=fixture(cwd);env=os.environ.copy();[env.pop(k,None) for k in ('OPENAI_API_KEY','CODEX_API_KEY','OPENAI_BASE_URL')];marker='BENCH_'+uuid.uuid4().hex
 wrapper=root/'hook-wrapper.py';audit=root/'hook-audit.jsonl';wrapper.write_text('import json,subprocess,sys\nfrom pathlib import Path\nd=sys.stdin.buffer.read();r=subprocess.run('+repr([str(hookbin),'hook','codex'])+',input=d,capture_output=True)\nPath('+repr(str(audit))+').open("ab").write(json.dumps({"in":json.loads(d),"out":r.stdout.decode()}).encode()+b"\\n")\nsys.stdout.buffer.write(r.stdout)\n')
 hooks='{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"python3 '+str(wrapper)+'"}]}]}}';cmd=[codex,'-a','never','-s','workspace-write','-m',MODEL,'-c','model_reasoning_effort="'+REASONING+'"','-c','skills.include_instructions=false','-c','forced_login_method="chatgpt"']
 if hook:cmd+=['-c','hooks='+hooks]
 cmd+=['exec','--json',prompt+' Finish with exactly '+marker+' after implementation and tests pass.'];p=run(cmd,cwd,env);tid=None;answer=''
 for l in p.stdout.splitlines():
  try:e=json.loads(l)
  except:continue
  tid=tid or e.get('thread_id')
  if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='agent_message':answer=e['item'].get('text','')
 test=run(testcmd,cwd,env,60);diff=run(['git','diff','--check'],cwd,env,30);u=usage(home,tid) if tid else None
 return {'kind':kind,'rep':rep,'hook':hook,'rc':p.returncode,'answer_ok':marker in answer,'tests':test.returncode==0,'diff_check':diff.returncode==0,'usage':u}
def main():
 if 'PUEUE_WORKER_ID' not in os.environ:raise SystemExit('queue required')
 codex=sys.argv[1];hookbin=Path(sys.argv[2]);out=Path(sys.argv[3]);out.mkdir(parents=True);home=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')));login=run([codex,'-c','forced_login_method="chatgpt"','login','status'],Path.cwd(),os.environ,15)
 if login.returncode or 'chatgpt' not in (login.stdout+login.stderr).lower():raise SystemExit('no subscription login')
 rows=[]
 for kind in TASKS:
  for rep in (1,2):
   for hook in ((False,True) if rep==1 else (True,False)):rows.append(arm(codex,home,out,kind,rep,hook,hookbin))
 report={'model':MODEL,'reasoning':REASONING,'rows':rows,'all_correct':all(r['rc']==0 and r['answer_ok'] and r['tests'] and r['diff_check'] and r['usage'] for r in rows)};(out/'safe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 0 if report['all_correct'] else 1
if __name__=='__main__':raise SystemExit(main())
