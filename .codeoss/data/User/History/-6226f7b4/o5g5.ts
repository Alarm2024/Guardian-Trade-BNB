export interface Env {
make 	// Example binding to a KV Namespace
	// MY_KV_NAMESPACE: KVNamespace;
  // Define your environment bindings here (KV, D1, etc.)
  // API_KEY: string;
}

/**
 * Helper to create standard JSON responses with CORS headers
 */
const jsonResponse = (data: any, status = 200) => {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
    },
  });
};

export default {
	async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
		const url = new URL(request.url);
		
		return new Response(JSON.stringify({
			message: "Hello! Your server is running for free.",
			path: url.pathname,
			timestamp: new Date().toISOString()
		}), { headers: { "Content-Type": "application/json" } });
	},
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    try {
      const url = new URL(request.url);
      const method = request.method;

      // Handle CORS preflight requests
      if (method === "OPTIONS") {
        return jsonResponse({ message: "OK" }, 204);
      }

      // Basic Routing logic
      switch (url.pathname) {
        case "/":
          return jsonResponse({
            message: "Hello! Your server is running for free.",
            status: "healthy",
            timestamp: new Date().toISOString(),
            endpoints: ["/api/info", "/api/echo"]
          });

        case "/api/info":
          return jsonResponse({
            colo: request.cf?.colo || "Unknown",
            country: request.cf?.country || "Unknown",
            userAgent: request.headers.get("user-agent")
          });

        case "/api/echo":
          if (method !== "POST") return jsonResponse({ error: "Method not allowed. Please use POST." }, 405);
          const body = await request.json().catch(() => ({}));
          return jsonResponse({ received: body, method });

        default:
          return jsonResponse({ error: "Endpoint not found" }, 404);
      }
    } catch (error: any) {
      return jsonResponse({ error: "Internal Server Error", message: error.message }, 500);
    }
  },
};