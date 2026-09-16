"""Frozen issue-shaped coding fixtures for lab issue #11; no production source."""
from pathlib import Path
import hashlib

COMMON = '''# Fixture worker contract
GitHub issue #11 in curlcomplex/coding-optimisations owns this benchmark. ISSUE.md
is its frozen task rendering, not a separate task authority.
Use the existing RTK wrapper for supported shell commands and Serena for relevant
symbol navigation. Recover original diagnostics when compressed output is missing
needed details. Do not force full-file rereads or bypass existing tools.
Implement only under src/. Keep public APIs and useful comments. Tests, ISSUE.md,
AGENTS.md, run_tests.py and configuration are protected: do not edit them.
Run python3 run_tests.py, fix failures within this task, and inspect your final diff.
Use no network, installs, external worktrees, commits, pushes or permission escalation.
Do not use other agents or inspect other trial directories. Report changes and exact
test evidence when done; an independent fresh session will review the patch.
'''
CPP_ISSUE = '''# C++ parameter smoother: time units and retargeting continuity
Fix src/smoother.hpp, preserving its public API. This control smoother is used for
parameter locks while a voice is releasing: changing a target must not reset its
current value or click. It runs once per sample, without allocation.
For positive time t milliseconds, a=exp(-1/(sampleRate*t*0.001)); each process()
returns target + a*(previous-target). Default sample rate 48000, time 10 ms.
setTarget changes the target only; ignore nonfinite targets. reset sets current
and target to a finite value (nonfinite reset means zero). setTimeMs updates the
coefficient without touching current/target; negative/nonfinite time means zero.
Zero time snaps to target on the next process(), not during setTarget.
setSampleRate accepts only positive finite rates; invalid rates leave prior rate
and all state unchanged. Valid rate changes recalculate the coefficient while
preserving state. processBlock must exactly match repeated process calls.
Run the frozen numerical tests, covering 44.1/48/96 kHz, rate/time changes,
retargeting during decay, zero-time and nonfinite handling. Do not weaken tests.
'''
CPP_SOURCE = '''#pragma once
#include <cstddef>
#include <cmath>
// State belongs to each voice; retargeting must be continuous during release.
class ParameterSmoother {
public:
    void setSampleRate(double rate) { rate_ = rate; update(); }
    void setTimeMs(double ms) { time_ = ms; update(); }
    void reset(double value) { current_ = target_ = value; }
    void setTarget(double value) { target_ = value; current_ = value; }
    double current() const { return current_; }
    double process() {
        current_ += (target_ - current_) * coefficient_;
        return current_;
    }
    void processBlock(double* output, std::size_t n) {
        const double value = process();
        for (std::size_t i=0; i<n; ++i) output[i] = value;
    }
private:
    void update() { coefficient_ = std::exp(-1.0/(rate_*time_)); }
    double rate_ = 48000.0, time_ = 10.0;
    double current_ = 0.0, target_ = 0.0;
    double coefficient_ = std::exp(-1.0/(48000.0*10.0));
};
'''
CPP_TEST = r'''#include "../src/smoother.hpp"
#include <cmath>
#include <iostream>
#include <limits>
#include <string>
static int failures=0, checks=0;
void near(double value,double expected,const std::string& name) {
    ++checks;
    if (!std::isfinite(value) || std::abs(value-expected)>2e-11) {
        ++failures;
        std::cerr.precision(17);
        std::cerr << "FAIL " << name << " actual=" << value << " expected=" << expected << " tolerance=2e-11\n";
    }
}
int main() {
    for(double sr:{44100.0,48000.0,96000.0}) for(double ms:{0.0,1.0,10.0,235.0}) {
        ParameterSmoother s; s.setSampleRate(sr); s.setTimeMs(ms); s.reset(1); s.setTarget(0);
        near(s.current(),1,"target continuity"); double expected=1;
        const double a=ms==0 ? 0:std::exp(-1/(sr*ms*.001));
        for(int i=0;i<127;++i) { expected*=a; near(s.process(),expected,"decay"); }
        const double before=s.current(); s.setTarget(.37); near(s.current(),before,"release retarget continuity");
        for(int i=0;i<43;++i) { expected=.37+a*(expected-.37); near(s.process(),expected,"retarget"); }
    }
    ParameterSmoother s; s.reset(0); s.setTarget(1);
    near(s.process(),1-std::exp(-1.0/480),"default milliseconds");
    double previous=s.current(); s.setTimeMs(20); near(s.current(),previous,"time continuity");
    near(s.process(),1+std::exp(-1.0/960)*(previous-1),"changed time");
    previous=s.current(); s.setSampleRate(96000); near(s.current(),previous,"rate continuity");
    near(s.process(),1+std::exp(-1.0/1920)*(previous-1),"changed rate");
    for(double bad:{0.0,-1.0,std::numeric_limits<double>::infinity(),std::numeric_limits<double>::quiet_NaN()}) {
        previous=s.current(); s.setSampleRate(bad);
        near(s.current(),previous,"invalid rate state");
        near(s.process(),1+std::exp(-1.0/1920)*(previous-1),"invalid rate ignored");
    }
    for(double bad:{std::numeric_limits<double>::infinity(),std::numeric_limits<double>::quiet_NaN()}) {
        s.setTarget(1); previous=s.current(); s.setTarget(bad); near(s.current(),previous,"invalid target state");
        near(s.process(),1+std::exp(-1.0/1920)*(previous-1),"invalid target ignored");
        s.reset(bad); near(s.current(),0,"invalid reset"); near(s.process(),0,"reset target");
    }
    for(double bad:{-1.0,std::numeric_limits<double>::infinity(),std::numeric_limits<double>::quiet_NaN()}) {
        s.reset(.2); s.setTimeMs(bad); s.setTarget(.9); near(s.current(),.2,"zero time continuity");
        near(s.process(),.9,"bad time snaps");
    }
    ParameterSmoother a,b; a.reset(1);b.reset(1);a.setTarget(0);b.setTarget(0);
    double buf[100]; a.processBlock(nullptr,0); near(a.current(),1,"empty block");
    a.processBlock(buf,100); for(int i=0;i<100;++i)near(buf[i],b.process(),"block equivalence");
    std::cout << checks << " checks; " << failures << " failures\n";
    return failures?1:0;
}
'''
UI_ISSUE = '''# Tracker held-row automation: current target, pointer ownership and dedup
Fix src/automation.ts without changing the public signatures.
AutomationWriter.begin(pointer,track,row) makes that pointer the newest active
hold. move updates only that pointer's track/row, never changes hold priority;
end releases only that pointer. With multiple holds, write targets the most
recently begun still-active pointer; releasing it falls back to the previous one.
No active hold means write returns null. Row/track zero are valid. Coordinates
must be finite nonnegative integers; invalid begin/move does not change any state.
write(parameter,value) rejects blank parameters and nonfinite values; valid values
are clamped into [0,1]. Returned lock is a fresh {track,row,parameter,value} object.
Suppress consecutive equal values only for the same track/row/parameter address.
A different row/track/parameter still needs its own event. After changing a value
at an address, returning to the old value must emit. Pointer moves/end never
retarget previously returned objects. A duplicate begin for a pointer replaces
its target and makes it newest. There is no writing to an original stale row.
Run python3 run_tests.py. Preserve types/comments and do not edit the tests.
'''
UI_SOURCE = '''export type Lock = { track: number; row: number; parameter: string; value: number };
type Hold = { track: number; row: number };
// Independent pointer ownership is required for touch parameter-lock editing.
export class AutomationWriter {
  private holds = new Map<number, Hold>();
  private lastValue: number | undefined;
  begin(pointer: number, track: number, row: number): void {
    this.holds.set(pointer, {track, row});
  }
  move(pointer: number, track: number, row: number): void {
    const hold = this.holds.get(pointer);
    if (hold) this.holds.set(pointer, {track: hold.track, row: hold.row});
  }
  end(pointer: number): void { this.holds.clear(); }
  write(parameter: string, value: number): Lock | null {
    const hold = this.holds.values().next().value;
    if (!hold || !hold.row || value === this.lastValue) return null;
    this.lastValue = value;
    return {...hold, parameter, value};
  }
}
'''
UI_TEST = '''import assert from 'node:assert/strict';
import {test} from 'node:test';
import {AutomationWriter} from '../src/automation.ts';
const lock=(track,row,parameter,value)=>({track,row,parameter,value});
test('no hold, row zero, current held row and track',()=>{
 const w=new AutomationWriter();assert.equal(w.write('cutoff',.2),null);
 w.begin(1,0,0);assert.deepEqual(w.write('cutoff',.2),lock(0,0,'cutoff',.2));
 w.move(1,2,7);assert.deepEqual(w.write('cutoff',.2),lock(2,7,'cutoff',.2));
 w.end(1);assert.equal(w.write('cutoff',.8),null);
});
test('latest begin wins; move does not change priority; release falls back',()=>{
 const w=new AutomationWriter();w.begin(1,0,1);w.begin(2,1,2);w.move(1,3,4);
 assert.deepEqual(w.write('tone',.5),lock(1,2,'tone',.5));
 w.end(2);assert.deepEqual(w.write('tone',.5),lock(3,4,'tone',.5));
 w.end(999);assert.deepEqual(w.write('tone',.6),lock(3,4,'tone',.6));
});
test('duplicate pointer begin becomes newest',()=>{
 const w=new AutomationWriter();w.begin(1,0,1);w.begin(2,0,2);w.begin(1,2,3);
 assert.deepEqual(w.write('x',.1),lock(2,3,'x',.1));
});
test('dedup is per complete address, not value alone',()=>{
 const w=new AutomationWriter();w.begin(1,0,3);
 assert.deepEqual(w.write('a',.5),lock(0,3,'a',.5));assert.equal(w.write('a',.5),null);
 assert.deepEqual(w.write('b',.5),lock(0,3,'b',.5));
 w.move(1,1,3);assert.deepEqual(w.write('a',.5),lock(1,3,'a',.5));
 w.move(1,0,3);assert.equal(w.write('a',.5),null);
 assert.deepEqual(w.write('a',.7),lock(0,3,'a',.7));
 assert.deepEqual(w.write('a',.5),lock(0,3,'a',.5));
});
test('value and coordinate validation',()=>{
 const w=new AutomationWriter();w.begin(1,0,1);
 for(const v of [NaN,Infinity,-Infinity])assert.equal(w.write('a',v),null);
 for(const p of ['', '  '])assert.equal(w.write(p,.3),null);
 assert.deepEqual(w.write('a',-4),lock(0,1,'a',0));assert.equal(w.write('a',-2),null);
 assert.deepEqual(w.write('a',4),lock(0,1,'a',1));
 for(const n of [-1,.5,Infinity,NaN]){w.move(1,0,n);w.begin(2,n,4);}
 assert.deepEqual(w.write('a',.6),lock(0,1,'a',.6));
 w.move(999,2,3);assert.deepEqual(w.write('a',.9),lock(0,1,'a',.9));
});
test('returned locks remain independent',()=>{
 const w=new AutomationWriter();w.begin(1,0,0);const first=w.write('a',.1);
 first.row=99;w.move(1,2,4);const second=w.write('a',.2);w.end(1);
 assert.deepEqual(second,lock(2,4,'a',.2));assert.equal(first.row,99);
});
test('deterministic mixed-pointer/address sequence matches reference',()=>{
 let seed=1234567;const rnd=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed;};
 const w=new AutomationWriter(),holds=new Map(),last=new Map();
 for(let i=0;i<400;i++){
  const p=rnd()%5, op=rnd()%4, track=rnd()%3,row=rnd()%16;
  if(op===0){w.begin(p,track,row);holds.delete(p);holds.set(p,{track,row});}
  else if(op===1){w.move(p,track,row);if(holds.has(p))holds.set(p,{track,row});}
  else if(op===2){w.end(p);holds.delete(p);}
  const parameter=['tone','release','pan'][rnd()%3],value=(rnd()%11)/10;
  const target=[...holds.values()].at(-1);let expected=null;
  if(target){const key=JSON.stringify([target.track,target.row,parameter]);if(last.get(key)!==value){last.set(key,value);expected={...target,parameter,value};}}
  assert.deepEqual(w.write(parameter,value),expected,`iteration ${i}`);
 }
});
'''
RUNNER = '''import pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parent
if (root/'src/smoother.hpp').exists():
 build=root/'build';build.mkdir(exist_ok=True)
 c=subprocess.run(['clang++','-std=c++17','-Wall','-Wextra','-Werror','-pedantic','tests/test.cpp','-o',str(build/'test')],cwd=root)
 if c.returncode:raise SystemExit(c.returncode)
 raise SystemExit(subprocess.run([str(build/'test')],cwd=root).returncode)
raise SystemExit(subprocess.run(['node','--experimental-strip-types','--test','tests/automation.mjs'],cwd=root).returncode)
'''

def files(kind: str) -> dict[str,str]:
    shared={'AGENTS.md':COMMON,'run_tests.py':RUNNER,'.gitignore':'build/\n.serena/\n__pycache__/\n',
            '.codex/config.toml':'[skills]\ninclude_instructions=false\n'}
    if kind=='cpp':shared.update({'ISSUE.md':CPP_ISSUE,'src/smoother.hpp':CPP_SOURCE,'tests/test.cpp':CPP_TEST})
    elif kind=='ui':shared.update({'ISSUE.md':UI_ISSUE,'src/automation.ts':UI_SOURCE,'tests/automation.mjs':UI_TEST})
    else:raise ValueError('unknown fixture')
    return shared

def materialize(root: Path, kind: str) -> dict[str,str]:
    root.mkdir(parents=True,exist_ok=False)
    contents=files(kind)
    for name,content in contents.items():
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
    return {name:hashlib.sha256(content.encode()).hexdigest() for name,content in contents.items()}
