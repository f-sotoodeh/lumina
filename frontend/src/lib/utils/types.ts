/**
 * Shared type definitions for API communication
 */

export interface MessageDict {
	en: string;
	ru: string;
	hy: string;
}

export interface ErrorItem {
	field: string | null;
	message: MessageDict;
}

export interface APIResponse<T = unknown> {
	success: boolean;
	data: T | null;
	message: MessageDict | null;
	errors: ErrorItem[] | null;
}

export interface ApiRequestOptions extends RequestInit {
	skipAuth?: boolean;
	timeout?: number;
}

