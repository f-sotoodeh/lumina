# Lumina

## Idea

### An editor pannel for impress.js

### docs

- https://github.com/impress/impress.js/blob/master/GettingStarted.md

- https://github.com/impress/impress.js/blob/master/DOCUMENTATION.md

### example

- https://impress.js.org/#/bored

### plugins

- https://github.com/impress/impress.js/tree/master/src/plugins

### Integration with plugins

- not in this version

## Backend

### technology

- api framework

	- FastAPI

- database

	- mongodb

		- use existing mongo instance

- filestorage

	- Minio

		- bucket name: "lumina"

		- creation: automatic on app startup (make_bucket if not exists)

		- bucket structure: one bucket

		- organization: deck_id/filename (for deck files), avatars/{user_id}/original and avatars/{user_id}/thumb_64.jpg (for user avatars)

		- thumbnail prefix: thumb_

		- URL: presigned (7 days expiry)

	- system fonts

		- source: Google Fonts

		- storage: no storage needed (only URLs)

		- format: Google Fonts API URLs

		- default fonts: predefined list of Google Fonts

		- access: public via Google Fonts CDN

- deployment

	- docker & docker-compose

		- services: api, minio, frontend

		- networks: default

		- volumes: data

- environment variables

	- MONGO_URI

		- includes database name

	- MINIO_ROOT_USER

	- MINIO_ROOT_PASSWORD

	- MINIO_URL

		- format: http://minio:9000

	- JWT_SECRET

	- EMAIL_HOST

	- EMAIL_PORT

	- EMAIL_USER

	- EMAIL_PASS

	- CORS_ORIGINS

		- allowed origins (comma-separated)

	- RATE_LIMIT_ENABLED

		- enable rate limiting (default: true)

	- RATE_LIMIT_PER_HOUR

		- rate limit per hour per IP (default: 100)


- database indexes

	- text index: Deck.data.title (for full text search)

	- compound: {owner_id: 1, title: 1}

	- compound: {deck_id: 1, created_at: -1} (for Comment)

	- as mentioned in models section

### Models

- User

	- email

		- str

		- indexed

		- validation: regex validation

		- unique: true

		- change: not allowed (only admin can change)

	- name

		- str | null

	- password_hash

		- str | null

		- hashing: argon2 or bcrypt

		- validation: min 8 chars, uppercase/lowercase/number required

	- otp

		- str | null

		- used for: reset password

		- expiry: 15 minutes

		- generation: 6 digits numeric

		- method: random with secrets.randbelow(900000) + 100000

	- otp_expiry

		- datetime | null

	- is_admin

		- bool (default: False)

		- indexed

	- created_at

		- datetime

		- indexed

	- last_logged_in_at

		- datetime

		- indexed

	- avatar_url

		- str | null

		- presigned URL (7 days expiry)

		- stored in Minio: avatars/{user_id}/original and avatars/{user_id}/thumb_64.jpg

		- thumbnail: 64x64 JPG (auto-generated)

		- always returns thumbnail presigned URL

