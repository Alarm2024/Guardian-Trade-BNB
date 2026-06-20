export interface Env {
  // You can set secrets like API_KEY using:
  // npx wrangler secret put API_KEY
  API_KEY?: string;
}

/**
 * Helper to create standard JSON responses with CORS headers
 * and high-grade security headers to prevent "spying" and exploits.
 */
const jsonResponse = (data: any, status = 200, extraHeaders: Record<string, string> = {}) => {
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
    headers: { ...securityHeaders, ...extraHeaders },
  });
};

/**
 * Constant-time comparison to prevent timing attacks on API keys
 */
async function isAuthorized(authHeader: string | null, apiKey: string | undefined): Promise<boolean> {
  if (!apiKey) return true; 
  if (!authHeader || !authHeader.startsWith("Bearer ")) return false;

  const providedKey = authHeader.substring(7);
  const encoder = new TextEncoder();
  const a = encoder.encode(providedKey);
  const b = encoder.encode(apiKey);

  if (a.byteLength !== b.byteLength) return false;
  return crypto.subtle.timingSafeEqual(a, b);
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const requestId = crypto.randomUUID();
    const url = new URL(request.url);
    const method = request.method;

    // Handle CORS preflight requests
    if (method === "OPTIONS") {
      return jsonResponse({ message: "OK" }, 204);
    }

    // 1. Security Check: Constant-time API Key Validation
    if (!(await isAuthorized(request.headers.get("Authorization"), env.API_KEY))) {
      return jsonResponse({ error: "Unauthorized access blocked.", requestId }, 401);
    }

    try {
      // Basic Routing logic
      switch (url.pathname) {
        case "/":
          return jsonResponse({
            message: "Hello! Your server is running for free.",
            status: "healthy",
            requestId,
            timestamp: Date.now(),
            endpoints: ["/api/info", "/api/echo"]
          }, 200, { "X-Request-Id": requestId });

        case "/api/info":
          return jsonResponse({
            colo: request.cf?.colo || "Unknown",
            country: request.cf?.country || "Unknown",
            userAgent: request.headers.get("user-agent"),
            ip: request.headers.get("cf-connecting-ip")
          }, 200, { "X-Request-Id": requestId });

        case "/api/echo":
          if (method !== "POST") return jsonResponse({ error: "Method not allowed. Please use POST." }, 405);
          const body = await request.json().catch(() => ({}));
          return jsonResponse({ received: body, method, requestId }, 200, { "X-Request-Id": requestId });

        default:
          return jsonResponse({ error: "Endpoint not found", requestId }, 404, { "X-Request-Id": requestId });
      }
    } catch (error: any) {
      return jsonResponse({ error: "Internal Server Error", requestId }, 500, { "X-Request-Id": requestId });
    }
  },
};