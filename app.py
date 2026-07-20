"""
app.py – Bears Share Notification System

Routes:
    GET  /                    → show submission form
    POST /send                → validate access code, send emails, log, redirect
    GET  /success             → confirmation page
    GET  /subscribers         → subscriber list status + CSV upload form
    POST /subscribers         → import a PantrySoft CSV export (replaces list)
    GET  /unsubscribe/<token> → one-click unsubscribe (signed link from emails)
    GET  /history             → log of past broadcasts
"""

import csv
import io
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session

import config
import db
import email_sender
import pantrysoft_mock
import tokens

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

db.init_db()


def _check_access_code(submitted: str) -> bool:
    """True if the access code matches (or no code is configured)."""
    return not config.ACCESS_CODE or submitted == config.ACCESS_CODE


@app.route("/")
def index():
    return render_template("form.html", access_code_required=bool(config.ACCESS_CODE))


@app.route("/send", methods=["POST"])
def send():
    # ── 1. Read form data ──────────────────────────────────────────────
    food      = request.form.get("food", "").strip()
    location  = request.form.get("location", "").strip()
    room      = request.form.get("room", "").strip()
    end_time  = request.form.get("end_time", "").strip()
    notes     = request.form.get("notes", "").strip()
    code      = request.form.get("access_code", "").strip()

    if not _check_access_code(code):
        return render_template(
            "form.html", error="Invalid access code.",
            access_code_required=bool(config.ACCESS_CODE),
        ), 403

    if not all([food, location, room, end_time]):
        return render_template(
            "form.html", error="All fields are required.",
            access_code_required=bool(config.ACCESS_CODE),
        )

    # ── 2. Get opted-in recipients (suppression list already filtered) ─
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

    if result["sent"] == 0 and recipients:
        first_error = (result["errors"][0].get("error", "unknown error")
                       if result["errors"] else "unknown error")
        return render_template(
            "form.html",
            error=f"No emails could be sent — {first_error}",
            access_code_required=bool(config.ACCESS_CODE),
        ), 502

    # ── 4. Log the broadcast ──────────────────────────────────────────
    db.log_send(
        food=food, location=location, room=room, end_time=end_time, notes=notes,
        sent=result["sent"], failed=result["failed"], total=len(recipients),
    )

    # ── 5. Store summary in session and redirect ──────────────────────
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


@app.route("/subscribers", methods=["GET", "POST"])
def subscribers():
    ctx = {
        "subscriber_count": db.subscriber_count(),
        "suppressed_count": db.suppressed_count(),
        "access_code_required": bool(config.ACCESS_CODE),
    }

    if request.method == "POST":
        if not _check_access_code(request.form.get("access_code", "").strip()):
            return render_template("subscribers.html", error="Invalid access code.", **ctx), 403

        file = request.files.get("csv_file")
        if not file or not file.filename:
            return render_template("subscribers.html", error="Please choose a CSV file.", **ctx)

        try:
            text = file.read().decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text))
            fields = [f.strip().lower() for f in (reader.fieldnames or [])]
            email_col = next((f for f in fields if "email" in f), None)
            name_col  = next((f for f in fields if "name" in f), None)
            if not email_col:
                return render_template(
                    "subscribers.html",
                    error="No email column found — the CSV needs a header row "
                          "with an 'email' column (PantrySoft export default).",
                    **ctx,
                )
            rows = []
            for raw in reader:
                row = {k.strip().lower(): (v or "") for k, v in raw.items() if k}
                rows.append({
                    "email": row.get(email_col, ""),
                    "name": row.get(name_col, "") if name_col else "",
                })
            imported = db.replace_subscribers(rows)
        except Exception as e:
            return render_template("subscribers.html", error=f"Import failed: {e}", **ctx)

        ctx["subscriber_count"] = db.subscriber_count()
        return render_template(
            "subscribers.html",
            message=f"Imported {imported} subscribers (previous list replaced). "
                    f"Unsubscribed users stay excluded automatically.",
            **ctx,
        )

    return render_template("subscribers.html", **ctx)


@app.route("/unsubscribe/<token>")
def unsubscribe(token):
    email = tokens.verify_unsubscribe_token(token)
    if not email:
        return render_template("unsubscribe.html", ok=False), 404
    db.suppress_email(email)
    print(f"[App] Unsubscribed: {email}")
    return render_template("unsubscribe.html", ok=True, email=email, token=token)


@app.route("/resubscribe/<token>")
def resubscribe(token):
    email = tokens.verify_unsubscribe_token(token)
    if not email:
        return render_template("unsubscribe.html", ok=False), 404
    db.unsuppress_email(email)
    print(f"[App] Resubscribed: {email}")
    return render_template("unsubscribe.html", ok=True, resubscribed=True, email=email)


@app.route("/history")
def history():
    return render_template("history.html", logs=db.get_send_logs())


if __name__ == "__main__":
    print("Bears Share running at http://localhost:5000")
    app.run(debug=True)
