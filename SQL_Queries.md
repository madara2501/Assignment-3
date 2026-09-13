# Assignment 3 — Representative SQL Queries

## Query 1: Find verified students

```sql
SELECT id, full_name, email, created_at
FROM users
WHERE role = 'student'
  AND is_verified = TRUE
ORDER BY created_at DESC;
```

**Explanation:** This query returns users whose role is `student` and whose email verification is complete. Results are ordered with the newest registrations first.

## Query 2: Find active sessions

```sql
SELECT
    u.full_name,
    u.email,
    u.role,
    s.created_at AS session_created_at,
    s.expires_at
FROM users u
JOIN user_sessions s
    ON u.id = s.user_id
WHERE s.expires_at > CURRENT_TIMESTAMP
ORDER BY s.created_at DESC;
```

**Explanation:** This joins `users` with `user_sessions` through `user_id` and returns sessions whose expiry time is still in the future. It demonstrates the relationship between users and session records.