- Deck

	- data

		- title

			- str

			- indexed

				- text (full text search)

			- validation: max 100 chars

		- order

			- list[ObjectId]

			- step order in deck

			- no minimum steps required

			- step deletion allowed even if last step

		- is_public

			- bool (default: False)

			- indexed

		- preview_url

			- str

			- UUID v4 format

			- stored in MongoDB as string (not ObjectId)

			- generated on deck creation

	- settings

		- background_color

			- str

			- format: hex (#RRGGBB)

			- all settings optional with defaults

		- all settings created with default values on deck creation (e.g., data_width=1024)

		- only title required

		- data_transition_duration

			- int

		- data_width

			- int (default: 1024)

		- data_height

			- int (default: 768)

		- data_max_scale

			- int | null

		- data_min_scale

			- int | null

		- data_perspective

			- int (default: 1000)

		- data_autoplay

			- int | null

	- overview

		- has_overview

			- bool (default: True)

		- overview_x

			- float (default: 0.0)

		- overview_y

			- float (default: 0.0)

		- overview_z

			- float (default: 0.0)

		- overview_scale

			- float (default: 1.0)

	- meta

		- owner_id

			- ObjectId

			- indexed

		- thumbnail_url

			- str | null

			- auto-generated: 200x200 JPG

			- generation: after first save with at least one step

			- update: automatically every time step is added/removed/reordered (debounce 2s)

		- created_at

			- datetime

			- indexed

		- updated_at

			- datetime

			- indexed

- Share

	- deck_id

		- ObjectId

		- indexed

	- owner_id

		- ObjectId

		- indexed

	- share_with

		- ObjectId

		- indexed

	- shared_at

		- datetime

		- indexed

	- access_level

		- enum ['Editor', 'Commenter', 'Viewer']

		- indexed

	- business rules

		- no self-share allowed

		- owner cannot change their own access level

		- multiple users can be shared simultaneously (one-to-many)

- Step

	- position

		- data_x

			- float (default: 0.0)

		- data_y

			- float (default: 0.0)

		- data_z

			- float (default: 0.0)

		- data_rotate

			- float (default: 0.0)

		- data_rotate_x

			- float (default: 0.0)

		- data_rotate_y

			- float (default: 0.0)

		- data_rotate_z

			- float (default: 0.0)

		- data_scale

			- float (default: 1.0)

	- settings

		- data_transition_duration

			- int (default: 1000)

		- data_autoplay

			- int | null

		- is_slide

			- bool (default: True)

	- data

		- inner_html

			- str

		- notes

			- str

		- font_family

			- str | null

			- Google Fonts URL or font-family name

			- applied to step content

			- stored as Google Fonts URL or CSS font-family

	- meta

		- user_id

			- ObjectId

			- indexed

		- deck_id

			- ObjectId

			- indexed

		- from path parameter in API

		- step appended to end of deck.order on creation

		- manual ordering from creation moment

- Comment

	- user_id

		- ObjectId

		- indexed

	- deck_id

		- ObjectId

		- indexed

	- step_id

		- ObjectId

		- indexed

	- text

		- str

		- validation: max 1000 characters

		- format: plain text only (HTML escaped)

	- is_edited

		- bool (default: False)

	- created_at

		- datetime

		- indexed

	- updated_at

		- datetime

	- permissions

		- edit/delete: Commenter can edit/delete own comments

		- Editor can delete others' comments

- file

	- user_id

		- ObjectId

		- indexed

	- deck_id

		- ObjectId

		- indexed

	- created_at

		- datetime

		- indexed

	- size

		- int

		- indexed

	- type

		- str

		- indexed

	- original_name

		- str

		- stored in DB

	- minio_id

		- str

		- filename in Minio: UUIDv4 + original extension (e.g., a1b2c3d4-....jpg)

		- collision: impossible (UUID)

	- url

		- str

		- presigned URL (7 days expiry)

		- always presigned

		- new URLs generated on get file list

	- file handling

		- thumbnail generation: Pillow library

		- thumbnail for: JPEG, PNG, GIF (SVG rasterized)

		- thumbnail size: 200x200 JPG

		- thumbnail prefix: thumb_

		- deletion: cascade from Minio (file and thumbnail deleted)

### API Configuration

- base URL

	- /api/v1/

	- response format

	- {success: bool, data: {}, message: {lang: str}, errors: []}

	- message languages: 'en', 'ru', 'hy'

	- error response structure

		- {success: false, message: {en: "Validation error", ...}, errors: [{field: "email", message: {en: "Invalid email format", ...}}, ...]}

		- field-level errors with multilingual messages

- pagination

	- query params: limit/offset or page/pagesize

	- default: limit=20, offset=0

	- response format: {data: [], total: int, page: int, pages: int}

- authentication

	- JWT token

		- payload: {sub: user_id, exp, iat, role}

		- role: "user" or "admin"

		- expiration: 15 minutes

		- refresh token: 7 days

		- storage: two separate httpOnly cookies

			- access_token (httpOnly, 15 minutes)

			- refresh_token (httpOnly, 7 days)

	- refresh endpoint

		- /api/v1/auth/refresh

		- refresh token in httpOnly cookie

	- middleware

		- permission checking middleware required

- password reset flow

	- email OTP -> verify -> new password

	- OTP expiry: 15 minutes

	- OTP generation: 6 digits numeric, random with secrets.randbelow(900000) + 100000

	- email template: "Your OTP: {otp} expires in {minutes}"

	- after reset: requires login again

	- previous tokens: invalidated

- email service

	- SMTP (Gmail) or SendGrid

	- env vars: EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS

- error handling

	- HTTP codes: standard (400, 401, 403, 404, 500)

	- no custom error codes

	- errors: English only (multilingual support in message field)

- CORS

	- enabled

	- allowed origins: from CORS_ORIGINS env variable

### endpoints

- admin

	- get all users

		- path: /api/v1/admin/users

		- params

			- pagination: limit/offset or page/pagesize

		- headers

			- JWT (admin check)

		- method

			- GET

	- get all decks

		- path: /api/v1/admin/decks

		- params

			- user_id

			- pagination: limit/offset or page/pagesize

		- headers

			- JWT (admin check)

		- method

			- GET

	- get decks count

		- path: /api/v1/admin/decks/count

		- headers

			- JWT (admin check)

		- method

			- GET

		- desc

			- {user_id: count}

- auth

	- register

		- path: /api/v1/auth/register

		- method

			- POST

		- request

			- {email: str required, password: str required, name: str optional}

	- login

		- path: /api/v1/auth/login

		- method

			- POST

		- request

			- {email: str, password: str}

	- forgot password

		- path: /api/v1/auth/forgot-password

		- method

			- POST

		- request

			- {email: str}

	- reset password

		- path: /api/v1/auth/reset-password

		- method

			- POST

		- request

			- {email: str, otp: str, new_password: str}

	- refresh token

		- path: /api/v1/auth/refresh

		- method

			- POST

		- headers

			- refresh token in httpOnly cookie

- user

	- edit profile

		- path: /api/v1/users/me

		- headers

			- JWT

		- method

			- PUT

		- request

			- {name: str optional, email: str optional}

		- desc

			- updates user profile information

	- upload avatar

		- path: /api/v1/users/me/avatar

		- headers

			- JWT

			- Content-Type: multipart/form-data

		- method

			- POST

		- request

			- file: File (multipart, image)

		- limits

			- max size: 5MB

			- allowed types: jpeg, png, gif

		- desc

			- uploads user avatar

			- thumbnail auto-generated: 64x64 JPG

			- stored in Minio: avatars/{user_id}/original and avatars/{user_id}/thumb_64.jpg

			- returns presigned URL for thumbnail (7 days expiry)

			- if avatar exists, replaces old one (cascade delete)

	- delete avatar

		- path: /api/v1/users/me/avatar

		- headers

			- JWT

		- method

			- DELETE

		- desc

			- deletes user avatar

			- removes from Minio (file and thumbnail)

			- sets avatar_url to null

- deck

	- get all

		- path: /api/v1/decks

		- params

			- mine (bool)

			- shared_with_me (bool)

			- pagination: limit/offset or page/pagesize

		- headers

			- JWT

		- method

			- GET

	- get deck by id

		- path: /api/v1/decks/{id}

		- headers

			- JWT

		- method

			- GET

	- search by title

		- path: /api/v1/decks/search

		- params

			- q (query string)

			- example: ?q=title&user_id=123

		- headers

			- JWT (optional for public decks)

		- method

			- GET

		- desc

			- search in title only

			- public decks visible without JWT

	- get decks by owner name

		- path: /api/v1/decks

		- params

			- owner_name (query string)

			- pagination: limit/offset or page/pagesize

		- headers

			- JWT

		- method

			- GET

		- desc

			- filter decks by owner name

	- share a deck

		- path: /api/v1/decks/{id}/share

		- headers

			- JWT

		- method

			- POST

		- request

			- {user_id: str, access_level: "Editor" | "Commenter" | "Viewer"}

		- desc

			- owner is separate from shared_with

			- Editor can create/edit/delete steps

			- Commenter can add comments

			- Viewer can only view

			- no self-share allowed

	- revoke sharing

		- path: /api/v1/decks/{id}/share

		- params

			- user_id

				- to revoke sharing a deck of mine with somebody

			- deck_id

				- to revoke sharing a somebody's deck with me

		- headers

			- JWT

		- method

			- DELETE

	- create a deck

		- path: /api/v1/decks

		- headers

			- JWT

		- method

			- POST

		- request

			- {title: str required}, others default

		- desc

			- no minimum steps required

			- preview_url (UUID v4) generated on creation

			- all settings created with default values (e.g., data_width=1024)

			- only title required

	- edit a deck

		- path: /api/v1/decks/{id}

		- headers

			- JWT

		- method

			- PUT

		- request

			- partial update (all fields optional)

	- delete a deck

		- path: /api/v1/decks/{id}

		- headers

			- JWT

		- method

			- DELETE

		- desc

			- cascade delete: steps, comments, files

	- preview a deck

		- path: /api/v1/decks/{id}/preview

		- params

			- uuid (preview URL)

		- headers

			- JWT (optional for public decks)

		- method

			- GET

		- response

			- JSON data for impress.js

	- export deck

		- path: /api/v1/decks/{id}/export

		- headers

			- JWT

		- method

			- GET

		- desc

			- export to HTML

			- includes impress.js inline

			- inline CSS/JS, bundle assets

			- images: base64 inline (up to 100KB), larger → relative path + copy to /assets

			- fonts: Google Fonts links in HTML head

			- font URLs from step.data.font_family added as <link> tags

			- font-family from step.data.font_family applied to step content via CSS

			- works online (requires Google Fonts CDN access)

	- public preview

		- path: /api/v1/preview/{uuid}

		- headers

			- no JWT required

		- method

			- GET

		- response

			- JSON data for impress.js

		- desc

			- frontend route: /preview/:uuid

			- backend sends JSON data

			- needs impress.js in frontend

			- rate limiting: 100 requests per hour per IP (with slowapi)

- step

	- get all steps of a deck

		- path: /api/v1/decks/{deck_id}/steps

		- params

			- pagination: limit/offset or page/pagesize

		- headers

			- JWT

		- method

			- GET

	- create a new step

		- path: /api/v1/decks/{deck_id}/steps

		- headers

			- JWT

		- method

			- POST

		- request

			- all fields optional with defaults (deck_id from path)

		- desc

			- step appended to end of deck.order

			- manual ordering from creation moment

			- all position/settings fields optional with defaults

	- reorder

		- path: /api/v1/decks/{deck_id}/steps/reorder

		- headers

			- JWT

		- method

			- PATCH

		- request

			- {step_ids: list[str] (ordered list)}

		- desc

			- called by drag & drop UI

	- edit step setting

		- path: /api/v1/steps/{id}/settings

		- headers

			- JWT

		- method

			- PUT

		- request

			- partial update (position, settings fields)

	- edit step data

		- path: /api/v1/steps/{id}/data

		- headers

			- JWT

		- method

			- PUT

		- request

			- {inner_html: str, notes: str, font_family: str optional}

	- delete step

		- path: /api/v1/steps/{id}

		- headers

			- JWT

		- method

			- DELETE

		- desc

			- removes step from deck.order list (cascade)

			- allowed even if last step in deck

- comment

	- get comments count

		- path: /api/v1/comments/count

		- params

			- deck_id (for deck comments)

			- step_id (for step comments)

		- headers

			- JWT

		- method

			- GET

	- get all comments of a step

		- path: /api/v1/steps/{step_id}/comments

		- params

			- pagination: limit/offset or page/pagesize

		- headers

			- JWT

		- method

			- GET

	- add a comment on a step

		- path: /api/v1/steps/{step_id}/comments

		- headers

			- JWT

		- method

			- POST

		- request

			- {text: str}

		- validation

			- max length: 1000 characters

			- format: plain text only (HTML escaped)

	- edit a comment

		- path: /api/v1/comments/{id}

		- headers

			- JWT

		- method

			- PUT

		- request

			- {text: str}

		- desc

			- Commenter can edit own comments

	- remove a comment

		- path: /api/v1/comments/{id}

		- headers

			- JWT

		- method

			- DELETE

		- desc

			- Commenter can delete own comments

			- Editor can delete others' comments

- file

	- get files list (by deck_id)

		- path: /api/v1/decks/{deck_id}/files

		- params

			- thumbnail (bool)

			- pagination: limit/offset or page/pagesize

		- headers

			- JWT

		- method

			- GET

		- desc

			- new presigned URLs generated on each request

	- get storage status

		- path: /api/v1/files/storage

		- headers

			- JWT

		- method

			- GET

		- response

			- {file_count: int, used_storage: int (bytes)}

	- get file (by file_id)

		- path: /api/v1/files/{id}

		- params

			- thumbnail (bool) - returns thumbnail if true

			- full (bool) - returns full file if true

		- headers

			- JWT

		- method

			- GET

		- response

			- presigned URL or file stream

	- upload file

		- path: /api/v1/files/upload

		- headers

			- JWT

			- Content-Type: multipart/form-data

		- method

			- POST

		- request

			- files: File[] (multipart, multiple files)

			- deck_id: form data (required)

		- limits

			- max size: 5MB per file

			- allowed types: jpeg, png, svg, gif

			- validation: type image (jpeg/png/svg/gif), size max 5MB

		- desc

			- thumbnail auto-generated with Pillow

			- JPEG/PNG/GIF: thumbnail created

			- SVG: rasterized then thumbnail created

			- filename in Minio: UUIDv4 + original extension (e.g., a1b2c3d4-....jpg)

			- original_name stored in DB

			- collision: impossible (UUID)

			- multiple files supported in one request

	- remove file

		- path: /api/v1/files/{id}

		- headers

			- JWT

		- method

			- DELETE

		- desc

			- cascade delete from Minio (file and thumbnail)

- fonts

	- get system fonts list

		- path: /api/v1/fonts

		- headers

			- no JWT required (public)

		- method

			- GET

		- response

			- {fonts: [{name: str, url: str, family: str}, ...]}

		- desc

			- returns list of available Google Fonts

			- includes font name, Google Fonts URL, and CSS font-family name

			- fonts from Google Fonts CDN (no storage needed)

			- predefined list of Google Fonts

## Frontend

### pages

- landing page

	- navbar

	- hero section

	- CTA

	- features

	- testimonials

	- footer

- sign in / sign up / forgot password

- decks list

	- filter by user (for admin)

- deck editor

	- auto-save enabled (5s debounce)

	- drag & drop reordering

- deck preview

	- public preview: /preview/:uuid

- profile

	- edit profile information

	- upload/change/delete avatar

	- avatar display

- users list (for admin)

### components

- TopBar

	- DeckTitleEditor

	- ShareButton

	- UserMenu

		- displays user avatar

		- avatar fallback if not set

- LeftPanel

	- VerticalIconTabs

- MainCanvas

- BottomTimeline

- RightInspector

- AuthGuard

- ErrorHandler

- PreviewModal

- DragDropHandler

- FileUploader

- AvatarUploader

	- upload avatar

	- change avatar

	- delete avatar

	- avatar preview

	- progress bar

- ElementEditor

	- text editor: Quill

	- images: upload

	- shapes: SVG

	- font selector

		- dropdown with Google Fonts

		- font preview

		- applies Google Fonts URL or font-family to step content

		- loads fonts from Google Fonts CDN

- SlideThumbnail

- ShareModal

- AutoSave

	- debounce: 5 seconds

	- saves deck changes automatically

### technology

- js framework

	- svelte

		- routing: SvelteKit

- css library

	- daisy ui

- presentation framework

	- impress.js

### Best Practices

- State management

	- Svelte stores/context

		- deckStore (current deck)

		- userStore (auth state)

		- slidesStore (steps)

- API calls

	- fetch wrapper with auth

		- automatic JWT handling

		- error handling

	- API base URL

		- environment variable: VITE_API_URL

		- different for dev/prod

- Real-time updates

	- not in this version

- Error handling

	- toast notifications

- Auto-save

	- saves all changes (deck settings and steps)

	- loading indicator shown during save

- File upload

	- progress bar

	- multiple file upload supported

