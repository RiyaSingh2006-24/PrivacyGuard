# Privacy Notes

PrivacyGuard is designed to keep network history and device-recognition state on the local machine.

- The local API binds to `127.0.0.1`.
- Scan history and trusted-device state are stored in a local SQLite database.
- Email addresses written to local history are masked.
- The SQLite database is excluded from Git.
- Identity exposure checks send the submitted email address to the configured external breach-intelligence provider so the lookup can be performed.

Users should review the external provider's privacy terms before using the identity exposure feature with personal information.
