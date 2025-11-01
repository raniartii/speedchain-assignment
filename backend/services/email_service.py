import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
import json

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SMTP_FILE = DATA_DIR / "smtp.json"

def _load_smtp_cfg():
    if SMTP_FILE.exists():
        try:
            return json.loads(SMTP_FILE.read_text())
        except Exception:
            pass
    return None

def send_booking_confirmation(booking: dict) -> dict:
    """
    booking: {
      'name','email','table_type','seats','slot_iso','meal_preorder','note'
    }
    """
    cfg = _load_smtp_cfg()
    if not cfg:
        return {"ok": False, "error": "No smtp.json found in data/"}

    smtp_host = cfg.get("host")
    smtp_port = cfg.get("port", 587)
    smtp_user = cfg.get("username")
    smtp_pass = cfg.get("password")
    from_name = cfg.get("from_name", "BrewHub Café")
    from_email = cfg.get("from_email", smtp_user)
    brand_color = "#B88A44"  # BrewHub gold accent

    subject = f"Your BrewHub Café Booking Confirmation – {booking.get('slot_iso','')}"
    meal = booking.get("meal_preorder") or []
    note = (booking.get("note") or "").strip()

    # ============ HTML body ============
    html = f"""
    <html>
    <body style="font-family: 'Segoe UI', Helvetica, Arial, sans-serif; background-color:#f7f6f3; margin:0; padding:0;">
      <table align="center" width="100%" cellpadding="0" cellspacing="0" style="max-width:640px; margin:auto; background:white; border-radius:16px; overflow:hidden; box-shadow:0 4px 24px rgba(0,0,0,.1);">
        <tr>
          <td style="background:{brand_color}; color:white; padding:22px 28px; font-size:24px; font-weight:600;">
            ☕ BrewHub Café
          </td>
        </tr>
        <tr>
          <td style="padding:28px;">
            <h2 style="color:#222; font-size:22px; margin:0 0 10px;">Hi {booking['name']},</h2>
            <p style="color:#444; font-size:15px; line-height:1.6;">
              Thank you for choosing <strong>BrewHub Café</strong>! Your table has been successfully reserved.
            </p>

            <table cellpadding="6" cellspacing="0" style="margin-top:20px; border-collapse:collapse; width:100%; font-size:15px;">
              <tr><td style="color:#666;">📅 <b>Date & Time</b></td><td>{booking['slot_iso']}</td></tr>
              <tr><td style="color:#666;">🍽️ <b>Table Type</b></td><td>{booking['table_type'].title()}</td></tr>
              <tr><td style="color:#666;">👥 <b>Seats</b></td><td>{booking['seats']}</td></tr>
              {"<tr><td style='color:#666;'>🥐 <b>Pre-Order</b></td><td>" + ", ".join(meal) + "</td></tr>" if meal else ""}
              {"<tr><td style='color:#666;'>📝 <b>Note</b></td><td>" + note + "</td></tr>" if note else ""}
            </table>

            <p style="color:#444; font-size:15px; line-height:1.6; margin-top:20px;">
              Our baristas and staff are looking forward to welcoming you. If you need to modify or cancel this reservation,
              simply reply to this email at least 1 hour before your slot.
            </p>

            <p style="margin-top:30px; color:#999; font-size:13px;">
              — The BrewHub Team<br/>
              <a href="https://brewhub.example.com" style="color:{brand_color}; text-decoration:none;">brewhub.example.com</a>
            </p>
          </td>
        </tr>
        <tr>
          <td style="background:#fafafa; color:#999; font-size:12px; padding:14px 24px; text-align:center;">
            © {booking.get('slot_iso','')[:4]} BrewHub Café. All rights reserved.
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = booking["email"]

    msg.attach(MIMEText("Your BrewHub Café booking confirmation.", "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, [booking["email"]], msg.as_string())
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
