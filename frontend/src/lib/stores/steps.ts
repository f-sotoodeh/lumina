/**
 * Steps Store
 * Manages steps array and current step selection
 */

import { writable, derived, get } from 'svelte/store';
import { get as apiGet, post, patch, del } from '$lib/utils/api';

/**
 * Step interface matching backend StepOut schema
 */
export interface Step {
	id: string;
	data_x: number;
	data_y: number;
	data_z: number;
	data_rotate: number;
	data_rotate_x: number;
	data_rotate_y: number;
	data_rotate_z: number;
	data_scale: number;
	data_transition_duration: number;
	data_autoplay: number | null;
	is_slide: boolean;
	inner_html: string;
	notes: string;
	font_family: string | null;
	user_id: string;
	deck_id: string;
}

/**
 * Step settings update data
 */
export interface StepUpdateSettings {
	data_x?: number;
	data_y?: number;
	data_z?: number;
	data_rotate?: number;
	data_rotate_x?: number;
	data_rotate_y?: number;
	data_rotate_z?: number;
	data_scale?: number;
	data_transition_duration?: number;
	data_autoplay?: number | null;
	is_slide?: boolean;
}

/**
 * Step content update data
 */
export interface StepUpdateData {
	inner_html?: string;
	notes?: string;
	font_family?: string | null;
}

/**
 * Step create data
 */
export interface StepCreateData {
	data_x?: number;
	data_y?: number;
	data_z?: number;
	data_rotate?: number;
	data_rotate_x?: number;
	data_rotate_y?: number;
	data_rotate_z?: number;
	data_scale?: number;
	data_transition_duration?: number;
	data_autoplay?: number | null;
	is_slide?: boolean;
	inner_html?: string;
	notes?: string;
	font_family?: string | null;
}

/**
 * Steps list response
 */
export interface StepsListResponse {
	steps: Step[];
	total: number;
	page: number;
	pages: number;
}

// Initial state
const initialState: Step[] = [];

// Create writable stores
export const stepsStore = writable<Step[]>(initialState);
export const currentStepId = writable<string | null>(null);
export const isLoadingSteps = writable<boolean>(false);
export const stepsError = writable<string | null>(null);

// Derived stores
export const currentStep = derived(
	[stepsStore, currentStepId],
	([$steps, $currentStepId]) => {
		if (!$currentStepId) return null;
		return $steps.find((step) => step.id === $currentStepId) || null;
	}
);

export const stepsCount = derived(stepsStore, ($steps) => $steps.length);

/**
 * Load steps for a deck
 * @param deckId Deck ID
 */
export async function loadSteps(deckId: string): Promise<Step[]> {
	isLoadingSteps.set(true);
	stepsError.set(null);

	try {
		const response = await apiGet<StepsListResponse>(`/steps/decks/${deckId}`);
		stepsStore.set(response.steps);
		return response.steps;
	} catch (error) {
		stepsError.set(error instanceof Error ? error.message : 'Failed to load steps');
		stepsStore.set([]);
		throw error;
	} finally {
		isLoadingSteps.set(false);
	}
}

/**
 * Create a new step
 * @param deckId Deck ID
 * @param data Step create data
 * @returns Created step
 */
export async function createStep(deckId: string, data?: StepCreateData): Promise<Step> {
	stepsError.set(null);

	try {
		const stepData = {
			data_x: data?.data_x ?? 0,
			data_y: data?.data_y ?? 0,
			data_z: data?.data_z ?? 0,
			data_rotate: data?.data_rotate ?? 0,
			data_rotate_x: data?.data_rotate_x ?? 0,
			data_rotate_y: data?.data_rotate_y ?? 0,
			data_rotate_z: data?.data_rotate_z ?? 0,
			data_scale: data?.data_scale ?? 1.0,
			data_transition_duration: data?.data_transition_duration ?? 1000,
			data_autoplay: data?.data_autoplay ?? null,
			is_slide: data?.is_slide ?? true,
			inner_html: data?.inner_html ?? '<h1>New Slide</h1>',
			notes: data?.notes ?? '',
			font_family: data?.font_family ?? null
		};

		const response = await post<{ id: string }>(`/steps/decks/${deckId}`, stepData);
		
		// Reload steps to get the full step data
		await loadSteps(deckId);
		
		// Select the new step
		currentStepId.set(response.id);
		
		// Return the created step
		const steps = get(stepsStore);
		const newStep = steps.find((s) => s.id === response.id);
		if (!newStep) {
			throw new Error('Failed to find created step');
		}
		return newStep;
	} catch (error) {
		stepsError.set(error instanceof Error ? error.message : 'Failed to create step');
		throw error;
	}
}

