/**
 * API Client Wrapper
 * Handles JWT authentication, automatic token refresh, and error handling
 */

import type { ApiRequestOptions, APIResponse } from './types';
import { ApiError, parseApiErrorResponse } from './error';

// Browser detection
const isBrowser = typeof window !== 'undefined';

// API base URL from environment variable
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Flag to prevent infinite refresh loops
let isRefreshing = false;
let refreshPromise: Promise<void> | null = null;
let refreshFailed = false; // Track if refresh has failed to prevent retry loops

/**
 * Get full URL for API endpoint
 */
function getApiUrl(endpoint: string): string {
	// Remove leading slash if present
	const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
	
	// Remove /api/v1 if already present in endpoint
	const normalizedEndpoint = cleanEndpoint.startsWith('api/v1/') 
		? cleanEndpoint.replace('api/v1/', '')
		: cleanEndpoint;
	
	return `${API_BASE_URL}/${normalizedEndpoint}`;
}

/**
 * Refresh access token using refresh token cookie
 */
async function refreshToken(): Promise<void> {
	if (isRefreshing && refreshPromise) {
		return refreshPromise;
	}

	isRefreshing = true;
	refreshPromise = (async () => {
		try {
			const response = await fetch(getApiUrl('/auth/refresh'), {
				method: 'POST',
				credentials: 'include',
				headers: {
					'Content-Type': 'application/json'
				}
			});

			if (!response.ok) {
				// Refresh failed - clear auth state
				isRefreshing = false;
				refreshPromise = null;
				refreshFailed = true; // Mark refresh as failed to prevent retry loops
				
				if (isBrowser) {
					// Clear any stored auth state
					localStorage.removeItem('lumina_auth');
					
					// Clear user store to prevent retry loops
					try {
						const { userStore } = await import('$lib/stores');
						userStore.set(null);
					} catch (e) {
						// Ignore import errors
					}
					
					// Use SvelteKit's goto instead of window.location.href to prevent full page reload
					try {
						const { goto } = await import('$app/navigation');
						goto('/auth/login');
					} catch (e) {
						// Fallback to window.location if goto fails
						window.location.href = '/auth/login';
					}
				}
				
				throw new ApiError(response.status, null, []);
			}

			// Refresh successful, tokens are updated in cookies
			isRefreshing = false;
			refreshPromise = null;
			refreshFailed = false; // Reset flag on successful refresh
		} catch (error) {
			isRefreshing = false;
			refreshPromise = null;
			throw error;
		}
	})();

	return refreshPromise;
}

/**
 * Core API request function
 */
