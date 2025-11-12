import { c as create_ssr_component } from "../../chunks/ssr.js";
import { e as escape } from "../../chunks/escape.js";
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const apiUrl = "http://localhost:8000/api/v1";
  return `<div class="container mx-auto p-8"><h1 class="text-4xl font-bold mb-4" data-svelte-h="svelte-1bkzn9o">Lumina Frontend</h1> <p class="text-lg mb-4" data-svelte-h="svelte-1185oh1">Configuration test page</p> <div class="card bg-base-100 shadow-xl"><div class="card-body"><h2 class="card-title" data-svelte-h="svelte-yxa1di">Configuration Status</h2> <p data-svelte-h="svelte-z729ps">TypeScript: ✅ Configured</p> <p data-svelte-h="svelte-xpc36f">DaisyUI: ✅ Configured</p> <p data-svelte-h="svelte-11szep0">Tailwind CSS: ✅ Configured</p> <p data-svelte-h="svelte-1ui9wwr">Environment Variables: ✅ Configured</p> <p class="text-sm text-gray-500">API URL: ${escape(apiUrl)}</p></div></div> <button class="btn btn-primary mt-4" data-svelte-h="svelte-1j4rife">Test DaisyUI Button</button></div>`;
});
export {
  Page as default
};
//# sourceMappingURL=_page.svelte.js.map
