Seems like Meridian is stuck again. Good news for you if you want the Ion$. They were even kind enough to provide you with a foothold this time, more info below:

    [INTERCEPTED TRANSMISSION: VANGUARD ORBITAL SECURITY]

    Priority: CRITICAL

    Subject: Deprecation of Local Signing Keys

    To all Flight Software Engineers:

    Effective immediately, local compiling and binary signing for the Vanguard CubeSat constellation is strictly prohibited. The PROD_SIGNING_KEY has been securely injected into the internal CI/CD runner environments.

    Do not submit IT tickets asking for the key. If your code passes the automated checks, the runner will sign the release bundle for you. The internal Gitea server (127.0.0.1:3000) is air-gapped from the public net. Security is absolute.

Find a way to exfiltrate the production key, they'll take it from there.

Access Terminal: https://[challenge-url]/shell/
