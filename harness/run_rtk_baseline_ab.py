#!/usr/bin/env python3
"""Driver for rtk_baseline_ab that keeps partial-row accounting valid."""
import rtk_baseline_ab as m

def aggregate(rows):
    out={}
    for arm in m.ARMS:
        rs=[r for r in rows if r.get('arm')==arm]
        calls=[r[k] for r in rs for k in ('worker','review') if isinstance(r.get(k),dict)]
        known=bool(calls) and all(c.get('accounting_verified') and c.get('usage') for c in calls)
        u={k:sum(c['usage'][k] for c in calls) for k in ('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens')} if known else None
        accepted=sum(r.get('accepted',False) for r in rs);total=u['input_tokens']+u['output_tokens'] if u else None
        out[arm]={'attempts':len(rs),'accepted':accepted,'failures':len(rs)-accepted,'model_invocations':len(calls),'usage':u,'total_tokens':total,
          'tokens_per_accepted':total/accepted if total is not None and accepted else None,'output_per_accepted':u['output_tokens']/accepted if u and accepted else None,
          'provider_requests':sum(c.get('provider_requests',0) for c in calls),'wall_seconds':sum(c.get('wall_seconds',0) for c in calls),'accounting_complete':known}
    return out
m.aggregate=aggregate
if __name__=='__main__':raise SystemExit(m.main())
