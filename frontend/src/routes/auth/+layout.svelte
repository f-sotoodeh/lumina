<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { isAuthenticated } from '$lib/stores';
	import { redirectIfAuthenticated } from '$lib/utils/auth-guard';

	let redirecting = false;

	// Redirect if already authenticated
	onMount(() => {
		if (browser) {
			// Wait a bit for user store to initialize
			setTimeout(() => {
				redirectIfAuthenticated();
			}, 100);
		}
	});

	// Reactive redirect (in case auth state changes after mount)
	$: if (browser && $isAuthenticated && !redirecting) {
		redirecting = true;
		goto('/decks');
	}
</script>

<div class="min-h-screen flex items-center justify-center bg-base-200 px-4">
	<div class="card bg-base-100 shadow-xl w-full max-w-md">
		<div class="card-body">
			<div class="text-center mb-6">
				<h1 class="text-3xl font-bold text-primary">Lumina</h1>
				<p class="text-sm text-base-content/70 mt-2">Create beautiful presentations</p>
			</div>
			<slot />
		</div>
	</div>
</div>

