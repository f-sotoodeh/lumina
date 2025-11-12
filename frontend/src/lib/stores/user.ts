/**
 * User Store
 * Manages user authentication state and profile data
 */

import { writable, derived, get } from 'svelte/store';
import { get as apiGet, post, put, resetRefreshFailed } from '$lib/utils/api';
import { getCurrentLanguage, setLanguage, parseApiErrorResponse, ApiError } from '$lib/utils/error';
import { browser } from '$app/environment';
import { goto } from '$app/navigation';

/**
 * User interface matching backend UserOut schema
 */
export interface User {
	id: string;
	email: string;
	first_name: string | null;
	last_name: string | null;
	avatar_url: string | null;
	preferred_language: string;
	is_admin: boolean;
	created_at: string;
	last_logged_in_at: string | null;
}

/**
 * Auth response interface matching backend AuthResponseData schema
 */
export interface AuthResponse {
	access_token: string;
	refresh_token: string;
	token_type: string;
	user: {
		id: string;
		email: string;
		first_name: string | null;
		last_name: string | null;
		avatar_url: string | null;
		preferred_language: string;
	};
}

/**
 * Login credentials
 */
export interface LoginCredentials {
	username: string; // email
	password: string;
}

/**
 * Register data
 */
export interface RegisterData {
	email: string;
	password: string;
	first_name?: string | null;
	last_name?: string | null;
}

/**
 * User update data
 */
export interface UserUpdateData {
	first_name?: string | null;
	last_name?: string | null;
	preferred_language?: 'en' | 'ru' | 'hy';
}

// Initial state
const initialState: User | null = null;

// Create writable store
export const userStore = writable<User | null>(initialState);

// Derived stores
export const isAuthenticated = derived(userStore, ($user) => $user !== null);
export const currentUser = derived(userStore, ($user) => $user);

/**
 * Initialize user store
 * Attempts to load user profile if authenticated
 */
export async function initUserStore(): Promise<void> {
	if (!browser) return;

	try {
		const user = await loadUserProfile();
		if (user) {
			userStore.set(user);
			// Sync preferred_language to localStorage
			if (user.preferred_language) {
				setLanguage(user.preferred_language as 'en' | 'ru' | 'hy');
			}
		}
	} catch (error) {
		// User not authenticated or error loading profile
		userStore.set(null);
	}
}

/**
 * Login user
 * @param credentials Login credentials
 * @returns User data
 */
export async function login(credentials: LoginCredentials): Promise<User> {
	try {
		// Use FormData for OAuth2PasswordRequestForm
		const formData = new FormData();
		formData.append('username', credentials.username);
		formData.append('password', credentials.password);

		const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/auth/login`, {
			method: 'POST',
			body: formData,
			credentials: 'include'
		});

		if (!response.ok) {
			let errorBody: unknown;
			try {
				errorBody = await response.json();
			} catch {
				errorBody = null;
			}
			const { messageDict, errors } = parseApiErrorResponse(response, errorBody);
			throw new ApiError(response.status, messageDict, errors);
		}

		const apiResponse = await response.json();
		const authData: AuthResponse = apiResponse.data;

		// Update user store
		const user: User = {
			id: authData.user.id,
			email: authData.user.email,
			first_name: authData.user.first_name,
			last_name: authData.user.last_name,
			avatar_url: authData.user.avatar_url,
			preferred_language: authData.user.preferred_language || 'en',
			is_admin: false, // Will be updated when profile is loaded
			created_at: '',
			last_logged_in_at: null
		};

		userStore.set(user);

		// Sync preferred_language to localStorage
		if (user.preferred_language) {
			setLanguage(user.preferred_language as 'en' | 'ru' | 'hy');
		}

		// Reset refresh failed flag after successful login
		resetRefreshFailed();

		// Load full profile to get all user data
		await loadUserProfile();

		return get(userStore)!;
	} catch (error) {
		userStore.set(null);
		throw error;
	}
}

/**
 * Register new user
 * @param data Registration data
 * @returns User data
 */
export async function register(data: RegisterData): Promise<User> {
	try {
		const response = await post<AuthResponse>('/auth/register', {
			email: data.email,
			password: data.password,
			first_name: data.first_name,
			last_name: data.last_name
		});

		// Update user store
		const user: User = {
			id: response.user.id,
			email: response.user.email,
			first_name: response.user.first_name,
			last_name: response.user.last_name,
			avatar_url: response.user.avatar_url,
			preferred_language: response.user.preferred_language || 'en',
			is_admin: false,
			created_at: '',
			last_logged_in_at: null
		};

		userStore.set(user);

		// Sync preferred_language to localStorage
		if (user.preferred_language) {
			setLanguage(user.preferred_language as 'en' | 'ru' | 'hy');
		}

		// Reset refresh failed flag after successful registration
		resetRefreshFailed();

		// Load full profile to get all user data
		await loadUserProfile();

		return get(userStore)!;
	} catch (error) {
		userStore.set(null);
		throw error;
	}
}

/**
 * Logout user
 */
export async function logout(): Promise<void> {
	try {
		await post('/auth/logout', {});
	} catch (error) {
		// Continue with logout even if API call fails
		console.error('Logout API call failed:', error);
	} finally {
		// Clear user store
		userStore.set(null);
		
		// Clear language preference from localStorage (optional - you might want to keep it)
		// localStorage.removeItem('lumina_language');
		
		// Redirect to login
		if (browser) {
			goto('/auth/login');
		}
	}
}

/**
 * Load user profile from API
 * @returns User data or null if not authenticated
 */
export async function loadUserProfile(): Promise<User | null> {
	try {
		const user = await apiGet<User>('/users/me');
		userStore.set(user);
		
		// Sync preferred_language to localStorage if changed
		if (user.preferred_language) {
			const currentLang = getCurrentLanguage();
			if (user.preferred_language !== currentLang) {
				setLanguage(user.preferred_language as 'en' | 'ru' | 'hy');
			}
		}
		
		return user;
	} catch (error) {
		// 401 or other auth error - user not authenticated
		userStore.set(null);
		return null;
	}
}

/**
 * Update user profile
 * @param data User update data
 * @returns Updated user data
 */
export async function updateProfile(data: UserUpdateData): Promise<User> {
	try {
		const updatedUser = await put<User>('/users/me', data);
		userStore.set(updatedUser);
		
		// Sync preferred_language to localStorage if changed
		if (data.preferred_language !== undefined) {
			setLanguage(data.preferred_language);
		}
		
		return updatedUser;
	} catch (error) {
		// Reload profile on error to ensure consistency
		await loadUserProfile();
		throw error;
	}
}

/**
 * Get current user from store
 * @returns Current user or null
 */
export function getCurrentUser(): User | null {
	return get(userStore);
}

