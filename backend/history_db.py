import json
import sqlite3
from datetime import datetime

from storage import DB_PATH


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            target TEXT,
            devices_found INTEGER DEFAULT 0,
            open_services INTEGER DEFAULT 0,
            risky_services INTEGER DEFAULT 0,
            breach_count INTEGER DEFAULT 0,
            security_score INTEGER,
            risk_level TEXT,
            status TEXT,
            details TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS known_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_key TEXT UNIQUE NOT NULL,
            mac_address TEXT,
            ip_address TEXT,
            device_name TEXT,
            device_type TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            times_seen INTEGER DEFAULT 1
        )
        """
    )

    connection.commit()
    connection.close()


def mask_email(email):
    if not email or "@" not in email:
        return "Hidden"
    username, domain = email.split("@", 1)
    if len(username) <= 1:
        masked_username = "*"
    else:
        masked_username = username[0] + "*" * (len(username) - 1)
    return f"{masked_username}@{domain}"


def save_network_scan(
    network,
    devices_found,
    open_services,
    risky_services,
    details=None,
):
    connection = get_connection()
    connection.execute(
        """
        INSERT INTO scan_history (
            event_type, created_at, target, devices_found,
            open_services, risky_services, breach_count,
            security_score, risk_level, status, details
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "Network Scan",
            datetime.now().isoformat(),
            network,
            devices_found,
            open_services,
            risky_services,
            0,
            None,
            "Medium" if risky_services > 0 else "Low",
            "Completed",
            json.dumps(details or {}),
        ),
    )
    connection.commit()
    connection.close()


def save_identity_check(
    email,
    breach_count,
    security_score,
    risk_level,
    breached,
    details=None,
):
    connection = get_connection()
    connection.execute(
        """
        INSERT INTO scan_history (
            event_type, created_at, target, devices_found,
            open_services, risky_services, breach_count,
            security_score, risk_level, status, details
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "Identity Check",
            datetime.now().isoformat(),
            mask_email(email),
            0,
            0,
            0,
            breach_count,
            security_score,
            risk_level,
            "Exposed" if breached else "Clear",
            json.dumps(details or {}),
        ),
    )
    connection.commit()
    connection.close()


def normalize_mac(mac_address):
    if not mac_address:
        return None
    value = mac_address.strip().replace("-", ":").upper()
    if value in ("", "UNKNOWN", "00:00:00:00:00:00"):
        return None
    return value


def track_devices(devices):
    connection = get_connection()
    cursor = connection.cursor()
    now = datetime.now().isoformat()
    new_devices = []

    for device in devices:
        mac_address = normalize_mac(device.get("mac"))
        ip_address = device.get("ip", "Unknown")
        device_key = (
            f"MAC:{mac_address}" if mac_address else f"IP:{ip_address}"
        )

        existing = cursor.execute(
            "SELECT * FROM known_devices WHERE device_key = ?",
            (device_key,),
        ).fetchone()

        if existing is None:
            cursor.execute(
                """
                INSERT INTO known_devices (
                    device_key, mac_address, ip_address, device_name,
                    device_type, first_seen, last_seen, times_seen
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    device_key,
                    mac_address,
                    ip_address,
                    device.get("name", "Network Device"),
                    device.get("type", "Unknown Device"),
                    now,
                    now,
                    1,
                ),
            )
            new_devices.append(
                {
                    "name": device.get("name", "Network Device"),
                    "ip": ip_address,
                    "mac": mac_address,
                    "type": device.get("type", "Unknown Device"),
                    "first_seen": now,
                }
            )
        else:
            cursor.execute(
                """
                UPDATE known_devices
                SET mac_address = ?, ip_address = ?, device_name = ?,
                    device_type = ?, last_seen = ?, times_seen = times_seen + 1
                WHERE device_key = ?
                """,
                (
                    mac_address,
                    ip_address,
                    device.get("name", existing["device_name"]),
                    device.get("type", existing["device_type"]),
                    now,
                    device_key,
                ),
            )

    connection.commit()
    connection.close()
    return new_devices


def get_known_devices():
    connection = get_connection()
    rows = connection.execute(
        "SELECT * FROM known_devices ORDER BY last_seen DESC"
    ).fetchall()
    connection.close()

    return [
        {
            "id": row["id"],
            "mac": row["mac_address"],
            "ip": row["ip_address"],
            "name": row["device_name"],
            "type": row["device_type"],
            "first_seen": row["first_seen"],
            "last_seen": row["last_seen"],
            "times_seen": row["times_seen"],
        }
        for row in rows
    ]


def get_history(limit=100):
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT id, event_type, created_at, target, devices_found,
               open_services, risky_services, breach_count,
               security_score, risk_level, status
        FROM scan_history
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def clear_history():
    connection = get_connection()
    connection.execute("DELETE FROM scan_history")
    connection.commit()
    connection.close()


init_db()
