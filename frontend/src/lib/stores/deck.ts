/**
 * Deck Store
 * Manages current deck state and loading/saving states
 */

import { writable, derived, get } from 'svelte/store';
import { get as apiGet, put, patch } from '$lib/utils/api';

/**
 * Deck interface matching backend DeckOut schema
 */
export interface Deck {
	id: string;
	title: string;
	order: string[];
	is_public: boolean;
	preview_url: string;
	background_color: string;
	data_transition_duration: number;
	data_width: number;
	data_height: number;
	data_max_scale: number | null;
	data_min_scale: number | null;
	data_perspective: number;
	data_autoplay: number | null;
	has_overview: boolean;
	overview_x: number;
	overview_y: number;
	overview_z: number;
	overview_scale: number;
	owner_id: string;
	thumbnail_url: string | null;
	created_at: string;
	updated_at: string;
}

/**
 * Deck update data
 */
export interface DeckUpdateData {
	title?: string;
	order?: string[];
	is_public?: boolean;
	background_color?: string;
	data_transition_duration?: number;
	data_width?: number;
	data_height?: number;
	data_max_scale?: number | null;
	data_min_scale?: number | null;
	data_perspective?: number;
	data_autoplay?: number | null;
	has_overview?: boolean;
	overview_x?: number;
	overview_y?: number;
	overview_z?: number;
	overview_scale?: number;
}

// Initial state
const initialState: Deck | null = null;

// Create writable stores
export const deckStore = writable<Deck | null>(initialState);
export const isLoadingDeck = writable<boolean>(false);
export const isSavingDeck = writable<boolean>(false);
export const deckError = writable<string | null>(null);

// Derived stores
export const currentDeck = derived(deckStore, ($deck) => $deck);
export const deckId = derived(deckStore, ($deck) => $deck?.id || null);
export const deckTitle = derived(deckStore, ($deck) => $deck?.title || '');

/**
 * Load deck by ID
 * @param deckId Deck ID
 */
export async function loadDeck(deckId: string): Promise<Deck> {
	isLoadingDeck.set(true);
	deckError.set(null);

	try {
		const deck = await apiGet<Deck>(`/decks/${deckId}`);
		deckStore.set(deck);
		return deck;
	} catch (error) {
		deckError.set(error instanceof Error ? error.message : 'Failed to load deck');
		deckStore.set(null);
		throw error;
	} finally {
		isLoadingDeck.set(false);
	}
}

/**
 * Update deck
 * @param deckId Deck ID
 * @param data Deck update data
 * @returns Updated deck
 */
export async function updateDeck(deckId: string, data: DeckUpdateData): Promise<Deck> {
	isSavingDeck.set(true);
	deckError.set(null);

	try {
		const updatedDeck = await put<Deck>(`/decks/${deckId}`, data);
		deckStore.set(updatedDeck);
		return updatedDeck;
	} catch (error) {
		deckError.set(error instanceof Error ? error.message : 'Failed to update deck');
		throw error;
	} finally {
		isSavingDeck.set(false);
	}
}

/**
 * Update deck order
 * @param deckId Deck ID
 * @param order New order array
 */
export async function updateDeckOrder(deckId: string, order: string[]): Promise<void> {
	isSavingDeck.set(true);
	deckError.set(null);

	try {
		const updatedDeck = await patch<Deck>(`/decks/${deckId}`, { order });
		deckStore.set(updatedDeck);
	} catch (error) {
		deckError.set(error instanceof Error ? error.message : 'Failed to update deck order');
		throw error;
	} finally {
		isSavingDeck.set(false);
	}
}

/**
 * Clear current deck
 */
export function clearDeck(): void {
	deckStore.set(null);
	deckError.set(null);
}

/**
 * Get current deck from store
 * @returns Current deck or null
 */
export function getCurrentDeck(): Deck | null {
	return get(deckStore);
}

