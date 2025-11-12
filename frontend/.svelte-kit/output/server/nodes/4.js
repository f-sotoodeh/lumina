

export const index = 4;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/(app)/decks/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/4.D0zmsJJC.js","_app/immutable/chunks/B2QSKqcC.js","_app/immutable/chunks/BGW9uiDs.js"];
export const stylesheets = [];
export const fonts = [];
