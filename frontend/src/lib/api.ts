export const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
export const ACTIVE_BUSINESS_STORAGE_KEY = "billyin-active-business";

export type TenantSummary = {
  tenant_id: number;
  tenant__name: string;
  role: string;
};

export type AuthSession = {
  detail?: string;
  user: {
    id: number;
    username: string;
    email: string;
    is_staff: boolean;
  };
  tenants: TenantSummary[];
};

export function getCsrfToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

export function getStoredActiveBusiness(): { id: number; name: string } | null {
  if (typeof window === "undefined") return null;

  try {
    const raw = window.localStorage.getItem(ACTIVE_BUSINESS_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { id?: number; name?: string };
    if (!parsed.id || !parsed.name) return null;
    return { id: parsed.id, name: parsed.name };
  } catch {
    window.localStorage.removeItem(ACTIVE_BUSINESS_STORAGE_KEY);
    return null;
  }
}

export function setStoredActiveBusiness(business: { id: number; name: string } | null): void {
  if (typeof window === "undefined") return;
  if (!business) {
    window.localStorage.removeItem(ACTIVE_BUSINESS_STORAGE_KEY);
    return;
  }
  window.localStorage.setItem(ACTIVE_BUSINESS_STORAGE_KEY, JSON.stringify(business));
}

export async function ensureCsrfCookie(): Promise<void> {
  if (typeof window === "undefined") return;
  const existing = getCsrfToken();
  if (existing) return;

  try {
    await fetch(`${API_BASE_URL}/api/v1/auth/me`, { credentials: "include" });
  } catch {
    // No-op; a later authenticated request will handle the real CSRF flow.
  }
}

export async function fetchJson<T>(input: string, init: RequestInit = {}): Promise<T> {
  const normalizedInput = input.replace(/\/+$/, "");
  const requestUrl = normalizedInput.startsWith("http") ? normalizedInput : `${API_BASE_URL}${normalizedInput}`;
  const headers = new Headers(init.headers ?? {});
  if (!(init.body instanceof FormData) && !headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  const csrfToken = getCsrfToken();
  if (csrfToken) {
    headers.set("X-CSRFToken", csrfToken);
  }

  const response = await fetch(requestUrl, {
    ...init,
    headers,
    credentials: "include",
  });

  if (!response.ok) {
    const contentType = response.headers.get("content-type") ?? "";
    const payload = contentType.includes("application/json") ? await response.json() : await response.text();
    const detail = typeof payload === "string" ? payload : payload?.detail ?? payload?.non_field_errors ?? "Request failed.";
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
