# Proxy & Network

## Proxy

Supports SOCKS5, HTTP, and HTTPS proxies:
```python
# SOCKS5
dc.create("x", proxy="socks5://host:1080")

# SOCKS5 with auth
dc.create("x", proxy="socks5://user:pass@host:1080")

# HTTP with auth
dc.create("x", proxy="http://user:pass@host:8080")
```

Credentials are extracted from the URL automatically and passed to the browser via `--aspect-proxy-username` and `--aspect-proxy-password`. Authentication happens at the C++ level — no browser extension or CDP hack.

### DNS leak protection

When a proxy is configured, DNS resolution is forced through the proxy:
```
--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost, EXCLUDE {proxy_host}
```

The proxy host itself is excluded so the browser can connect to it.

### WebRTC leak protection

WebRTC is restricted to prevent IP leaks:
```
--force-webrtc-ip-handling-policy=disable_non_proxied_udp
```

Available policies:

| Policy | Description |
|---|---|
| `default` | No restrictions |
| `default_public_and_private_interfaces` | Use default route + associated interfaces |
| `default_public_interface_only` | Only default route |
| `disable_non_proxied_udp` | Force UDP through proxy (default) |

## Timezone
```python
dc.create("x", timezone="Asia/Tokyo")
```

Sets the `TZ` environment variable. Covers:

- `new Date().getTimezoneOffset()`
- `Intl.DateTimeFormat().resolvedOptions().timeZone`
- `new Date().toString()` timezone abbreviation

## Locale
```python
dc.create("x", locale="ja-JP", languages=["ja-JP", "ja", "en-US", "en"])
```

- `locale` → `--lang` flag + `LANG` env var → affects `Intl.*` APIs
- `languages` → `--accept-lang` flag → `navigator.languages` and `Accept-Language` header

## Consistency

For anti-detect to work, network settings must be consistent:

- Proxy IP geolocation should match the timezone
- Timezone should match the locale (a Japanese locale with a US timezone is suspicious)
- Languages should include the locale's language
