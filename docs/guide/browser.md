# Browser Lifecycle

## Starting a browser
```python
browser = dc.start(profile_id, headless=True)
```

Parameters:

| Parameter | Default | Description |
|---|---|---|
| `headless` | `True` | Run without visible window |
| `extra_args` | `None` | Additional Chrome flags |
| `timeout` | `15.0` | Seconds to wait for CDP ready |

Returns a `BrowserInfo` object:
```python
browser.profile_id   # which profile this browser belongs to
browser.pid          # OS process ID
browser.debug_port   # CDP port (auto-allocated from 9200-9999)
browser.ws_endpoint  # WebSocket URL for CDP
browser.cdp_url      # HTTP URL for CDP
```

## Headless vs headed

**Headless** — no window, no GPU. Good for servers and automation:
```python
dc.start(profile_id, headless=True)
# adds: --headless=new --enable-unsafe-swiftshader
```

**Headed** — visible browser window. Requires a display (real or virtual):
```python
dc.start(profile_id, headless=False)
```

On a Linux server without a monitor, use Xvfb:
```bash
apt install xvfb
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
```

## Stopping
```python
dc.stop(profile_id)   # SIGTERM → wait → SIGKILL
dc.stop_all()          # stop everything
```

## Status
```python
status = dc.status(profile_id)
# {"status": "running", "pid": 1234, "debug_port": 9200, ...}
# or {"status": "stopped", "profile_id": "abc123"}

running = dc.running()  # list of BrowserInfo for all running browsers
```

## Extra Chrome flags
```python
dc.start(profile_id, extra_args=[
    "--disable-extensions",
    "--window-position=0,0",
])
```

## Port allocation

Debug ports are automatically allocated from the range 9200-9999. Each browser gets a unique port. Configure the range:
```python
dc = Dechromium(Config(debug_port_start=10000, debug_port_end=10999))
```
