from datetime import datetime
import sqlite3

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from storage import DB_PATH

router = APIRouter()


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_trusted_columns():
    connection = get_connection()
    cursor = connection.cursor()

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

    columns = cursor.execute(
        "PRAGMA table_info(known_devices)"
    ).fetchall()
    column_names = [column["name"] for column in columns]

    if "trusted" not in column_names:
        cursor.execute(
            """
            ALTER TABLE known_devices
            ADD COLUMN trusted INTEGER NOT NULL DEFAULT 0
            """
        )

    if "trusted_at" not in column_names:
        cursor.execute(
            """
            ALTER TABLE known_devices
            ADD COLUMN trusted_at TEXT
            """
        )

    connection.commit()
    connection.close()


ensure_trusted_columns()


class DeviceTrustRequest(BaseModel):
    trusted: bool


@router.get("/api/network/trust-status")
def get_trust_status():
    connection = get_connection()
    rows = connection.execute(
        "SELECT id, trusted, trusted_at FROM known_devices"
    ).fetchall()
    connection.close()

    devices = [
        {
            "id": row["id"],
            "trusted": bool(row["trusted"]),
            "trusted_at": row["trusted_at"],
        }
        for row in rows
    ]

    return {
        "status": "success",
        "trusted_ids": [d["id"] for d in devices if d["trusted"]],
        "devices": devices,
    }


@router.patch("/api/network/devices/{device_id}/trust")
def update_device_trust(device_id: int, request: DeviceTrustRequest):
    connection = get_connection()
    cursor = connection.cursor()

    device = cursor.execute(
        "SELECT * FROM known_devices WHERE id = ?",
        (device_id,),
    ).fetchone()

    if device is None:
        connection.close()
        raise HTTPException(status_code=404, detail="Device not found.")

    trusted_at = datetime.now().isoformat() if request.trusted else None

    cursor.execute(
        """
        UPDATE known_devices
        SET trusted = ?, trusted_at = ?
        WHERE id = ?
        """,
        (1 if request.trusted else 0, trusted_at, device_id),
    )
    connection.commit()
    connection.close()

    return {
        "status": "success",
        "device_id": device_id,
        "trusted": request.trusted,
        "trusted_at": trusted_at,
        "message": (
            "Device marked as trusted."
            if request.trusted
            else "Device removed from trusted devices."
        ),
    }
