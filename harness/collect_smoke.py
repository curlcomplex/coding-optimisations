#!/usr/bin/env python3
import json
import sys
from pathlib import Path

src = Path(sys.argv[1])
out = Path(sys.argv[2])
answer = None
usage_events = []
event_types = {}

for raw in src.read_text().splitlines():
    if not raw.strip():
        continue
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        continue
    et = str(event.get('type', 'unknown'))
    event_types[et] = event_types.get(et, 0) + 1
    if 'usage' in event:
        usage_events.append(event['usage'])
    item = event.get('item') or {}
    if item.get('type') == 'agent_message' and isinstance(item.get('text'), str):
        answer = item['text'].strip()

summary = {
    'answer': answer,
    'usage_events': usage_events,
    'event_types': event_types,
    'source_event_count': sum(event_types.values()),
}
out.write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
