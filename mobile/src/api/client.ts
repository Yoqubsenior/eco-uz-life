import { API_URL, REQUEST_TIMEOUT_MS } from "@/lib/config";
import { clearTokens, getAccessToken, getRefreshToken, saveTokens, type Tokens } from "@/lib/tokens";

/** Any non-2xx answer from the API. `body` holds DRF's error JSON, e.g. {"email": ["..."]}. */
export class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown,
  ) {
    super(`API error ${status}`);
  }
}

/** The request never got an HTTP answer (no network, server down, timeout). */
export class NetworkError extends Error {}

// ---------- Session-expired notifications (AuthProvider listens) ----------

type Listener = () => void;
const sessionExpiredListeners = new Set<Listener>();

export function onSessionExpired(listener: Listener): () => void {
  sessionExpiredListeners.add(listener);
  return () => sessionExpiredListeners.delete(listener);
}

// ---------- Token refresh (single-flight) ----------

/**
 * The backend ROTATES refresh tokens: each refresh returns a new one and blacklists the old.
 * If three requests get 401 at the same time and each starts its own refresh, the first
 * succeeds and the other two send an already-blacklisted token -> the user is logged out.
 * So all callers share ONE in-flight refresh promise.
 */
let refreshInFlight: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      const refresh = await getRefreshToken();
      if (!refresh) return null;
      try {
        const res = await fetchWithTimeout(`${API_URL}/auth/refresh/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh }),
        });
        if (!res.ok) throw new ApiError(res.status, null);
        const tokens = (await res.json()) as Tokens;
        await saveTokens(tokens);
        return tokens.access;
      } catch (error) {
        if (error instanceof ApiError) {
          // Refresh token expired or blacklisted: the session is really over.
          await clearTokens();
          sessionExpiredListeners.forEach((listener) => listener());
        }
        return null;
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  return refreshInFlight;
}

// ---------- Core request ----------

async function fetchWithTimeout(url: string, init: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } catch {
    throw new NetworkError("Network request failed");
  } finally {
    clearTimeout(timer);
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown; // plain object -> JSON; FormData -> multipart
  query?: Record<string, string | number | undefined>;
  auth?: boolean; // attach the access token if we have one (default true)
};

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, query, auth = true } = options;

  // Built by hand: React Native's URLSearchParams is only partially implemented.
  const queryString = Object.entries(query ?? {})
    .filter(([, value]) => value !== undefined)
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
    .join("&");
  const url = `${API_URL}${path}${queryString ? `?${queryString}` : ""}`;

  const isForm = body instanceof FormData;

  const send = async (accessToken: string | null) => {
    const headers: Record<string, string> = { Accept: "application/json" };
    // For FormData, let fetch set Content-Type itself: it must include the multipart boundary.
    if (body !== undefined && !isForm) headers["Content-Type"] = "application/json";
    if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
    return fetchWithTimeout(url, {
      method,
      headers,
      body: body === undefined ? undefined : isForm ? (body as FormData) : JSON.stringify(body),
    });
  };

  const token = auth ? await getAccessToken() : null;
  let res = await send(token);

  // Access token expired (15 min lifetime): refresh once, then retry the same request.
  if (res.status === 401 && token) {
    const newToken = await refreshAccessToken();
    if (newToken) res = await send(newToken);
  }

  const data = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, data);
  return data as T;
}
