"""
email_sender.py – Sends Bears Share notification emails via SMTP.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config


def build_email_body(
    food: str, location: str, room: str, end_time: str, notes: str = ""
) -> tuple[str, str]:
    """Returns (plain_text, html) email body."""

    notes_plain = f"\n  Notes:    {notes}\n" if notes else ""
    notes_html = (
        f"""
      <tr style="background:#fff3f3;">
        <td style="padding:10px; border-bottom:1px solid #eee;"><strong>Notes</strong></td>
        <td style="padding:10px; border-bottom:1px solid #eee;">{notes}</td>
      </tr>"""
        if notes
        else ""
    )

    plain = f"""Hi there!

Free food is available through Bears Share right now!

  What:     {food}
  Where:    {location}, {room}
  Until:    {end_time}{notes_plain}

Stop by while it lasts!

— Bear Pantry Team
Missouri State University

---
You're receiving this because you opted in to Bears Share notifications.
To unsubscribe, update your preferences in the pantry portal.
"""

    html = f"""\
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 560px; margin: auto; color: #333;">
  <div style="background:#5E0009; padding:20px; border-radius:8px 8px 0 0; text-align:center;">
    <h1 style="color:#fff; margin:0; font-size:22px;">🐻 Bears Share Alert!</h1>
  </div>
  <div style="background:#fdf5f5; padding:24px; border-radius:0 0 8px 8px; border:1px solid #ddd;">
    <p style="font-size:16px;">Hi there,</p>
    <p style="font-size:16px;">Free food is available through <strong>Bears Share</strong> right now:</p>

    <table style="width:100%; border-collapse:collapse; margin:16px 0;">
      <tr style="background:#5E0009; color:#fff;">
        <th style="padding:10px; text-align:left; border-radius:4px 0 0 0;">Detail</th>
        <th style="padding:10px; text-align:left; border-radius:0 4px 0 0;">Info</th>
      </tr>
      <tr style="background:#fff;">
        <td style="padding:10px; border-bottom:1px solid #eee;"><strong>What</strong></td>
        <td style="padding:10px; border-bottom:1px solid #eee;">{food}</td>
      </tr>
      <tr style="background:#fdf5f5;">
        <td style="padding:10px; border-bottom:1px solid #eee;"><strong>Where</strong></td>
        <td style="padding:10px; border-bottom:1px solid #eee;">{location}, {room}</td>
      </tr>
      <tr style="background:#fff;">
        <td style="padding:10px; border-bottom:1px solid #eee;"><strong>Available Until</strong></td>
        <td style="padding:10px; border-bottom:1px solid #eee;">{end_time}</td>
      </tr>{notes_html}
    </table>

    <p style="font-size:15px;">Stop by while it lasts!</p>

    <hr style="border:none; border-top:1px solid #ddd; margin:20px 0;">
    <p style="font-size:12px; color:#888;">
      You're receiving this because you opted in to Bears Share notifications.<br>
      To unsubscribe, update your preferences in the pantry portal.
    </p>
    <p style="font-size:13px; color:#5E0009; font-weight:bold;">— Bear Pantry Team, Missouri State University</p>
  </div>
</body>
</html>
"""
    return plain, html


def send_notification(
    food: str,
    location: str,
    room: str,
    end_time: str,
    recipients: list[str],
    notes: str = "",
) -> dict:
    """
    Sends Bears Share notification to all recipients.
    Returns a result dict with 'sent', 'failed', and 'errors' keys.
    """
    if not recipients:
        print("[EmailSender] No recipients – nothing to send.")
        return {"sent": 0, "failed": 0, "errors": []}

    subject = f"🐻 Bears Share Alert: Free food at {location}, {room} — available until {end_time}"
    plain_body, html_body = build_email_body(food, location, room, end_time, notes)

    sent, failed, errors = 0, 0, []

    try:
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)

            for recipient in recipients:
                try:
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = subject
                    msg["From"]    = f"{config.FROM_NAME} <{config.FROM_EMAIL}>"
                    msg["To"]      = recipient

                    msg.attach(MIMEText(plain_body, "plain"))
                    msg.attach(MIMEText(html_body,  "html"))

                    server.sendmail(config.FROM_EMAIL, recipient, msg.as_string())
                    print(f"[EmailSender] ✓ Sent to {recipient}")
                    sent += 1

                except Exception as e:
                    print(f"[EmailSender] ✗ Failed for {recipient}: {e}")
                    failed += 1
                    errors.append({"recipient": recipient, "error": str(e)})

    except smtplib.SMTPAuthenticationError:
        msg = "SMTP authentication failed – check config.py credentials."
        print(f"[EmailSender] ERROR: {msg}")
        return {"sent": 0, "failed": len(recipients), "errors": [{"error": msg}]}

    except Exception as e:
        print(f"[EmailSender] SMTP connection error: {e}")
        return {"sent": 0, "failed": len(recipients), "errors": [{"error": str(e)}]}

    print(f"[EmailSender] Done – {sent} sent, {failed} failed.")
    return {"sent": sent, "failed": failed, "errors": errors}
