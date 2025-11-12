

export const index = 3;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/3.ClgBPsh1.js","_app/immutable/chunks/B2QSKqcC.js","_app/immutable/chunks/BGW9uiDs.js"];
export const stylesheets = [];
export const fonts = [];
