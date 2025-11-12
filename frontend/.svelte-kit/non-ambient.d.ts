
// this file is generated — do not edit it


declare module "svelte/elements" {
	export interface HTMLAttributes<T> {
		'data-sveltekit-keepfocus'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-noscroll'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-preload-code'?:
			| true
			| ''
			| 'eager'
			| 'viewport'
			| 'hover'
			| 'tap'
			| 'off'
			| undefined
			| null;
		'data-sveltekit-preload-data'?: true | '' | 'hover' | 'tap' | 'off' | undefined | null;
		'data-sveltekit-reload'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-replacestate'?: true | '' | 'off' | undefined | null;
	}
}

export {};


declare module "$app/types" {
	export interface AppTypes {
		RouteId(): "/(app)" | "/" | "/auth" | "/auth/forgot-password" | "/auth/login" | "/auth/register" | "/(app)/decks" | "/(app)/decks/[id]" | "/(app)/decks/[id]/preview" | "/preview" | "/preview/[uuid]";
		RouteParams(): {
			"/(app)/decks/[id]": { id: string };
			"/(app)/decks/[id]/preview": { id: string };
			"/preview/[uuid]": { uuid: string }
		};
		LayoutParams(): {
			"/(app)": { id?: string };
			"/": { id?: string; uuid?: string };
			"/auth": Record<string, never>;
			"/auth/forgot-password": Record<string, never>;
			"/auth/login": Record<string, never>;
			"/auth/register": Record<string, never>;
			"/(app)/decks": { id?: string };
			"/(app)/decks/[id]": { id: string };
			"/(app)/decks/[id]/preview": { id: string };
			"/preview": { uuid?: string };
			"/preview/[uuid]": { uuid: string }
		};
		Pathname(): "/" | "/auth" | "/auth/" | "/auth/forgot-password" | "/auth/forgot-password/" | "/auth/login" | "/auth/login/" | "/auth/register" | "/auth/register/" | "/decks" | "/decks/" | `/decks/${string}` & {} | `/decks/${string}/` & {} | `/decks/${string}/preview` & {} | `/decks/${string}/preview/` & {} | "/preview" | "/preview/" | `/preview/${string}` & {} | `/preview/${string}/` & {};
		ResolvedPathname(): `${"" | `/${string}`}${ReturnType<AppTypes['Pathname']>}`;
		Asset(): string & {};
	}
}