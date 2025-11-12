<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import '../app.css';
	import { initUserStore } from '$lib/stores';

	// Initialize user store on client-side mount
	onMount(() => {
		if (browser) {
			initUserStore();
		}
	});
</script>

<div class="min-h-screen">
	<slot />
</div>
