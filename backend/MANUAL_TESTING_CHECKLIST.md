# Manual Testing Checklist for Lumina Backend

## ✅ Automated Tests Completed

The following tests have been automatically verified:

### Code Structure (107 tests passed)
- ✅ All Python files have valid syntax (36 files)
- ✅ All critical files exist (34 files)
- ✅ All models have indexes defined (6 models)
- ✅ All schemas contain BaseModel (5 schemas)
- ✅ All utility functions exist (14 functions)
- ✅ All core modules exist and have required functions (4 modules)
- ✅ Main application configured correctly (6 checks)
- ✅ Router includes all endpoints (10 routers)
- ✅ Data files exist and not empty (2 files)
- ✅ Total endpoints found: 47 endpoints
  - GET: 20 endpoints
  - POST: 14 endpoints
  - PUT: 6 endpoints
  - DELETE: 6 endpoints
  - PATCH: 1 endpoint

---

## 🔧 Manual Testing Required

These tests require a running server with MongoDB and MinIO:

### 1. Environment Setup & Server Start

#### 1.1 Environment Variables
- [ ] Create `.env` file in `backend/` directory
- [ ] Set all required environment variables (see checklist above)
- [ ] Verify MongoDB connection string is correct
- [ ] Verify MinIO credentials are correct
- [ ] Verify Gmail SMTP credentials (for email testing)

#### 1.2 Dependencies Installation
- [ ] Run `pip install -r requirements.txt`
- [ ] Verify all packages install without errors
- [ ] Check Python version is 3.9+

#### 1.3 Database & Storage Setup
- [ ] MongoDB is running and accessible
- [ ] MinIO is running and accessible
- [ ] Can connect to MongoDB with provided URI
- [ ] Can connect to MinIO with provided credentials

#### 1.4 Server Startup
- [ ] Run `uvicorn app.main:app --reload`
- [ ] Server starts without errors
- [ ] See "✓ MongoDB initialized" in logs
- [ ] See "✓ MinIO bucket initialized" in logs
- [ ] No import errors
- [ ] No syntax errors

#### 1.5 Health Check
- [ ] `GET /health` returns `{"status": "healthy"}`
- [ ] `GET /` returns API info
- [ ] `GET /api/v1/redoc` opens ReDoc documentation

---

### 2. Authentication Flow (Requires Server)

#### 2.1 Registration
- [ ] `POST /api/v1/auth/register` with valid data
  - [ ] Returns success response
  - [ ] Sets `access_token` and `refresh_token` cookies (httpOnly)
  - [ ] User created in database
  - [ ] Password is hashed (not plain text)
- [ ] `POST /api/v1/auth/register` with duplicate email
  - [ ] Returns 400 error
  - [ ] Error message is in correct format
- [ ] `POST /api/v1/auth/register` with invalid email
  - [ ] Returns 400 error
  - [ ] Validation error message shown
- [ ] `POST /api/v1/auth/register` with weak password
  - [ ] Returns 400 error
  - [ ] Password validation message shown

#### 2.2 Login
- [ ] `POST /api/v1/auth/login` with correct credentials
  - [ ] Returns success response
  - [ ] Sets cookies
  - [ ] `last_logged_in_at` updated in database
- [ ] `POST /api/v1/auth/login` with wrong password
  - [ ] Returns 401 error
- [ ] `POST /api/v1/auth/login` with non-existent email
  - [ ] Returns 401 error

#### 2.3 Token Refresh
- [ ] `POST /api/v1/auth/refresh` with valid refresh_token cookie
  - [ ] Returns new access_token
- [ ] `POST /api/v1/auth/refresh` with expired refresh_token
  - [ ] Returns 401 error
- [ ] `POST /api/v1/auth/refresh` without cookie
  - [ ] Returns 401 error

#### 2.4 Logout
- [ ] `POST /api/v1/auth/logout` clears cookies
  - [ ] Cookies are cleared/expired
  - [ ] Subsequent requests require login

