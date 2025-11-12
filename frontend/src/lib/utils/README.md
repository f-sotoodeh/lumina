# API Utilities

Core utilities for API communication and error handling.

## Usage

### Basic API Calls

```typescript
import { get, post, put, del } from '$lib/utils';

// GET request
const decks = await get<DeckListData>('/decks?mine=true');

// POST request
const newDeck = await post<DeckCreateData>('/decks', {
  title: 'My New Deck'
});

// PUT request
const updatedDeck = await put<DeckOut>('/decks/123', {
  title: 'Updated Title'
});

// DELETE request
await del('/decks/123');
```

### Error Handling

```typescript
import { ApiError, getMessage, formatErrorMessage } from '$lib/utils';

try {
  const deck = await get('/decks/123');
} catch (error) {
  if (error instanceof ApiError) {
    // Get error message in current language
    const message = getMessage(error.messageDict);
    
    // Or format with field errors
    const formatted = formatErrorMessage(error.messageDict, error.errors);
    
    // Check specific field error
    const emailError = error.fieldErrors.get('email');
  }
}
```

### File Upload

```typescript
import { uploadFile } from '$lib/utils';

const files = await uploadFile<FileUploadListData>(
  '/files/upload?deck_id=123',
  fileInput.files,
  (progress) => {
    console.log(`Upload progress: ${progress}%`);
  }
);
```

### Language Management

```typescript
import { getCurrentLanguage, setLanguage } from '$lib/utils';

// Get current language
const lang = getCurrentLanguage(); // 'en' | 'ru' | 'hy'

// Set language preference
setLanguage('ru');
```

## Features

- ✅ Automatic JWT token handling via httpOnly cookies
- ✅ Automatic token refresh on 401 errors
- ✅ Multilingual error messages (en, ru, hy)
- ✅ Field-level error extraction
- ✅ Request/response logging in development
- ✅ Timeout handling
- ✅ Network error handling
- ✅ TypeScript support with generics

