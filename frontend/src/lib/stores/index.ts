/**
 * Store Exports
 * Central export point for all stores
 */

// User store
export {
	userStore,
	isAuthenticated,
	currentUser,
	initUserStore,
	login,
	register,
	logout,
	loadUserProfile,
	updateProfile,
	getCurrentUser,
	type User,
	type AuthResponse,
	type LoginCredentials,
	type RegisterData,
	type UserUpdateData
} from './user';

// Deck store
export {
	deckStore,
	isLoadingDeck,
	isSavingDeck,
	deckError,
	currentDeck,
	deckId,
	deckTitle,
	loadDeck,
	updateDeck,
	updateDeckOrder,
	clearDeck,
	getCurrentDeck,
	type Deck,
	type DeckUpdateData
} from './deck';

// Steps store
export {
	stepsStore,
	currentStepId,
	currentStep,
	isLoadingSteps,
	stepsError,
	stepsCount,
	loadSteps,
	createStep,
	updateStepSettings,
	updateStepData,
	deleteStep,
	duplicateStep,
	reorderSteps,
	selectStep,
	clearSteps,
	getCurrentStep,
	getAllSteps,
	type Step,
	type StepUpdateSettings,
	type StepUpdateData,
	type StepCreateData,
	type StepsListResponse
} from './steps';

// UI store
export {
	toastStore,
	modalStore,
	loadingStore,
	hasToasts,
	hasModals,
	isLoading,
	showToast,
	removeToast,
	clearToasts,
	openModal,
	closeModal,
	closeAllModals,
	setLoading,
	clearLoading,
	type Toast,
	type Modal
} from './ui';