#### 2.5 Password Reset Flow
- [ ] `POST /api/v1/auth/forgot-password` with valid email
  - [ ] Returns success (even if email doesn't exist - security)
  - [ ] OTP email sent (check Gmail inbox)
  - [ ] OTP stored in database with 15 min expiry
- [ ] `POST /api/v1/auth/reset-password` with correct OTP
  - [ ] Password updated
  - [ ] OTP invalidated
  - [ ] User must login again
- [ ] `POST /api/v1/auth/reset-password` with wrong OTP
  - [ ] Returns 400 error
- [ ] `POST /api/v1/auth/reset-password` with expired OTP
  - [ ] Returns 400 error

---

### 3. User Endpoints (Requires Authentication)

#### 3.1 Profile Management
- [ ] `GET /api/v1/users/me` without JWT
  - [ ] Returns 401 error
- [ ] `GET /api/v1/users/me` with valid JWT
  - [ ] Returns user data
  - [ ] Response includes: id, email, first_name, last_name, avatar_url, is_admin
- [ ] `PUT /api/v1/users/me` update first_name/last_name
  - [ ] Profile updated successfully
  - [ ] Changes reflected in database

#### 3.2 Avatar Management
- [ ] `POST /api/v1/users/me/avatar` upload image
  - [ ] Valid image (< 5MB) uploads successfully
  - [ ] Original stored in MinIO: `avatars/{user_id}/original`
  - [ ] Thumbnail 64x64 created: `avatars/{user_id}/thumb_64.jpg`
  - [ ] Presigned URL returned (7 days expiry)
  - [ ] `avatar_url` updated in database
- [ ] `POST /api/v1/users/me/avatar` with invalid file type
  - [ ] Returns 400 error
- [ ] `POST /api/v1/users/me/avatar` with file > 5MB
  - [ ] Returns 413 error
- [ ] `GET /api/v1/users/me/avatar/fallback` when no avatar
  - [ ] Returns SVG with initials
  - [ ] Background color is consistent (based on email hash)
  - [ ] Uses first_name and last_name initials
- [ ] `DELETE /api/v1/users/me/avatar`
  - [ ] Avatar deleted from MinIO (original + thumbnail)
  - [ ] `avatar_url` set to null in database

---

### 4. Deck Endpoints (Requires Authentication)

#### 4.1 Deck CRUD
- [ ] `POST /api/v1/decks` create deck
  - [ ] Only title required
  - [ ] Default values set correctly
  - [ ] `preview_url` is UUID v4 format
  - [ ] Returns deck ID and preview_url
- [ ] `GET /api/v1/decks` get all decks
  - [ ] Returns user's decks by default
  - [ ] `?mine=true` filters correctly
  - [ ] `?shared_with_me=true` shows shared decks
  - [ ] `?owner_name=John` filters by owner name
  - [ ] Pagination works (limit/offset)
  - [ ] Response includes: total, page, pages
- [ ] `GET /api/v1/decks/{deck_id}` get deck
  - [ ] Returns full deck data
  - [ ] Access control works (owner or shared)
  - [ ] 404 for non-existent deck
  - [ ] 403 for unauthorized access
- [ ] `PUT /api/v1/decks/{deck_id}` update deck
  - [ ] Partial update works (only provided fields updated)
  - [ ] Validation works:
    - [ ] `background_color` - hex format (#RRGGBB) - 400 if invalid
    - [ ] `data_width` - 500-4000 range - 400 if out of range
    - [ ] `data_height` - 500-4000 range - 400 if out of range
    - [ ] `data_perspective` - 100-5000 range - 400 if out of range
  - [ ] Only owner can update
- [ ] `DELETE /api/v1/decks/{deck_id}` delete deck
  - [ ] Deck deleted from database
  - [ ] Steps cascade deleted
  - [ ] Comments cascade deleted
  - [ ] Files cascade deleted from MinIO
  - [ ] Only owner can delete

#### 4.2 Deck Search
- [ ] `GET /api/v1/decks/search?q=test` without JWT
  - [ ] Only public decks returned
  - [ ] Returns 200 (not 401)
- [ ] `GET /api/v1/decks/search?q=test` with JWT
  - [ ] Returns: user's decks + public decks + shared decks
  - [ ] Sort by relevance works
  - [ ] `?sort=title_asc` works
  - [ ] `?sort=title_desc` works
  - [ ] `?sort=created_desc` works
  - [ ] `?sort=updated_desc` works

#### 4.3 Deck Cloning
- [ ] `POST /api/v1/decks/{deck_id}/clone` clone deck
  - [ ] Complete copy created
  - [ ] All steps copied
  - [ ] All files copied (new MinIO objects)
  - [ ] New preview_url generated
  - [ ] New owner is requesting user
  - [ ] New thumbnail generated

#### 4.4 Deck Export
- [ ] `GET /api/v1/decks/{deck_id}/export` export to HTML
  - [ ] Returns HTML file
  - [ ] impress.js is inline (not CDN)
  - [ ] Images < 100KB are base64 inline
  - [ ] Images > 100KB have comment for /assets folder
  - [ ] Font links included in <head>
  - [ ] Font-family applied to steps
  - [ ] File downloads with correct filename

#### 4.5 Deck Preview
- [ ] `GET /api/v1/decks/{deck_id}/preview` without JWT
  - [ ] Public deck - returns JSON data
  - [ ] Private deck - returns 403
- [ ] `GET /api/v1/decks/{deck_id}/preview` with JWT
  - [ ] Returns JSON for impress.js
  - [ ] Includes deck settings
  - [ ] Includes steps in correct order
- [ ] `GET /api/v1/preview/{uuid}` public preview
  - [ ] Rate limiting works (100/hour per IP)
  - [ ] Only public decks accessible
  - [ ] Returns JSON data

#### 4.6 Deck Thumbnail
- [ ] Thumbnail auto-generation:
  - [ ] After first step added - thumbnail created
  - [ ] After step added/removed/reordered - regenerated (2s debounce)
  - [ ] After step data updated - regenerated (2s debounce)
  - [ ] Thumbnail stored in MinIO: `decks/{deck_id}/thumbnail.jpg`
  - [ ] Presigned URL stored in database
- [ ] `GET /api/v1/decks/{deck_id}/thumbnail/fallback`
  - [ ] Returns SVG
  - [ ] Uses deck background_color
  - [ ] Shows deck title

---

### 5. Step Endpoints (Requires Authentication)

#### 5.1 Step CRUD
- [ ] `GET /api/v1/steps/decks/{deck_id}` get all steps
  - [ ] Sorted by deck.order
  - [ ] Pagination works
  - [ ] Access control works (Viewer or higher)
- [ ] `POST /api/v1/steps/decks/{deck_id}` create step
  - [ ] Step appended to end of deck.order
  - [ ] HTML sanitization works (XSS protection)
  - [ ] Position clamping works (-50000 to 50000)
  - [ ] NaN values converted to 0.0
  - [ ] Access control works (Editor required)
- [ ] `PATCH /api/v1/steps/decks/{deck_id}/reorder` reorder
  - [ ] Validation: all step_ids must exist
  - [ ] Validation: no duplicates
  - [ ] Validation: no missing steps
  - [ ] Order updated correctly
  - [ ] Thumbnail regenerated (2s debounce)
- [ ] `PUT /api/v1/steps/{step_id}/settings` update position
  - [ ] Position clamping works
  - [ ] All position fields update correctly
- [ ] `PUT /api/v1/steps/{step_id}/data` update content
  - [ ] HTML sanitization works
  - [ ] Notes updated
  - [ ] Font family updated
  - [ ] Thumbnail regenerated (2s debounce)
- [ ] `DELETE /api/v1/steps/{step_id}` delete step
  - [ ] Removed from deck.order
  - [ ] Step deleted from database
  - [ ] If last step - thumbnail cleared
  - [ ] If steps remain - thumbnail regenerated
- [ ] `POST /api/v1/steps/{step_id}/duplicate` duplicate
  - [ ] Complete copy created
  - [ ] Appended to end of deck.order

---

### 6. Comment Endpoints (Requires Authentication)

#### 6.1 Comment Management
- [ ] `GET /api/v1/comments/count?deck_id=xxx` count
  - [ ] Returns correct count
- [ ] `GET /api/v1/comments/count?step_id=xxx` count
  - [ ] Returns correct count
- [ ] `GET /api/v1/comments/step/{step_id}` get comments
  - [ ] Sorted by created_at desc
  - [ ] Pagination works
  - [ ] Access control works (Viewer or higher)
- [ ] `POST /api/v1/comments/step/{step_id}` create comment
  - [ ] Access control works (Commenter or Editor)
  - [ ] Text validation: max 1000 chars
  - [ ] HTML escaping works
  - [ ] Comment saved to database
- [ ] `PUT /api/v1/comments/{comment_id}` update
  - [ ] Only owner can edit
  - [ ] `is_edited` flag set
  - [ ] `updated_at` updated
- [ ] `DELETE /api/v1/comments/{comment_id}` delete
  - [ ] Owner can delete own comment
  - [ ] Editor can delete others' comments
  - [ ] Viewer cannot delete

---

### 7. File Endpoints (Requires Authentication)

#### 7.1 File Management
- [ ] `GET /api/v1/decks/{deck_id}/files` get files
  - [ ] Presigned URLs regenerated on each request
  - [ ] Thumbnail URLs included
  - [ ] Pagination works
  - [ ] Access control works (Viewer or higher)
- [ ] `GET /api/v1/files/quota` get quota
  - [ ] Returns used/limit in MB
  - [ ] Calculation is correct
- [ ] `GET /api/v1/files/{file_id}` get file
  - [ ] Presigned URL returned
  - [ ] Access control works
- [ ] `POST /api/v1/files/upload?deck_id=xxx` upload
  - [ ] Multiple files supported
  - [ ] File type validation (only images)
  - [ ] File size validation (max 5MB)
  - [ ] Quota check (max 100MB per user)
  - [ ] Thumbnail generation for images
  - [ ] SVG rasterization works
  - [ ] Files stored in MinIO
  - [ ] Database records created
- [ ] `DELETE /api/v1/files/{file_id}` delete
  - [ ] Only owner can delete
  - [ ] Cascade delete from MinIO (file + thumbnail)

---

### 8. Share Endpoints (Requires Authentication)

#### 8.1 Sharing
- [ ] `POST /api/v1/decks/{deck_id}/share` share deck
  - [ ] Only owner can share
  - [ ] No self-share (400 error)
  - [ ] Invalid user_id (404 error)
  - [ ] Already shared - updates access level
  - [ ] Success - share created
- [ ] `GET /api/v1/decks/{deck_id}/shares` get shares
  - [ ] Only owner can view
  - [ ] Returns list of shares
- [ ] `DELETE /api/v1/decks/{deck_id}/share?user_id=xxx` revoke
  - [ ] Only owner can revoke
  - [ ] Share deleted

#### 8.2 Access Control Testing
- [ ] Viewer access:
  - [ ] Can view deck
  - [ ] Cannot create/edit/delete steps (403)
  - [ ] Cannot add comments (403)
- [ ] Commenter access:
  - [ ] Can view deck
  - [ ] Can add comments
  - [ ] Cannot create/edit/delete steps (403)
- [ ] Editor access:
  - [ ] Can view deck
  - [ ] Can create/edit/delete steps
  - [ ] Can add comments
  - [ ] Can delete others' comments

---

### 9. Admin Endpoints (Requires Admin Role)

#### 9.1 Admin Functions
- [ ] `GET /api/v1/admin/users` get all users
  - [ ] Only admin (403 for non-admin)
  - [ ] Pagination works
- [ ] `PUT /api/v1/admin/users/{user_id}/email` change email
  - [ ] Only admin
  - [ ] Email validation
  - [ ] Duplicate check
- [ ] `GET /api/v1/admin/decks` get all decks
  - [ ] Filter by user_id works
  - [ ] Pagination works
- [ ] `GET /api/v1/admin/decks/count` get count
  - [ ] Returns count per user

---

### 10. Fonts Endpoint

- [ ] `GET /api/v1/fonts` get fonts
  - [ ] Public endpoint (no JWT required)
  - [ ] Returns list of Google Fonts
  - [ ] Format: `{name, url, family}`
  - [ ] At least 20 fonts returned

---

### 11. Security Testing

#### 11.1 Authentication
- [ ] Invalid JWT - 401 error
- [ ] Expired JWT - 401 error
- [ ] Missing JWT - 401 error
- [ ] JWT with invalid signature - 401 error

#### 11.2 Authorization
- [ ] Non-owner access - 403 error
- [ ] Insufficient access level - 403 error
- [ ] Admin-only endpoints - 403 for non-admin

#### 11.3 Input Validation
- [ ] XSS protection - HTML sanitization works
- [ ] File upload - type validation
- [ ] File upload - size validation
- [ ] Path traversal - validation works

#### 11.4 Rate Limiting
- [ ] Public preview endpoint - 100/hour per IP
- [ ] Rate limit exceeded - 429 error

---

### 12. Error Handling

#### 12.1 Error Responses
- [ ] 400 - Bad Request - validation errors
- [ ] 401 - Unauthorized - authentication errors
- [ ] 403 - Forbidden - authorization errors
- [ ] 404 - Not Found - resource not found
- [ ] 413 - Payload Too Large - file size/quota
- [ ] 429 - Too Many Requests - rate limit
- [ ] 500 - Internal Server Error - global handler

#### 12.2 Error Format
- [ ] Error responses have correct format:
  ```json
  {
    "success": false,
    "message": {"en": "...", "ru": "...", "hy": "..."},
    "errors": [{"field": "...", "message": {...}}]
  }
  ```

---

### 13. i18n Testing

- [ ] `Accept-Language: en` - English messages
- [ ] `Accept-Language: ru` - Russian messages
- [ ] `Accept-Language: hy` - Armenian messages
- [ ] Default - English if no language header

---

### 14. Database Indexes (After First Use)

Run these MongoDB commands to verify indexes:

```javascript
// Connect to MongoDB
use lumina

// Check User indexes
db.users.getIndexes()
// Should have: email (unique), is_admin, created_at, last_logged_in_at

// Check Deck indexes
db.decks.getIndexes()
// Should have: title (text), is_public, owner_id, created_at, updated_at, compound (owner_id, title)

// Check Step indexes
db.steps.getIndexes()
// Should have: user_id, deck_id

// Check Comment indexes
db.comments.getIndexes()
// Should have: user_id, deck_id, step_id, created_at, compound (deck_id, created_at)

// Check File indexes
db.files.getIndexes()
// Should have: user_id, deck_id, created_at, size

// Check Share indexes
db.shares.getIndexes()
// Should have: deck_id, owner_id, share_with, shared_at, access_level
```

---

### 15. Integration Testing

#### 15.1 Complete Flows
- [ ] User registration → Login → Create deck → Add steps → Share → Comment → Export
- [ ] Password reset flow - end to end (check email)
- [ ] Deck cloning - all data copied correctly
- [ ] File upload → Thumbnail → Delete

---

## 📝 Notes

- Use Postman or similar tool for easier cookie handling
- Check MongoDB and MinIO logs for any errors
- Monitor server logs for exceptions
- Test with multiple users to verify sharing works
- Test rate limiting by making many requests quickly

---

## ✅ Summary

**Automated Tests:** 107 passed, 0 failed

**Manual Tests Required:** ~150+ test cases

**Estimated Time:** 2-4 hours for comprehensive testing

**Priority Tests:**
1. Server startup and health check
2. Authentication flow (register, login, refresh)
3. Basic CRUD operations (decks, steps)
4. File upload and quota
5. Sharing and access control
6. Error handling

