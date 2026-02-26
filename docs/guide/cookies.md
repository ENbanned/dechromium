# Cookies

Import and export cookies in Chrome's SQLite format.

## Import
```python
# From a list of dicts
dc.import_cookies(profile_id, [
    {
        "host_key": ".example.com",
        "name": "session_id",
        "value": "abc123",
        "path": "/",
        "is_secure": 1,
        "is_httponly": 1,
        "expires_utc": 13370000000000000,
    }
])

# From a JSON file
dc.import_cookies(profile_id, "/path/to/cookies.json")
```

Import replaces all existing cookies in the profile.

## Export
```python
cookies = dc.export_cookies(profile_id)
# Returns list[dict] with all cookie fields
```

## Cookie fields

| Field | Type | Description |
|---|---|---|
| `host_key` | str | Domain (`.example.com`) |
| `name` | str | Cookie name |
| `value` | str | Cookie value (unencrypted only) |
| `path` | str | Cookie path |
| `expires_utc` | int | Expiry in Chrome epoch (microseconds since 1601-01-01) |
| `is_secure` | int | HTTPS only (0 or 1) |
| `is_httponly` | int | HTTP only (0 or 1) |
| `samesite` | int | SameSite policy (-1, 0, 1, 2) |

!!! note
    Encrypted cookies (`encrypted_value`) cannot be imported or exported. Only plaintext `value` is supported. This covers most use cases — session tokens, preferences, etc.
