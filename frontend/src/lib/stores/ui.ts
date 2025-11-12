/**
 * UI Store
 * Manages UI state: loading indicators, toast notifications, and modals
 */

import { writable, derived } from 'svelte/store';

/**
 * Toast notification interface
 */
export interface Toast {
	id: string;
	message: string;
	type: 'success' | 'error' | 'info' | 'warning';
	duration?: number;
}

/**
 * Modal interface
 */
export interface Modal {
	id: string;
	component: any;
	props?: Record<string, any>;
}

// Toast store
const createToastStore = () => {
	const { subscribe, update, set } = writable<Toast[]>([]);

	return {
		subscribe,
		/**
		 * Show a toast notification
		 * @param message Toast message
		 * @param type Toast type
		 * @param duration Duration in milliseconds (default: 5000)
		 */
		show: (message: string, type: Toast['type'] = 'info', duration: number = 5000) => {
			const id = `toast-${Date.now()}-${Math.random()}`;
			const toast: Toast = { id, message, type, duration };
			
			update((toasts) => [...toasts, toast]);
			
			// Auto-remove toast after duration
			if (duration > 0) {
				setTimeout(() => {
					update((toasts) => toasts.filter((t) => t.id !== id));
				}, duration);
			}
			
			return id;
		},
		/**
		 * Remove a toast by ID
		 * @param id Toast ID
		 */
		remove: (id: string) => {
			update((toasts) => toasts.filter((t) => t.id !== id));
		},
		/**
		 * Clear all toasts
		 */
		clear: () => {
			set([]);
		}
	};
};

// Modal store
const createModalStore = () => {
	const { subscribe, update, set } = writable<Modal[]>([]);

	return {
		subscribe,
		/**
		 * Open a modal
		 * @param id Modal ID
		 * @param component Modal component
		 * @param props Modal props
		 */
		open: (id: string, component: any, props?: Record<string, any>) => {
			const modal: Modal = { id, component, props };
			update((modals) => {
				// Remove existing modal with same ID if present
				const filtered = modals.filter((m) => m.id !== id);
				return [...filtered, modal];
			});
		},
		/**
		 * Close a modal by ID
		 * @param id Modal ID
		 */
		close: (id: string) => {
			update((modals) => modals.filter((m) => m.id !== id));
		},
		/**
		 * Close all modals
		 */
		closeAll: () => {
			set([]);
		}
	};
};

// Loading states store
const createLoadingStore = () => {
	const { subscribe, update } = writable<Set<string>>(new Set());

	return {
		subscribe,
		/**
		 * Set loading state for a key
		 * @param key Loading key
		 * @param isLoading Whether it's loading
		 */
		set: (key: string, isLoading: boolean) => {
			update((loadingKeys) => {
				const newSet = new Set(loadingKeys);
				if (isLoading) {
					newSet.add(key);
				} else {
					newSet.delete(key);
				}
				return newSet;
			});
		},
		/**
		 * Clear all loading states
		 */
		clear: () => {
			update(() => new Set());
		}
	};
};

// Create stores
export const toastStore = createToastStore();
export const modalStore = createModalStore();
export const loadingStore = createLoadingStore();

// Derived stores
export const hasToasts = derived(toastStore, ($toasts) => $toasts.length > 0);
export const hasModals = derived(modalStore, ($modals) => $modals.length > 0);
export const isLoading = derived(loadingStore, ($loadingKeys) => $loadingKeys.size > 0);

// Convenience functions
export const showToast = toastStore.show;
export const removeToast = toastStore.remove;
export const clearToasts = toastStore.clear;
export const openModal = modalStore.open;
export const closeModal = modalStore.close;
export const closeAllModals = modalStore.closeAll;
export const setLoading = loadingStore.set;
export const clearLoading = loadingStore.clear;