async function apiRequest<T>(
	endpoint: string,
	options: ApiRequestOptions = {}
): Promise<T> {
	const {
		skipAuth = false,
		timeout = 30000,
		...fetchOptions
	} = options;

	const url = getApiUrl(endpoint);

	// Set up headers
	const headers = new Headers(fetchOptions.headers);
	
	// Set Content-Type if body is JSON and not already set
	if (fetchOptions.body && !headers.has('Content-Type')) {
		if (fetchOptions.body instanceof FormData) {
			// Don't set Content-Type for FormData, browser will set it with boundary
		} else if (typeof fetchOptions.body === 'string') {
			try {
				JSON.parse(fetchOptions.body);
				headers.set('Content-Type', 'application/json');
			} catch {
				// Not JSON, leave as is
			}
		} else {
			headers.set('Content-Type', 'application/json');
		}
	}

	// Set up fetch options
	const requestOptions: RequestInit = {
		...fetchOptions,
		headers,
		credentials: 'include', // Important: sends httpOnly cookies
	};

	// Log request in development
	if (isBrowser && import.meta.env.DEV) {
		console.log(`[API] ${fetchOptions.method || 'GET'} ${url}`, {
			headers: Object.fromEntries(headers.entries()),
			body: fetchOptions.body
		});
	}

	// Make request with timeout
	const controller = new AbortController();
	const timeoutId = setTimeout(() => controller.abort(), timeout);
	requestOptions.signal = controller.signal;

	try {
		let response = await fetch(url, requestOptions);
		clearTimeout(timeoutId);

		// Log response in development
		if (isBrowser && import.meta.env.DEV) {
			console.log(`[API] ${response.status} ${url}`, response);
		}

		// Handle 401 Unauthorized - try to refresh token
		if (response.status === 401 && !skipAuth && !refreshFailed) {
			try {
				await refreshToken();
				// Retry original request with new token
				clearTimeout(timeoutId);
				const retryController = new AbortController();
				const retryTimeoutId = setTimeout(() => retryController.abort(), timeout);
				requestOptions.signal = retryController.signal;
				
				response = await fetch(url, requestOptions);
				clearTimeout(retryTimeoutId);
			} catch (refreshError) {
				// Refresh failed, error already handled in refreshToken()
				refreshFailed = true; // Mark refresh as failed to prevent further retries
				throw refreshError;
			}
		}

		// Parse response body
		let body: unknown;
		const contentType = response.headers.get('content-type');
		
		if (contentType && contentType.includes('application/json')) {
			try {
				body = await response.json();
			} catch (e) {
				throw new ApiError(
					response.status,
					{
						en: 'Failed to parse JSON response',
						ru: 'Не удалось разобрать JSON ответ',
						hy: 'JSON պատասխանը վերլուծել չհաջողվեց'
					},
					[]
				);
			}
		} else {
			body = await response.text();
		}

		// Handle error responses
		if (!response.ok) {
			const { messageDict, errors } = parseApiErrorResponse(response, body);
			throw new ApiError(response.status, messageDict, errors);
		}

		// Parse successful response
		if (body && typeof body === 'object' && 'success' in body) {
			const apiResponse = body as APIResponse<T>;
			
			// Check if API indicates failure even with 200 status
			if (!apiResponse.success) {
				const { messageDict, errors } = parseApiErrorResponse(response, body);
				throw new ApiError(response.status, messageDict, errors);
			}
			
			// Return data
			return apiResponse.data as T;
		}

		// Fallback: return body as-is if not APIResponse structure
		return body as T;
	} catch (error) {
		clearTimeout(timeoutId);
		
		// Handle network errors
		if (error instanceof TypeError && error.message.includes('fetch')) {
			throw new ApiError(
				0,
				{
					en: 'Network error. Please check your connection.',
					ru: 'Ошибка сети. Проверьте подключение.',
					hy: 'Ցանցի սխալ: Ստուգեք կապը:'
				},
				[]
			);
		}

		// Handle timeout errors
		if (error instanceof Error && error.name === 'AbortError') {
			throw new ApiError(
				0,
				{
					en: 'Request timeout. Please try again.',
					ru: 'Тайм-аут запроса. Попробуйте снова.',
					hy: 'Հարցման ժամանակը լրացել է: Կրկին փորձեք:'
				},
				[]
			);
		}

		// Re-throw ApiError as-is
		if (error instanceof ApiError) {
			throw error;
		}

		// Unknown error
		throw new ApiError(
			0,
			{
				en: error instanceof Error ? error.message : 'Unknown error occurred',
				ru: error instanceof Error ? error.message : 'Произошла неизвестная ошибка',
				hy: error instanceof Error ? error.message : 'Անհայտ սխալ է տեղի ունեցել'
			},
			[]
		);
	}
}

/**
 * HTTP Method Helpers
 */

export function get<T>(endpoint: string, options?: ApiRequestOptions): Promise<T> {
	return apiRequest<T>(endpoint, { ...options, method: 'GET' });
}

export function post<T>(
	endpoint: string,
	body?: unknown,
	options?: ApiRequestOptions
): Promise<T> {
	return apiRequest<T>(endpoint, {
		...options,
		method: 'POST',
		body: body instanceof FormData ? body : JSON.stringify(body)
	});
}

export function put<T>(
	endpoint: string,
	body?: unknown,
	options?: ApiRequestOptions
): Promise<T> {
	return apiRequest<T>(endpoint, {
		...options,
		method: 'PUT',
		body: body instanceof FormData ? body : JSON.stringify(body)
	});
}

export function patch<T>(
	endpoint: string,
	body?: unknown,
	options?: ApiRequestOptions
): Promise<T> {
	return apiRequest<T>(endpoint, {
		...options,
		method: 'PATCH',
		body: body instanceof FormData ? body : JSON.stringify(body)
	});
}

export function del<T>(endpoint: string, options?: ApiRequestOptions): Promise<T> {
	return apiRequest<T>(endpoint, { ...options, method: 'DELETE' });
}

// Export delete as well for convenience
export { del as delete };

/**
 * File upload helper with progress tracking
 */
export async function uploadFile<T>(
	endpoint: string,
	file: File | File[],
	onProgress?: (progress: number) => void
): Promise<T> {
	const files = Array.isArray(file) ? file : [file];
	const formData = new FormData();

	files.forEach((f) => {
		formData.append('files', f);
	});

	// Note: XMLHttpRequest is needed for progress tracking
	// For now, we'll use fetch and call onProgress with 100% after completion
	// Full progress tracking can be added later if needed
	
	if (onProgress) {
		onProgress(0);
	}

	try {
		const result = await post<T>(endpoint, formData, {
			// Don't set Content-Type header, browser will set it with boundary
		});

		if (onProgress) {
			onProgress(100);
		}

		return result;
	} catch (error) {
		if (onProgress) {
			onProgress(0);
		}
		throw error;
	}
}

// Export apiRequest for advanced usage
export { apiRequest };

/**
 * Reset refresh failed flag (useful after successful login)
 */
export function resetRefreshFailed(): void {
	refreshFailed = false;
}

