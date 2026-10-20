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

- `POST /register`: returns 201 with `id`, `username` and `role: "user"`;
  duplicates return 409. A submitted `role` cannot grant admin access.
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

## Roles and administrative permissions

Apply the role migration before starting the updated application:
`uv run alembic upgrade head`.
The `users.role` column accepts only `admin` or `user`, is required, and defaults
to `user` for both existing accounts and newly registered accounts.

Only an admin can call the following endpoints:

- `POST /api/v1/students/`, `PUT /api/v1/students/{id}`,
  `DELETE /api/v1/students/{id}`.
- `POST /api/v1/classes/`, `PUT /api/v1/classes/{id}`,
  `DELETE /api/v1/classes/{id}`.
- `POST /api/v1/teachers/`, `PUT /api/v1/teachers/{id}`,
  `DELETE /api/v1/teachers/{id}`.
- `GET /demo/fixed-n-plus-1` (returns the complete student roster).

Authorization behavior:

- Missing or invalid authentication returns 401.
- An authenticated regular user receives 403 with `detail: "Admin role required"`,
  including when the target ID does not exist. No record is created, changed or deleted.
- Authorized requests retain normal validation and response codes: creation returns
  201, successful deletion returns 204, and missing update/delete targets return 404.

Roles are read from the database on every request; changing a role takes effect
with an already issued token. JWT role claims are not used for authorization.
Both roles can read list/detail endpoints for students, classes and teachers.
These reads are not scoped to a user's own profile or class: accounts currently
have no relationship to student records. Such restrictions require an additional
data model and business policy. Registration and login remain public; registration
always assigns `user`. The frontend displays a 403 error while keeping the
signed-in session; management action buttons remain visible to both roles.

To grant the first admin, register an account and run the following parameterized
statement through a trusted database administration tool, binding `username` to
that account's exact username, then commit:

```sql
UPDATE users SET role = 'admin' WHERE username = :username;
```

Verify that exactly one account was updated. Use `role = 'user'` to revoke admin
access. There is no public endpoint for changing roles.

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
