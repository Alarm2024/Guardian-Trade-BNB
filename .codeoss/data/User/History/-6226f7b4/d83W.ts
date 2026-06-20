export interface Env {
  // You can set secrets like API_KEY using:
  // npx wrangler secret put API_KEY
  API_KEY?: string;
}

/**
 * Helper to create standard JSON responses with CORS headers
 * and high-grade security headers to prevent "spying" and exploits.
 */
const jsonResponse = (data: any, status = 200) => {
  const securityHeaders = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none';",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload"
  };

  return new Response(JSON.stringify(data), {
    status,
    headers: securityHeaders,
  });
};

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const method = request.method;

    // Handle CORS preflight requests
    if (method === "OPTIONS") {
      return jsonResponse({ message: "OK" }, 204);
    }

    // 1. Mandatory Security Check: Validate API Key
    const authHeader = request.headers.get("Authorization");
    if (env.API_KEY && authHeader !== `Bearer ${env.API_KEY}`) {
      return jsonResponse({ error: "Unauthorized access blocked." }, 401);
    }

    try {
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
      // 2. Prevent Info Leakage: Do not return raw error messages to the user
      return jsonResponse({ 
        error: "Internal Server Error", 
        traceId: crypto.randomUUID() 
      }, 500);
    }
  },
};