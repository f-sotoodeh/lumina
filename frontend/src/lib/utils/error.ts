/**
 * Error handling utilities for API responses
 */

import type { MessageDict, ErrorItem, APIResponse } from './types';

/**
 * Custom API Error class with structured error data
 */
export class ApiError extends Error {
	status: number;
	messageDict: MessageDict | null;
	errors: ErrorItem[];
	fieldErrors: Map<string, string>;

	constructor(
		status: number,
		messageDict: MessageDict | null,
		errors: ErrorItem[] = []
	) {
		const message = getMessage(messageDict) || `API Error ${status}`;
		super(message);
		this.name = 'ApiError';
		this.status = status;
		this.messageDict = messageDict;
		this.errors = errors;
		this.fieldErrors = new Map();

		// Build field errors map for easy lookup
		errors.forEach((error) => {
			if (error.field) {
				this.fieldErrors.set(error.field, getMessage(error.message));
			}
		});
	}
}

/**
 * Get current language preference
 * Checks localStorage first, then browser language, defaults to 'en'
 */
export function getCurrentLanguage(): 'en' | 'ru' | 'hy' {
	if (typeof window === 'undefined') return 'en';

	// Check localStorage for user preference
	const stored = localStorage.getItem('lumina_language');
	if (stored === 'en' || stored === 'ru' || stored === 'hy') {
		return stored;
	}

	// Check browser language
	const browserLang = navigator.language.toLowerCase();
	if (browserLang.startsWith('ru')) return 'ru';
	if (browserLang.startsWith('hy')) return 'hy';

	// Default to English
	return 'en';
}

/**
 * Set language preference
 */
export function setLanguage(lang: 'en' | 'ru' | 'hy'): void {
	if (typeof window !== 'undefined') {
		localStorage.setItem('lumina_language', lang);
	}
}

/**
 * Extract message from MessageDict for current language
 */
export function getMessage(messageDict: MessageDict | null): string | null {
	if (!messageDict) return null;

	const lang = getCurrentLanguage();
	return messageDict[lang] || messageDict.en || null;
}

/**
 * Parse API error response
 */
export function parseApiErrorResponse(
	response: Response,
	body: unknown
): { messageDict: MessageDict | null; errors: ErrorItem[] } {
	// Try to parse as APIResponse structure
	if (body && typeof body === 'object' && 'success' in body) {
		const apiResponse = body as APIResponse<unknown>;
		return {
			messageDict: apiResponse.message || null,
			errors: apiResponse.errors || []
		};
	}

	// Fallback: try to extract error from body
	if (body && typeof body === 'object' && 'detail' in body) {
		const detail = (body as { detail: unknown }).detail;
		if (detail && typeof detail === 'object' && 'message' in detail) {
			const message = (detail as { message: unknown }).message;
			if (message && typeof message === 'object') {
				return {
					messageDict: message as MessageDict,
					errors: []
				};
			}
		}
	}

	// Last resort: create a generic error message
	return {
		messageDict: {
			en: `Request failed with status ${response.status}`,
			ru: `Запрос не удался со статусом ${response.status}`,
			hy: `Հարցումը ձախողվեց ${response.status} կարգավիճակով`
		},
		errors: []
	};
}

/**
 * Format field-level errors for display
 * Returns a map of field names to error messages
 */
export function formatFieldErrors(errors: ErrorItem[]): Map<string, string> {
	const fieldErrors = new Map<string, string>();
	errors.forEach((error) => {
		if (error.field) {
			fieldErrors.set(error.field, getMessage(error.message) || '');
		}
	});
	return fieldErrors;
}

/**
 * Format general error message for display
 */
export function formatErrorMessage(
	messageDict: MessageDict | null,
	errors: ErrorItem[] = []
): string {
	// If there's a general message, use it
	if (messageDict) {
		const msg = getMessage(messageDict);
		if (msg) return msg;
	}

	// If there are field errors, combine them
	if (errors.length > 0) {
		const fieldMessages = errors
			.map((error) => {
				if (error.field) {
					return `${error.field}: ${getMessage(error.message)}`;
				}
				return getMessage(error.message);
			})
			.filter(Boolean)
			.join(', ');

		if (fieldMessages) return fieldMessages;
	}

	// Fallback
	return 'An error occurred';
}

/**
 * Get error message for a specific field
 */
export function getFieldError(
	errors: ErrorItem[],
	fieldName: string
): string | null {
	const error = errors.find((e) => e.field === fieldName);
	return error ? getMessage(error.message) : null;
}

