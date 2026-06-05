"""
app.py – Bears Share Notification System (Demo)

Routes:
    GET  /       → show submission form
    POST /send   → process form, send emails, redirect to success page
"""

from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import pantrysoft_mock
import email_sender
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


@app.route("/")
def index():
    return render_template("form.html")


@app.route("/send", methods=["POST"])
def send():
    # ── 1. Read form data ──────────────────────────────────────────────
    food      = request.form.get("food", "").strip()
    location  = request.form.get("location", "").strip()
    room      = request.form.get("room", "").strip()
    end_time  = request.form.get("end_time", "").strip()
    notes     = request.form.get("notes", "").strip()

    if not all([food, location, room, end_time]):
        return render_template("form.html", error="All fields are required.")

    # ── 2. Get opted-in recipients ────────────────────────────────────
    print("\n" + "="*50)
    print("[App] New Bears Share submission received")
    print(f"      Food:     {food}")
    print(f"      Location: {location}, Room {room}")
    print(f"      Until:    {end_time}")

    recipients = pantrysoft_mock.get_optin_emails()
    print(f"[App] Recipients ({len(recipients)}): {recipients}")

    # ── 3. Send emails ────────────────────────────────────────────────
    result = email_sender.send_notification(
        food=food,
        location=location,
        room=room,
        end_time=end_time,
        notes=notes,
        recipients=recipients,
    )
    print(f"[App] Result: {result}")
    print("="*50 + "\n")

    # ── 4. Store summary in session and redirect ──────────────────────
    session["summary"] = {
        "food":       food,
        "location":   location,
        "room":       room,
        "end_time":   end_time,
        "notes":      notes,
        "sent":       result["sent"],
        "failed":     result["failed"],
        "total":      len(recipients),
        "sent_at":    datetime.now().strftime("%B %d, %Y at %I:%M %p"),
    }
    return redirect(url_for("success"))


@app.route("/success")
def success():
    summary = session.pop("summary", None)
    if not summary:
        return redirect(url_for("index"))
    return render_template("success.html", summary=summary)


if __name__ == "__main__":
    print("Bears Share Demo running at http://localhost:5000")
    app.run(debug=True)
