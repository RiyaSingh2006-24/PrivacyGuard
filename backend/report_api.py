from datetime import datetime
from io import BytesIO
import sqlite3

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from storage import DB_PATH

router = APIRouter()


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def get_latest_event(event_type):
    connection = get_connection()
    row = connection.execute(
        """
        SELECT * FROM scan_history
        WHERE event_type = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (event_type,),
    ).fetchone()
    connection.close()
    return dict(row) if row else None


def get_recent_history(limit=10):
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT event_type, created_at, target, devices_found,
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


def get_device_summary():
    connection = get_connection()
    try:
        total = connection.execute(
            "SELECT COUNT(*) FROM known_devices"
        ).fetchone()[0]
        trusted = connection.execute(
            "SELECT COUNT(*) FROM known_devices WHERE trusted = 1"
        ).fetchone()[0]
    except sqlite3.OperationalError:
        total = 0
        trusted = 0
    connection.close()
    return {
        "total": total,
        "trusted": trusted,
        "untrusted": total - trusted,
    }


def calculate_security_score(network, identity):
    network_score = None
    identity_score = None

    if network:
        risky_services = network.get("risky_services") or 0
        open_services = network.get("open_services") or 0
        risky_penalty = min(risky_services * 15, 45)
        open_penalty = min(open_services * 2, 10)
        network_score = max(0, 100 - risky_penalty - open_penalty)

    if identity:
        identity_score = identity.get("security_score")

    if network_score is not None and identity_score is not None:
        score = round(network_score * 0.55 + identity_score * 0.45)
    elif network_score is not None:
        score = network_score
    elif identity_score is not None:
        score = identity_score
    else:
        score = 100

    risk = "High" if score < 70 else "Medium" if score < 90 else "Low"
    return score, risk


def make_table(rows, widths, header=False):
    table = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BCCCDC")),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]

    if header:
        style.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#102A43")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    else:
        style.extend(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF4F8")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ]
        )

    table.setStyle(TableStyle(style))
    return table


@router.get("/api/report/security")
def generate_security_report():
    latest_network = get_latest_event("Network Scan")
    latest_identity = get_latest_event("Identity Check")
    history = get_recent_history(10)
    devices = get_device_summary()
    security_score, overall_risk = calculate_security_score(
        latest_network,
        latest_identity,
    )

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=45,
        bottomMargin=45,
        title="PrivacyGuard Security Report",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PrivacyGuardTitle",
        parent=styles["Title"],
        fontSize=24,
        leading=28,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#102A43"),
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        "PrivacyGuardSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#627D98"),
        spaceAfter=18,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#0B6E99"),
        spaceBefore=12,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=9,
        leading=14,
        textColor=colors.HexColor("#334E68"),
    )
    note_style = ParagraphStyle(
        "Note",
        parent=body_style,
        fontSize=8,
        textColor=colors.HexColor("#7C5C20"),
        leading=12,
    )

    story = [
        Paragraph("PrivacyGuard", title_style),
        Paragraph(
            "Personal Digital Exposure & Home Network Security Report",
            subtitle_style,
        ),
        Paragraph(
            f"Generated: {datetime.now().strftime('%d %B %Y • %I:%M %p')}",
            subtitle_style,
        ),
        Paragraph("Overall Security Posture", section_style),
        make_table(
            [
                ["Security Score", "Risk Level", "Known Devices", "Trusted Devices"],
                [
                    f"{security_score}/100",
                    overall_risk,
                    str(devices["total"]),
                    str(devices["trusted"]),
                ],
            ],
            [115, 115, 115, 115],
            header=True,
        ),
        Spacer(1, 10),
        Paragraph(
            "The PrivacyGuard score is an advisory heuristic based on network exposure "
            "and identity-exposure results. It is not a formal security certification.",
            note_style,
        ),
        Paragraph("Network Security", section_style),
    ]

    if latest_network:
        story.append(
            make_table(
                [
                    ["Protected Network", latest_network.get("target") or "Unknown"],
                    ["Devices Found", str(latest_network.get("devices_found") or 0)],
                    ["Open Services", str(latest_network.get("open_services") or 0)],
                    ["Risky Services", str(latest_network.get("risky_services") or 0)],
                    ["Risk Level", latest_network.get("risk_level") or "Unknown"],
                    ["Last Scan", latest_network.get("created_at") or "Unknown"],
                ],
                [150, 310],
            )
        )
    else:
        story.append(Paragraph("No network scan has been completed yet.", body_style))

    story.extend(
        [
            Paragraph("Device Recognition", section_style),
            make_table(
                [
                    ["Remembered Devices", str(devices["total"])],
                    ["Trusted / Recognized", str(devices["trusted"])],
                    ["Not Marked Trusted", str(devices["untrusted"])],
                ],
                [230, 230],
            ),
            Spacer(1, 7),
            Paragraph(
                "Trusted means the user recognizes the device. It does not guarantee "
                "that the device itself is secure.",
                note_style,
            ),
            Paragraph("Identity Exposure", section_style),
        ]
    )

    if latest_identity:
        identity_score = latest_identity.get("security_score")
        story.append(
            make_table(
                [
                    ["Identity", latest_identity.get("target") or "Masked"],
                    ["Known Breaches", str(latest_identity.get("breach_count") or 0)],
                    [
                        "Identity Score",
                        f"{identity_score}/100" if identity_score is not None else "Unavailable",
                    ],
                    ["Risk Level", latest_identity.get("risk_level") or "Unknown"],
                    ["Status", latest_identity.get("status") or "Unknown"],
                ],
                [150, 310],
            )
        )
    else:
        story.append(
            Paragraph("No identity exposure check has been completed yet.", body_style)
        )

    story.extend([PageBreak(), Paragraph("Recent Security Activity", section_style)])

    if history:
        rows = [["Event", "Target", "Risk", "Status", "Date"]]
        for item in history:
            created_at = item.get("created_at") or ""
            if "T" in created_at:
                created_at = created_at.replace("T", " ")[:16]
            rows.append(
                [
                    item.get("event_type") or "",
                    item.get("target") or "",
                    item.get("risk_level") or "",
                    item.get("status") or "",
                    created_at,
                ]
            )
        story.append(make_table(rows, [92, 130, 65, 72, 105], header=True))
    else:
        story.append(Paragraph("No security activity is currently stored.", body_style))

    story.append(Paragraph("Recommended Actions", section_style))
    recommendations = []

    if latest_network and (latest_network.get("risky_services") or 0) > 0:
        recommendations.append(
            "Review Medium and High-risk network services and disable services that are not required."
        )
    if latest_network and (latest_network.get("open_services") or 0) > 0:
        recommendations.append(
            "Confirm that detected open services are intentionally enabled."
        )
    if devices["untrusted"] > 0:
        recommendations.append(
            "Review devices that have not been marked trusted and confirm that you recognize them."
        )
    if latest_identity and (latest_identity.get("breach_count") or 0) > 0:
        recommendations.append(
            "Change affected account passwords, avoid password reuse, and enable multi-factor authentication."
        )
    if not recommendations:
        recommendations.append(
            "Continue regular network scans, keep devices updated, use unique passwords, and enable multi-factor authentication."
        )

    for recommendation in recommendations:
        story.extend([Paragraph(f"• {recommendation}", body_style), Spacer(1, 5)])

    story.extend(
        [
            Spacer(1, 15),
            Paragraph(
                "<b>Authorized Use Notice:</b> PrivacyGuard is designed for networks and "
                "systems that the user owns or has explicit permission to assess.",
                note_style,
            ),
        ]
    )

    document.build(story)
    buffer.seek(0)

    filename = (
        "PrivacyGuard_Security_Report_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".pdf"
    )

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
