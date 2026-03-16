# Configuration Guide

DiagNet is designed to work out-of-the-box with zero configuration for most users. However, you can customize its behavior using environment variables.

These variables can be set in your `compose.yaml` file or passed directly to the container.

## Core Configuration

| Variable                       | Description                                                                                                | Default                                            |
| :----------------------------- | :--------------------------------------------------------------------------------------------------------- | :------------------------------------------------- |
| `DIAGNET_DATA_PATH`            | **Recommended.** The base directory for all persistent data (database, secrets).                           | `/data` (in container) <br> `BASE_DIR` (local dev) |
| `DIAGNET_ALLOWED_HOSTS`        | Comma-separated list of hostnames/IPs that can access the application.                                     | `localhost,127.0.0.1`                              |
| `DIAGNET_CSRF_TRUSTED_ORIGINS` | Comma-separated list of trusted origins for CSRF checks. **Required when running behind a reverse proxy.** | _(unset)_                                          |
| `DIAGNET_DEBUG`                | Enables Django debug mode. **Never set this to `True` in production.**                                     | `False`                                            |

## Data & Storage

| Variable              | Description                                                                                                        | Default                         |
| :-------------------- | :----------------------------------------------------------------------------------------------------------------- | :------------------------------ |
| `DIAGNET_DB_PATH`     | Full path to the SQLite database file. Useful if you want the DB in a different location than `DIAGNET_DATA_PATH`. | `$DIAGNET_DATA_PATH/db.sqlite3` |
| `DIAGNET_STATIC_ROOT` | Directory where static files (CSS/JS) are collected. **Managed automatically by the container.**                   | `/nix/store/.../static`         |

## Security (Advanced)

These keys are **automatically generated and persisted** to `DIAGNET_DATA_PATH/secrets.env` on the first run. You typically do **not** need to set these manually unless you are rotating keys or integrating with an external secrets manager.

| Variable                        | Description                                                                   | Requirement                   |
| :------------------------------ | :---------------------------------------------------------------------------- | :---------------------------- |
| `DIAGNET_SECRET_KEY`            | The secret key used for cryptographic signing (session cookies, CSRF tokens). | Random string                 |
| `DIAGNET_DEVICE_ENCRYPTION_KEY` | The key used to encrypt/decrypt sensitive device passwords in the database.   | 32-byte base64-encoded string |

## Custom Test Templates

| Variable                          | Description                                                       | Default                        |
| :-------------------------------- | :---------------------------------------------------------------- | :----------------------------- |
| `DIAGNET_ENABLE_CUSTOM_TESTCASES` | Set to `True` to enable the dynamic loading of custom test cases. | `False`                        |
| `DIAGNET_CUSTOM_TESTCASES_PATH`   | The directory where the system scans for `.py` custom test files. | `$DIAGNET_DATA_PATH/testcases` |

## Example `compose.yaml`

```yaml
services:
  diagnet:
    image: ghcr.io/diagnet/diagnet:latest
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data:Z
    environment:
      - DIAGNET_DATA_PATH=/data
      - DIAGNET_ALLOWED_HOSTS=diagnet.local,192.168.1.50
```

## Behind a Reverse Proxy

When DiagNet runs behind a reverse proxy (e.g. nginx, Caddy, Traefik), the browser sends requests to the proxy's origin, not directly to DiagNet. Django's CSRF protection checks that the `Origin`/`Referer` header matches a trusted origin, so you must tell DiagNet what origin(s) to trust.

Set `DIAGNET_CSRF_TRUSTED_ORIGINS` to a comma-separated list of the scheme + host (and optional port) that users access DiagNet through:

```yaml
environment:
  - DIAGNET_ALLOWED_HOSTS=diagnet.example.com
  - DIAGNET_CSRF_TRUSTED_ORIGINS=https://diagnet.example.com
```

If your proxy exposes DiagNet on a non-standard port, include it:

```
DIAGNET_CSRF_TRUSTED_ORIGINS=https://diagnet.example.com:8443
```

Without this setting, all form submissions and HTMX requests will be rejected with a **403 Forbidden (CSRF verification failed)** error when accessed through the proxy.
