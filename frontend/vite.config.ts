import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	// Note: API calls should use VITE_API_URL directly from environment variables
	// Proxy is optional - uncomment if you want to proxy /api requests
	// server: {
	// 	proxy: {
	// 		'/api': {
	// 			target: 'http://localhost:8000',
	// 			changeOrigin: true
	// 		}
	// 	}
	// },
	build: {
		sourcemap: true
	}
});

