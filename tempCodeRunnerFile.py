
    token = request.cookies.get("session_token")

    if not token:
        return redirect(url_for("login"))

    token_hash = hash_token(token)

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                u.id,
                u.full_name,
                u.email,
                u.role,
                u.is_verified
            FROM users u
            JOIN user_sessions s
                ON u.id = s.user_id
            WHERE s.session_token_hash = %s
            AND s.expires_at > CURRENT_TIMESTAMP
            """,
            (token_hash,)
        )

        user = cursor.fetchone()

    finally:
        cursor.close()
        connection.close()

    if not user:
        return redirect(url_for("login"))

    return render_template("dashboard.html", user=user)