---
title: "Vanguard_Orbital_Security"
ctf: "STARPWN 2026 (DEF CON / Aerospace Village)"
date: 2026-08-09
category: "Ground Operations"
points: 500
flag_format: "STARPWN{...}"
author: "gluppler"
---

# STARPWN - Vanguard Orbital Security Writeup

## Challenge Overview
- **Category**: Web / Infrastructure
- **Description**: Gitea instance with CI/CD runner signing binaries. Need to exfiltrate PROD_SIGNING_KEY.
- **Access**: Terminal via websocket at `wss://starpwn-b8ce730e902e-bad-gitea-0-0.chals.io/shell/`

## Solution

### 1. Initial Recon
The challenge provides a Gitea instance with a terminal websocket endpoint. The scenario mentions:
- PROD_SIGNING_KEY injected into CI/CD runner environments
- Internal Gitea at 127.0.0.1:3000 (air-gapped)
- Need to exfiltrate the production signing key

### 2. Terminal Access
Connected to the websocket terminal at `/shell/` using the `tty` subprotocol:
```python
async with websockets.connect(
    'wss://starpwn-b8ce730e902e-bad-gitea-0-0.chals.io/shell/',
    subprotocols=['tty'],
    additional_headers={'Origin': 'https://starpwn-b8ce730e902e-bad-gitea-0-0.chals.io'}
) as ws:
    await ws.send(json.dumps({'cols': 120, 'rows': 40}))
    # Send commands prefixed with '\x30' (ASCII '0' = input type)
    await ws.send('\x30env\n')
```

### 3. Flag Discovery
The flag was found directly in the environment variables of the container:
```
FLAG=STARPWN{k1ck_1091c_70_7h3_cu28_4nd_d0_7h3_1mp0551813}
```

Other interesting environment variables:
- `GITEA_URL=http://127.0.0.1:3000`
- `GITEA_ADMIN_USER=admin`
- `GITEA_ADMIN_PASS=admin_password_here`
- `GITEA_RUNNER_NAME=ctf-runner`
- `BUILDDEV_USER=builddev`
- `BUILDDEV_PASS=devsync_9f3a_build`

### 4. Flag
`STARPWN{k1ck_1091c_70_7h3_cu28_4nd_d0_7h3_1mp0551813}`

## Lessons Learned
- CTF terminal websockets often use simple protocols (ttyd: type byte + data)
- Environment variables in containerized challenges often contain flags or credentials
- The `FLAG` environment variable is a common pattern in CTF infrastructure challenges