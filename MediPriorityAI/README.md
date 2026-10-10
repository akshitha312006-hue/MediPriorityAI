# MediPriority AI

MediPriority AI is a patient-intake and clinical-priority workflow web application. Reception staff can register patients, capture symptoms and optional vital signs, flag warning signs, and send records to a prioritized waiting queue. Staff can search records, update the workflow status, assign a clinician, and review each patient's intake details.

## Run locally (Windows)

1. Install Python 3.10 or newer.
2. Extract this folder.
3. Open Command Prompt in the `MediPriorityAI` folder.
4. Run:
   ```bat
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   py app.py
   ```
5. Open `http://127.0.0.1:5000` in your browser.

## Demo sign-in

- Email: `demo@medipriority.ai`
- Password: `Demo@123`

You can also create a new account from **Create account**. The SQLite database (`medipriority.db`) is created automatically in this folder and persists records between runs.

## Features

- Sign-in and account creation with hashed passwords
- Dashboard metrics and priority-ordered patient queue
- New-patient intake form with symptoms, history, optional vital signs, and warning-sign checklist
- Transparent screening label with explanation
- Patient record detail, clinician assignment, and workflow status updates
- Search and urgency filters
- SQLite database persistence and JSON endpoint at `/api/patients`

## Important safety boundary

The screening logic is a simple, transparent rule-based aid for demonstrating workflow; it is not an AI diagnosis or a validated medical triage system. It may miss serious conditions and must never be used to rule out an emergency. A qualified clinician must assess the patient and confirm or override the displayed priority. If someone appears acutely unwell, alert clinical staff and follow local emergency procedures regardless of the software result.

## Before public deployment

Set a strong `MEDIPRIORITY_SECRET` environment variable, use HTTPS, add CSRF protection and rate limiting, restrict role permissions, configure backups and audit logging, and obtain appropriate privacy/security review before entering real patient data. The included demo data is fictional.
