# Assignment 3 — AI Usage Log

## AI tool used
- ChatGPT

## Other development tools used
- Visual Studio Code for writing and testing the Flask project.
- PostgreSQL / pgAdmin for creating the database, tables, and checking stored records.
- Python for running the Flask application.

## Key prompts / requests made to AI
1. Asked for step-by-step help creating the PostgreSQL database and `schema.sql`.
2. Asked for help connecting Flask to PostgreSQL and testing the database connection.
3. Asked for help implementing registration, password hashing, email OTP generation, OTP expiry, OTP verification, sessions, and role-based access.
4. Asked for help adding CSS to the Flask HTML templates and fixing the dashboard rendering problem.
5. Reported the Flask `BuildError` for `student_page` and asked for the route/template mismatch to be fixed.
6. Asked what remained to complete Assignment 3 and used the assignment PDF to identify the required deliverables.

## What I accepted
- The basic normalized three-table design: `users`, `otp_codes`, and `user_sessions`.
- Password hashing with Werkzeug.
- Random six-digit OTP generation.
- Hashing OTPs before storing them.
- OTP expiry and a maximum number of verification attempts.
- Hashed session tokens and session expiry.
- Flask/Jinja `render_template()` for the dashboard.
- Role checks for student and instructor routes.
- A shared CSS file under Flask's `static/` directory.

## What I edited / corrected
- The dashboard initially referenced endpoint names that did not match the Flask route function names. The resulting `BuildError` was observed during testing. I corrected the dashboard links to use the actual Flask endpoints (`student` and `instructor`).
- The dashboard initially displayed Jinja expressions as text when the HTML was not being processed correctly. I corrected the project structure so templates are rendered through Flask and CSS is loaded from `static/style.css`.
- I removed unnecessary repeated styling and moved common CSS into one stylesheet.

## What I rejected / verified
- I did not submit AI output without testing it.
- I tested the Flask application locally through the browser.
- I tested registration, OTP verification, login, dashboard access, and role-based links.
- I used pgAdmin to verify that OTP records were being created and that the database was receiving authentication data.
- I corrected the route-name mismatch after Flask produced an actual error.

## Reflection
AI was used as an implementation and debugging assistant rather than as an unchecked source of final code. I ran the code locally, inspected PostgreSQL records, and corrected problems when the generated code did not match the actual Flask endpoint names or template structure. The final implementation was kept aligned with the assignment requirements and the working project environment.
