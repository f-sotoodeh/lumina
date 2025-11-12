/**
 * Auth Guard Utilities
 * Functions for protecting routes and handling authentication redirects
 */

import { get } from 'svelte/store';
import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import { isAuthenticated, getCurrentUser } from '$lib/stores';

/**
 * Check if user is authenticated (without redirect)
 * @returns true if authenticated, false otherwise
 */
export function checkAuth(): boolean {
	if (!browser) return false;
	return get(isAuthenticated);
}

/**
 * Require authentication for a route
 * Redirects to login if not authenticated
 * @returns true if authenticated, false if redirected
 */
export function requireAuth(): boolean {
	if (!browser) return false;

	const authenticated = get(isAuthenticated);
	if (!authenticated) {
		goto('/auth/login');
		return false;
	}
	return true;
}

/**
 * Redirect authenticated users away from auth pages
 * Redirects to /decks if already authenticated
 */
export function redirectIfAuthenticated(): void {
	if (!browser) return;

	const authenticated = get(isAuthenticated);
	if (authenticated) {
		goto('/decks');
	}
}

/**
 * Get current user (helper function)
 * @returns Current user or null
 */
export function getAuthUser() {
	if (!browser) return null;
	return getCurrentUser();
}

