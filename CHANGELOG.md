# Changelog

## 2.1.0 — Beta

### Added

- Local-first FastAPI security engine bound to `127.0.0.1`
- React/Vite dashboard bundled into the packaged application
- Private local-network discovery with a 256-address safety limit
- Selected TCP service exposure checks and risk recommendations
- Persistent known-device registry
- First-seen/new-device detection
- User-controlled Trusted/recognized device state
- Identity exposure lookup with masked local history
- SQLite-backed activity history
- Transparent heuristic security posture score
- Downloadable PDF security report
- Cross-platform Linux/Windows network-detection logic
- Persistent per-user application-data storage
- Linux PyInstaller packaging
- Windows PyInstaller build script
- Inno Setup Windows installer definition
- GitHub Actions Windows build, packaged-app health smoke test, and installer artifacts

### Security and privacy notes

- PrivacyGuard does not treat an open port as proof of a vulnerability.
- The security score is advisory and is not CVSS or a certification.
- Trusted means recognized by the user; it does not prove a device is secure.
- Identity exposure checks send the submitted email address to the configured external breach-intelligence provider.

### Known limitations

- Ping-based discovery may miss hosts that ignore ICMP.
- MAC resolution depends on the operating system's neighbor/ARP cache.
- Windows remains beta until the generated installer completes the manual clean-machine checklist.
- Windows packages are currently unsigned and may trigger SmartScreen warnings.
