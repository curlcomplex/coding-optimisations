#!/usr/bin/env python3
"""Complete the two missing UI repetition-2 arms; RTK use is observed, not mandatory."""
from pathlib import Path
source=Path(__file__).with_name('rtk_baseline_ab.py').read_text()
replacements={
"rs=[r for r in rows if r['arm']==arm];calls=[r[k] for r in rs for k in ('worker','review')]":"rs=[r for r in rows if r.get('arm')==arm];calls=[r[k] for r in rs for k in ('worker','review') if isinstance(r.get(k),dict)]",
"if kind in bases and bases[kind][arm]!=base:raise RuntimeError('same-arm starting commit drift')":"if kind in bases and arm in bases[kind] and bases[kind][arm]!=base:raise RuntimeError('same-arm starting commit drift')",
"for kind in ('cpp','ui'):":"for kind in ('ui',):",
"for rep in (1,2):":"for rep in (2,):",
"            if arm=='rtk' and row['rtk_wrapper_executions']==0:raise RuntimeError('RTK arm did not execute RTK')":"            # Normal RTK is available and instructed, but agents may legitimately not need it on a task."
}
for old,new in replacements.items():
    if source.count(old)!=1:raise SystemExit('patch point drift: '+old[:40])
    source=source.replace(old,new)
exec(compile(source,str(Path(__file__).with_name('rtk_baseline_ab.py')),'exec'),{'__name__':'__main__','__file__':str(Path(__file__).with_name('rtk_baseline_ab.py'))})
