<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { isAuthenticated, currentUser, logout, toastStore } from '$lib/stores';
	import { requireAuth } from '$lib/utils/auth-guard';

	let checkingAuth = true;
	let authChecked = false;

	// Protect route and initialize auth check
	onMount(() => {
		if (browser) {
			checkingAuth = true;
			// Wait a bit for user store to initialize, then check auth
			setTimeout(() => {
				const authenticated = requireAuth();
				checkingAuth = false;
				authChecked = true;
				if (!authenticated) {
					return; // Redirect handled by requireAuth
				}
			}, 150);
		} else {
			checkingAuth = false;
			authChecked = true;
		}
	});

	async function handleLogout() {
		try {
			await logout();
			toastStore.show('Logged out successfully', 'success');
		} catch (error) {
			toastStore.show('Failed to logout', 'error');
		}
	}

	function getInitials(firstName: string | null, lastName: string | null): string {
		const first = firstName?.[0]?.toUpperCase() || '';
		const last = lastName?.[0]?.toUpperCase() || '';
		return first + last || '?';
	}

	function getAvatarColor(email: string): string {
		// Simple hash for consistent color
		let hash = 0;
		for (let i = 0; i < email.length; i++) {
			hash = email.charCodeAt(i) + ((hash << 5) - hash);
		}
		const colors = [
			'bg-primary',
			'bg-secondary',
			'bg-accent',
			'bg-info',
			'bg-success',
			'bg-warning',
			'bg-error'
		];
		return colors[Math.abs(hash) % colors.length];
	}
</script>

{#if checkingAuth || !authChecked}
	<div class="min-h-screen flex items-center justify-center">
		<span class="loading loading-spinner loading-lg"></span>
	</div>
{:else if $isAuthenticated && $currentUser}
	<div class="min-h-screen flex flex-col">
		<!-- Navigation Bar -->
		<nav class="navbar bg-base-100 shadow-lg">
			<div class="flex-1">
				<a href="/decks" class="btn btn-ghost text-xl font-bold text-primary">
					Lumina
				</a>
			</div>
			<div class="flex-none gap-2">
				<!-- Navigation Links -->
				<ul class="menu menu-horizontal px-1">
					<li>
						<a href="/decks" class="btn btn-ghost">Decks</a>
					</li>
				</ul>

				<!-- User Menu Dropdown -->
				<div class="dropdown dropdown-end">
					<label tabindex="0" class="btn btn-ghost btn-circle avatar">
						<div
							class="w-10 rounded-full {getAvatarColor($currentUser.email)} text-white flex items-center justify-center font-semibold"
						>
							{#if $currentUser.avatar_url}
								<img src={$currentUser.avatar_url} alt="Avatar" />
							{:else}
								{getInitials($currentUser.first_name, $currentUser.last_name)}
							{/if}
						</div>
					</label>
					<ul
						tabindex="0"
						class="mt-3 z-[1] p-2 shadow menu menu-sm dropdown-content bg-base-100 rounded-box w-52"
					>
						<li>
							<a href="/profile" class="justify-between">
								Profile
								<span class="badge">New</span>
							</a>
						</li>
						<li><a>Settings</a></li>
						<li><button on:click={handleLogout}>Logout</button></li>
					</ul>
				</div>
			</div>
		</nav>

		<!-- Main Content -->
		<main class="flex-1">
			<slot />
		</main>

		<!-- Toast Container -->
		<div class="toast toast-top toast-end z-50">
			{#each $toastStore as toast (toast.id)}
				<div class="alert alert-{toast.type === 'error' ? 'error' : toast.type === 'success' ? 'success' : toast.type === 'warning' ? 'warning' : 'info'} shadow-lg">
					<span>{toast.message}</span>
					<button
						class="btn btn-sm btn-circle btn-ghost"
						on:click={() => toastStore.remove(toast.id)}
					>
						✕
					</button>
				</div>
			{/each}
		</div>
	{/if}

