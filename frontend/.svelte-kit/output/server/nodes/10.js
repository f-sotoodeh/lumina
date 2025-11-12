

export const index = 10;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/preview/_uuid_/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/10.D0zmsJJC.js","_app/immutable/chunks/B2QSKqcC.js","_app/immutable/chunks/BGW9uiDs.js"];
export const stylesheets = [];
export const fonts = [];
