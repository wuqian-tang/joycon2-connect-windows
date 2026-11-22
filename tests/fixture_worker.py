"""A real subprocess fixture: same line protocol, no Bluetooth side effects."""
import json
import sys
import time

print(json.dumps({'event': 'phase', 'phase': 'scanning_left'}), flush=True)
if '--localized-error' in sys.argv:
    print(json.dumps({'event': 'hint', 'key': 'reconnect_mode', 'params': {'side': 'left'},
                      'message': 'Pair 11:22:33:44:55:66 again'}), flush=True)
    print(json.dumps({'event': 'error', 'key': 'gatt_unreachable',
                      'message': 'Unreachable 11:22:33:44:55:66'}), flush=True)
    sys.exit(1)
if '--crash' in sys.argv:
    print(json.dumps({'event': 'side', 'side': 'left', 'connected': True}), flush=True)
    sys.exit(7)
for line in sys.stdin:
    if line.strip() == 'stop':
        print(json.dumps({'event': 'stopped'}), flush=True)
        sys.exit(0)
    time.sleep(0.01)
