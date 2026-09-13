# Assignment 3 — Security Risks and Mitigations

## 1. Plain-text password storage
**Risk:** A database leak could expose users' passwords.

**Mitigation:** Passwords are processed with Werkzeug's password hashing functions and only `password_hash` is stored.

## 2. OTP exposure or unlimited guessing
**Risk:** An attacker could repeatedly guess an OTP.

**Mitigation:** The application stores only `otp_hash`, gives OTPs a short expiry period, invalidates older OTPs, and limits verification attempts.

## 3. Session-token theft
**Risk:** A stolen session token could be used to impersonate a user.

**Mitigation:** Only a SHA-256 hash of the session token is stored in PostgreSQL. The browser cookie is also marked `HttpOnly` and `SameSite=Lax`, and sessions have an expiry time.

## 4. Unauthorized role access
**Risk:** A student could try to access instructor functionality directly by changing the URL.

**Mitigation:** The Flask routes check the authenticated user's role before allowing access to the student or instructor area.

## 5. Database credentials exposure
**Risk:** Hard-coding database or SMTP credentials in source code can expose secrets.

**Mitigation:** Credentials are loaded from environment variables in `.env`, and `.env` should not be committed to GitHub.
