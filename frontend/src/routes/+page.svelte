<script lang="ts">
	// Test environment variable access
	const apiUrl = import.meta.env.VITE_API_URL;
</script>

<div class="container mx-auto p-8">
	<h1 class="text-4xl font-bold mb-4">Lumina Frontend</h1>
	<p class="text-lg mb-4">Configuration test page</p>
	
	<div class="card bg-base-100 shadow-xl">
		<div class="card-body">
			<h2 class="card-title">Configuration Status</h2>
			<p>TypeScript: ✅ Configured</p>
			<p>DaisyUI: ✅ Configured</p>
			<p>Tailwind CSS: ✅ Configured</p>
			<p>Environment Variables: ✅ Configured</p>
			<p class="text-sm text-gray-500">API URL: {apiUrl}</p>
		</div>
	</div>
	
	<button class="btn btn-primary mt-4">Test DaisyUI Button</button>
</div>

