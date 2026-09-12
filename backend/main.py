from concurrent.futures import ThreadPoolExecutor
import ipaddress
import platform
import re
import socket
import subprocess

import httpx
import psutil
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from frontend_host import mount_frontend
from history_db import (
    get_history,
    get_known_devices,
    save_identity_check,
    save_network_scan,
    track_devices,
)
from report_api import router as report_router
from trusted_api import router as trusted_router

app = FastAPI(
    title="PrivacyGuard Security Engine",
    version="2.1.0",
)

app.include_router(trusted_router)
app.include_router(report_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PORT_DATABASE = {
    21: {
        "service": "FTP",
        "risk": "Medium",
        "recommendation": "Avoid exposing FTP unless required. Prefer SFTP.",
    },
    22: {
        "service": "SSH",
        "risk": "Low",
        "recommendation": "Use strong authentication and restrict unnecessary remote access.",
    },
    23: {
        "service": "Telnet",
        "risk": "High",
        "recommendation": "Disable Telnet and use SSH instead.",
    },
    53: {
        "service": "DNS",
        "risk": "Low",
        "recommendation": "Confirm that the DNS service is intentionally available.",
    },
    80: {
        "service": "HTTP",
        "risk": "Medium",
        "recommendation": "Prefer HTTPS for sensitive or administrative web interfaces.",
    },
    443: {
        "service": "HTTPS",
        "risk": "Low",
        "recommendation": "Keep certificates and TLS configuration updated.",
    },
    445: {
        "service": "SMB",
        "risk": "High",
        "recommendation": "Restrict SMB access to trusted devices and keep systems patched.",
    },
    3389: {
        "service": "RDP",
        "risk": "High",
        "recommendation": "Restrict Remote Desktop access and require strong authentication.",
    },
    8080: {
        "service": "HTTP Alternate",
        "risk": "Medium",
        "recommendation": "Verify that this web service is intentionally exposed.",
    },
}


def get_hostname():
    return socket.gethostname()


def get_operating_system():
    return f"{platform.system()} {platform.release()}"


def get_local_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "Unknown"
    finally:
        sock.close()


def get_interface_details(local_ip):
    if local_ip == "Unknown":
        return "Unknown", "Unknown"

    for interface_name, addresses in psutil.net_if_addrs().items():
        for address in addresses:
            if address.family == socket.AF_INET and address.address == local_ip:
                return interface_name, address.netmask or "Unknown"

    return "Unknown", "Unknown"


def get_local_mac(interface_name):
    try:
        for address in psutil.net_if_addrs().get(interface_name, []):
            family_name = str(address.family).lower()
            if "link" in family_name or "packet" in family_name:
                mac = (address.address or "").replace("-", ":").upper()
                if mac and mac != "00:00:00:00:00:00":
                    return mac
    except Exception:
        pass
    return None


def get_network_range(local_ip, netmask):
    if local_ip == "Unknown" or netmask == "Unknown":
        return "Unknown"
    try:
        return str(
            ipaddress.IPv4Network(
                f"{local_ip}/{netmask}",
                strict=False,
            )
        )
    except Exception:
        return "Unknown"


def get_linux_gateway():
    try:
        result = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        match = re.search(r"default via ([0-9.]+)", result.stdout)
        if match:
            return match.group(1)
    except Exception:
        pass
    return "Unknown"


def get_windows_gateway():
    try:
        result = subprocess.run(
            ["route", "print", "-4"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in result.stdout.splitlines():
            parts = line.split()
            if (
                len(parts) >= 5
                and parts[0] == "0.0.0.0"
                and parts[1] == "0.0.0.0"
            ):
                try:
                    ipaddress.IPv4Address(parts[2])
                    return parts[2]
                except ValueError:
                    continue
    except Exception:
        pass
    return "Unknown"


def get_default_gateway():
    system = platform.system().lower()
    if system == "linux":
        return get_linux_gateway()
    if system == "windows":
        return get_windows_gateway()
    return "Unknown"


def is_allowed_local_network(network):
    try:
        first_host = next(network.hosts(), network.network_address)
        if first_host.is_private:
            return True
        return first_host in ipaddress.IPv4Network("100.64.0.0/10")
    except Exception:
        return False


def ping_host(ip):
    system = platform.system().lower()
    try:
        if system == "windows":
            command = ["ping", "-n", "1", "-w", "700", str(ip)]
        else:
            command = ["ping", "-c", "1", "-W", "1", str(ip)]

        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
        return result.returncode == 0
    except Exception:
        return False


def get_mac_address(ip, local_ip, interface_name):
    if ip == local_ip:
        return get_local_mac(interface_name)

    system = platform.system().lower()
    try:
        if system == "linux":
            result = subprocess.run(
                ["ip", "neigh", "show", str(ip)],
                capture_output=True,
                text=True,
                timeout=3,
            )
            match = re.search(
                r"lladdr\s+([0-9a-fA-F:]{17})",
                result.stdout,
            )
        elif system == "windows":
            result = subprocess.run(
                ["arp", "-a", str(ip)],
                capture_output=True,
                text=True,
                timeout=3,
            )
            match = re.search(
                r"([0-9a-fA-F]{2}(?:[:-][0-9a-fA-F]{2}){5})",
                result.stdout,
            )
        else:
            return None

        if match:
            return match.group(1).replace("-", ":").upper()
    except Exception:
        pass
    return None


def check_port(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.35)
    try:
        return sock.connect_ex((str(ip), port)) == 0
    except Exception:
        return False
    finally:
        sock.close()


def scan_host_ports(ip):
    findings = []
    for port, details in PORT_DATABASE.items():
        if check_port(ip, port):
            findings.append(
                {
                    "port": port,
                    "service": details["service"],
                    "risk": details["risk"],
                    "recommendation": details["recommendation"],
                }
            )
    return findings


def calculate_device_risk(services):
    risks = [service["risk"] for service in services]
    if "High" in risks:
        return "High"
    if "Medium" in risks:
        return "Medium"
    return "Low"


class IdentityCheckRequest(BaseModel):
    email: str


def calculate_identity_risk(breaches):
    if not breaches:
        return {"score": 100, "level": "Low"}

    score = 100
    for breach in breaches:
        score -= 8
        exposed = breach.get("xposed_data", "").lower()
        password_risk = breach.get("password_risk", "").lower()

        if "password" in exposed:
            score -= 12
        if "phone" in exposed:
            score -= 5
        if "address" in exposed:
            score -= 5
        if password_risk in ("plaintext", "easytocrack"):
            score -= 10

    score = max(score, 0)
    level = "Low" if score >= 80 else "Medium" if score >= 55 else "High"
    return {"score": score, "level": level}


@app.get("/")
def root():
    return {
        "application": "PrivacyGuard",
        "engine": "Local Security Engine",
        "version": "2.1.0",
        "status": "running",
        "operating_system": get_operating_system(),
    }


@app.get("/api/health")
def health():
    return {
        "status": "online",
        "message": "PrivacyGuard security engine is running",
        "version": "2.1.0",
        "platform": get_operating_system(),
    }


@app.get("/api/network/info")
def network_info():
    local_ip = get_local_ip()
    interface, netmask = get_interface_details(local_ip)
    return {
        "hostname": get_hostname(),
        "operating_system": get_operating_system(),
        "interface": interface,
        "local_ip": local_ip,
        "netmask": netmask,
        "gateway": get_default_gateway(),
        "network_range": get_network_range(local_ip, netmask),
        "environment": f"{platform.system()} Local Security Agent",
    }


@app.get("/api/network/scan")
def scan_network():
    local_ip = get_local_ip()
    interface, netmask = get_interface_details(local_ip)
    network_range = get_network_range(local_ip, netmask)
    gateway = get_default_gateway()

    if network_range == "Unknown":
        return {
            "status": "error",
            "message": "PrivacyGuard could not determine the local network range.",
        }

    try:
        network = ipaddress.ip_network(network_range, strict=False)
    except ValueError:
        return {"status": "error", "message": "Invalid local network range."}

    if not is_allowed_local_network(network):
        return {
            "status": "error",
            "message": "PrivacyGuard only scans private local networks.",
        }

    if network.num_addresses > 256:
        return {
            "status": "error",
            "message": "PrivacyGuard limits scans to a maximum of 256 local addresses.",
        }

    hosts = list(network.hosts())
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(ping_host, hosts))

    discovered_ips = [
        str(ip) for ip, alive in zip(hosts, results) if alive
    ]

    devices = []
    for ip in discovered_ips:
        services = scan_host_ports(ip)
        risk = calculate_device_risk(services)
        mac_address = get_mac_address(ip, local_ip, interface)

        if ip == local_ip:
            name = get_hostname()
            device_type = f"{platform.system()} Computer"
        elif ip == gateway:
            name = "Default Gateway"
            device_type = "Gateway / Router"
        else:
            name = "Network Device"
            device_type = "Unknown Device"

        devices.append(
            {
                "name": name,
                "ip": ip,
                "mac": mac_address,
                "type": device_type,
                "status": "online",
                "risk": risk,
                "open_ports": [service["port"] for service in services],
                "services": services,
            }
        )

    try:
        new_devices = track_devices(devices)
    except Exception as error:
        print("Device tracking error:", error)
        new_devices = []

    new_device_keys = {
        f"MAC:{device['mac']}" if device.get("mac") else f"IP:{device['ip']}"
        for device in new_devices
    }

    for device in devices:
        key = (
            f"MAC:{device['mac']}"
            if device.get("mac")
            else f"IP:{device['ip']}"
        )
        device["is_new"] = key in new_device_keys

    findings = []
    for device in devices:
        for service in device["services"]:
            findings.append(
                {
                    "ip": device["ip"],
                    "device": device["name"],
                    "port": service["port"],
                    "service": service["service"],
                    "risk": service["risk"],
                    "recommendation": service["recommendation"],
                }
            )

    risky_services = sum(
        1 for finding in findings if finding["risk"] in ("Medium", "High")
    )
    open_services = sum(len(device["services"]) for device in devices)

    try:
        save_network_scan(
            network=network_range,
            devices_found=len(devices),
            open_services=open_services,
            risky_services=risky_services,
            details={
                "findings": findings,
                "new_devices": new_devices,
            },
        )
    except Exception as error:
        print("Network history error:", error)

    return {
        "status": "success",
        "network": network_range,
        "platform": platform.system(),
        "devices_found": len(devices),
        "open_services": open_services,
        "risky_services": risky_services,
        "new_device_count": len(new_devices),
        "new_devices": new_devices,
        "devices": devices,
        "findings": findings,
    }


@app.get("/api/network/devices")
def known_device_list():
    try:
        devices = get_known_devices()
        return {
            "status": "success",
            "count": len(devices),
            "devices": devices,
        }
    except Exception as error:
        print("Known devices error:", error)
        return {
            "status": "error",
            "message": "Unable to load known devices.",
        }


@app.post("/api/identity/check")
async def check_identity(request: IdentityCheckRequest):
    email = request.email.strip()

    if "@" not in email or "." not in email.split("@")[-1]:
        return {"status": "error", "message": "Please enter a valid email address."}

    url = "https://api.xposedornot.com/v1/breach-analytics"

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.get(url, params={"email": email})

        if response.status_code == 429:
            return {
                "status": "error",
                "message": "Breach intelligence rate limit reached. Please try again later.",
            }

        if response.status_code != 200:
            return {
                "status": "error",
                "message": "Breach intelligence service is temporarily unavailable.",
            }

        data = response.json()
        exposed_section = data.get("ExposedBreaches")

        if not exposed_section:
            save_identity_check(
                email=email,
                breach_count=0,
                security_score=100,
                risk_level="Low",
                breached=False,
                details={},
            )
            return {
                "status": "success",
                "email": email,
                "breached": False,
                "breach_count": 0,
                "security_score": 100,
                "risk_level": "Low",
                "breaches": [],
                "recommendations": [
                    "Continue using unique passwords for every account.",
                    "Keep multi-factor authentication enabled where available.",
                    "Monitor important accounts for unusual activity.",
                ],
            }

        breaches = exposed_section.get("breaches_details", [])
        formatted_breaches = []

        for breach in breaches:
            exposed_data = breach.get("xposed_data", "")
            formatted_breaches.append(
                {
                    "name": breach.get("breach", "Unknown"),
                    "domain": breach.get("domain", "Unknown"),
                    "year": breach.get("xposed_date", "Unknown"),
                    "industry": breach.get("industry", "Unknown"),
                    "exposed_data": [
                        item.strip()
                        for item in exposed_data.split(";")
                        if item.strip()
                    ],
                    "password_risk": breach.get("password_risk", "unknown"),
                    "records": breach.get("xposed_records", 0),
                    "verified": breach.get("verified", "Unknown"),
                }
            )

        risk = calculate_identity_risk(breaches)
        recommendations = [
            "Change passwords for affected accounts that are still active.",
            "Do not reuse passwords across different websites.",
            "Enable multi-factor authentication wherever possible.",
            "Watch for phishing messages related to exposed account information.",
        ]

        save_identity_check(
            email=email,
            breach_count=len(formatted_breaches),
            security_score=risk["score"],
            risk_level=risk["level"],
            breached=True,
            details={},
        )

        return {
            "status": "success",
            "email": email,
            "breached": True,
            "breach_count": len(formatted_breaches),
            "security_score": risk["score"],
            "risk_level": risk["level"],
            "breaches": formatted_breaches,
            "recommendations": recommendations,
        }

    except httpx.RequestError:
        return {
            "status": "error",
            "message": "Unable to reach the breach intelligence service.",
        }
    except Exception as error:
        print("Identity checker error:", error)
        return {
            "status": "error",
            "message": "An unexpected identity-check error occurred.",
        }


@app.get("/api/history")
def history():
    try:
        records = get_history(limit=100)
        return {
            "status": "success",
            "count": len(records),
            "history": records,
        }
    except Exception as error:
        print("History API error:", error)
        return {
            "status": "error",
            "message": "Unable to load PrivacyGuard history.",
        }


mount_frontend(app)
