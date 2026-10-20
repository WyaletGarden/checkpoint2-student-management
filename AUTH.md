# Authentication

Install dependencies with `uv sync`, then run `uv run alembic upgrade head`.

Set `JWT_SECRET_KEY` in `.env` to a random secret (at least 32 bytes), shared
by all application workers. Generate one with
`uv run python -c "import secrets; print(secrets.token_urlsafe(48))"`.
Without this setting, the app generates a temporary key on each process start;
tokens will stop working after a restart or across different workers.
`ACCESS_TOKEN_EXPIRE_MINUTES` defaults to 30.

Both endpoints accept JSON:

```json
{"username": "student01", "password": "StrongPassword123!"}
```

- `POST /register`: returns 201 with `id` and `username`; duplicates return 409.
- `POST /login`: returns `access_token` and `token_type: "bearer"`;
  incorrect credentials return 401.

Usernames contain 1–64 ASCII letters, digits, underscores, dots or hyphens
and are case-sensitive. Passwords require at least 8 characters and at most
72 UTF-8 bytes. Only salted bcrypt hashes are stored in the database.
JWTs use HS256 and contain the user ID in `sub`, plus `iat` and `exp`.
All `/api/v1/students`, `/api/v1/classes`, `/api/v1/teachers` endpoints and
`/demo/fixed-n-plus-1` require the header `Authorization: Bearer <access_token>`.
Missing, malformed, expired, incorrectly signed tokens, or tokens for deleted
users return 401 with `WWW-Authenticate: Bearer`.
`/register`, `/login`, the frontend and API documentation remain public.
In Swagger `/docs`, click **Authorize** and paste the access token.
Use `Depends(get_current_user)` on an endpoint to access its authenticated user,
or on a router to protect every endpoint in that router.

## Web interface

Open `/` to sign in or register. Registration returns to the login form after
success. Management screens are shown only after successful authentication.
The frontend sends the Bearer token with every management API request.
The token is stored in `sessionStorage` for the current tab (passwords are never
stored). Refreshing the page validates the saved token with the server before
showing management. Logout clears the local session and displayed records;
expiry or a 401 response returns to login. Logout does not revoke already issued
JWTs on the server; those remain valid until their expiry time.

The interface is split into `frontend/index.html`, `frontend/styles.css` and
`frontend/app.js`. It includes responsive navigation, field validation, loading
and retry states, and confirmation before deletion. List endpoints accept an
optional `q` parameter (maximum 100 characters) to search names, codes and emails;
pagination totals reflect the search and class filter. Search is a literal,
case-insensitive substring match; it does not remove Vietnamese accents.

Run frontend logic checks with `node tests/frontend_auth.test.mjs`.
