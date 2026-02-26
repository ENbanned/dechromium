# REST API

The REST API wraps the Python library. Install with server dependencies:
```bash
pip install dechromium[server]
```

Start the server:
```bash
dechromium serve --host=127.0.0.1 --port=3789
```

Or from Python:
```python
dc = Dechromium()
dc.serve(host="127.0.0.1", port=3789)
```

## Endpoints

### Profiles

**Create profile**
```
POST /profiles
```
```json
{
    "name": "my-profile",
    "platform": "windows",
    "proxy": "socks5://user:pass@host:1080",
    "timezone": "America/New_York"
}
```

**List profiles**
```
GET /profiles
```

**Get profile**
```
GET /profiles/{id}
```

**Update profile**
```
PUT /profiles/{id}
```
```json
{
    "name": "renamed",
    "hardware": {"cores": 16}
}
```

**Delete profile**
```
DELETE /profiles/{id}
```

### Browser

**Start browser**
```
POST /profiles/{id}/start
```
```json
{
    "headless": true,
    "timeout": 15.0
}
```

Response:
```json
{
    "profile_id": "abc123",
    "pid": 12345,
    "debug_port": 9200,
    "ws_endpoint": "ws://127.0.0.1:9200/devtools/browser/...",
    "cdp_url": "http://127.0.0.1:9200"
}
```

**Stop browser**
```
POST /profiles/{id}/stop
```

**Browser status**
```
GET /profiles/{id}/status
```

**All running browsers**
```
GET /running
```

**Stop all**
```
POST /stop-all
```

### Cookies

**Import cookies**
```
POST /profiles/{id}/cookies/import
```
```json
{
    "cookies": [
        {"host_key": ".example.com", "name": "session", "value": "abc", "path": "/", "is_secure": 1}
    ]
}
```

**Export cookies**
```
GET /profiles/{id}/cookies/export
```

### Health
```
GET /health
```
```json
{"status": "ok", "profiles": 5, "running": 2}
```
