export interface Env {
	// Example binding to a KV Namespace
	// MY_KV_NAMESPACE: KVNamespace;
}

export default {
	async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
		const url = new URL(request.url);
		
		return new Response(JSON.stringify({
			message: "Hello! Your server is running for free.",
			path: url.pathname,
			timestamp: new Date().toISOString()
		}), { headers: { "Content-Type": "application/json" } });
	},
};