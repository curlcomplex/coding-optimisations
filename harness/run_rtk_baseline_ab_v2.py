#!/usr/bin/env python3
"""Execute the reviewed baseline harness with two narrow pre-inference bookkeeping fixes."""
from pathlib import Path
source=(Path(__file__).with_name('rtk_baseline_ab.py')).read_text()
old="rs=[r for r in rows if r['arm']==arm];calls=[r[k] for r in rs for k in ('worker','review')]"
new="rs=[r for r in rows if r.get('arm')==arm];calls=[r[k] for r in rs for k in ('worker','review') if isinstance(r.get(k),dict)]"
if source.count(old)!=1:raise SystemExit('aggregate patch point drift')
source=source.replace(old,new)
old2="if kind in bases and bases[kind][arm]!=base:raise RuntimeError('same-arm starting commit drift')"
new2="if kind in bases and arm in bases[kind] and bases[kind][arm]!=base:raise RuntimeError('same-arm starting commit drift')"
if source.count(old2)!=1:raise SystemExit('baseline patch point drift')
source=source.replace(old2,new2)
code=compile(source,str(Path(__file__).with_name('rtk_baseline_ab.py')),'exec')
exec(code,{'__name__':'__main__','__file__':str(Path(__file__).with_name('rtk_baseline_ab.py'))})
