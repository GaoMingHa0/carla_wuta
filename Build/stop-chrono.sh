#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import os, signal
for entry in os.listdir('/proc'):
    if not entry.isdigit():
        continue
    try:
        args = open('/proc/' + entry + '/cmdline', 'rb').read().split(b'\0')
        if (args[0] == b'/home/wuta/UnrealEngine_4.26/Engine/Binaries/Linux/UE4Editor'
                and any(m in args for m in [b'/Game/ChronoTest/ChronoFlat', b'/Game/ChronoTest/FSACLoop'])
                and b'-carla-rpc-port=2200' in args):
            os.kill(int(entry), signal.SIGTERM)
            print('Stopping ChronoFlat PID', entry)
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        pass
PY