/**
 * Update step settings (position, rotation, scale, transitions)
 * @param stepId Step ID
 * @param data Step settings update data
 * @returns Updated step
 */
export async function updateStepSettings(stepId: string, data: StepUpdateSettings): Promise<Step> {
	stepsError.set(null);

	try {
		const updatedStep = await patch<Step>(`/steps/${stepId}/settings`, data);
		
		// Update step in store
		stepsStore.update((steps) =>
			steps.map((step) => (step.id === stepId ? updatedStep : step))
		);
		
		return updatedStep;
	} catch (error) {
		stepsError.set(error instanceof Error ? error.message : 'Failed to update step settings');
		throw error;
	}
}

/**
 * Update step content (inner_html, notes, font_family)
 * @param stepId Step ID
 * @param data Step content update data
 * @returns Updated step
 */
export async function updateStepData(stepId: string, data: StepUpdateData): Promise<Step> {
	stepsError.set(null);

	try {
		const updatedStep = await patch<Step>(`/steps/${stepId}/data`, data);
		
		// Update step in store
		stepsStore.update((steps) =>
			steps.map((step) => (step.id === stepId ? updatedStep : step))
		);
		
		return updatedStep;
	} catch (error) {
		stepsError.set(error instanceof Error ? error.message : 'Failed to update step data');
		throw error;
	}
}

/**
 * Delete a step
 * @param stepId Step ID
 */
export async function deleteStep(stepId: string): Promise<void> {
	stepsError.set(null);

	try {
		await del(`/steps/${stepId}`);
		
		// Remove step from store
		stepsStore.update((steps) => steps.filter((step) => step.id !== stepId));
		
		// Clear current step if it was deleted
		const currentId = get(currentStepId);
		if (currentId === stepId) {
			currentStepId.set(null);
		}
	} catch (error) {
		stepsError.set(error instanceof Error ? error.message : 'Failed to delete step');
		throw error;
	}
}

/**
 * Duplicate a step
 * @param stepId Step ID to duplicate
 * @returns Duplicated step
 */
export async function duplicateStep(stepId: string): Promise<Step> {
	stepsError.set(null);

	try {
		const response = await post<{ id: string }>(`/steps/${stepId}/duplicate`, {});
		
		// Reload steps to get the duplicated step
		const currentStep = get(stepsStore).find((s) => s.id === stepId);
		if (!currentStep) {
			throw new Error('Step not found');
		}
		
		await loadSteps(currentStep.deck_id);
		
		// Select the duplicated step
		currentStepId.set(response.id);
		
		// Return the duplicated step
		const steps = get(stepsStore);
		const duplicatedStep = steps.find((s) => s.id === response.id);
		if (!duplicatedStep) {
			throw new Error('Failed to find duplicated step');
		}
		return duplicatedStep;
	} catch (error) {
		stepsError.set(error instanceof Error ? error.message : 'Failed to duplicate step');
		throw error;
	}
}

/**
 * Reorder steps
 * @param deckId Deck ID
 * @param stepIds Ordered array of step IDs
 */
export async function reorderSteps(deckId: string, stepIds: string[]): Promise<void> {
	stepsError.set(null);

	try {
		await patch(`/steps/decks/${deckId}/reorder`, { step_ids: stepIds });
		
		// Reload steps to get the new order
		await loadSteps(deckId);
	} catch (error) {
		stepsError.set(error instanceof Error ? error.message : 'Failed to reorder steps');
		throw error;
	}
}

/**
 * Select a step
 * @param stepId Step ID to select
 */
export function selectStep(stepId: string | null): void {
	currentStepId.set(stepId);
}

/**
 * Clear steps
 */
export function clearSteps(): void {
	stepsStore.set([]);
	currentStepId.set(null);
	stepsError.set(null);
}

/**
 * Get current step from store
 * @returns Current step or null
 */
export function getCurrentStep(): Step | null {
	const stepId = get(currentStepId);
	if (!stepId) return null;
	const steps = get(stepsStore);
	return steps.find((step) => step.id === stepId) || null;
}

/**
 * Get all steps from store
 * @returns Array of steps
 */
export function getAllSteps(): Step[] {
	return get(stepsStore);
}

