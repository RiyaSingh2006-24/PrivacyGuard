# PrivacyGuard v2.1.0 Release Checklist

## Automated build

- [ ] React production build succeeds on Windows
- [ ] PyInstaller Windows package succeeds
- [ ] Packaged `/api/health` smoke test succeeds
- [ ] Inno Setup installer compiles
- [ ] Portable Windows artifact is uploaded
- [ ] Windows installer artifact is uploaded

## Manual Windows verification

Install the generated `PrivacyGuard-Setup-2.1.0.exe` on a clean Windows system and verify:

- [ ] PrivacyGuard launches and opens `http://127.0.0.1:8000`
- [ ] Dashboard loads without a development server
- [ ] Network information detects the Windows host correctly
- [ ] Local network scan completes on an authorized home/test network
- [ ] A first-seen device is flagged as new
- [ ] A recognized device can be marked Trusted
- [ ] Trusted state persists after restarting PrivacyGuard
- [ ] Identity exposure check handles clean/breached/error responses correctly
- [ ] History persists after restart
- [ ] PDF security report downloads successfully
- [ ] Settings page shows Windows and current network information
- [ ] Uninstall removes application files
- [ ] Local user data remains under `%LOCALAPPDATA%\PrivacyGuard` unless intentionally deleted by the user

## Security and privacy review

- [ ] API is bound only to `127.0.0.1`
- [ ] Public/arbitrary network ranges cannot be supplied for scanning
- [ ] Scan range remains limited to 256 addresses
- [ ] No personal SQLite database is committed
- [ ] No secrets, tokens, or personal reports are committed
- [ ] README accurately states that the score is heuristic, not a certification
- [ ] README accurately states that Trusted means recognized, not proven secure
- [ ] Identity lookup privacy disclosure is visible in repository documentation

## Public beta notes

PrivacyGuard v2.1.0 should remain labelled **beta** until the installer has completed the manual Windows verification above. The current Windows executable is unsigned, so Windows SmartScreen may show an unknown-publisher warning.
