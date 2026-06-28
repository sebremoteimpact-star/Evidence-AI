/**
 * Cliente HTTP base hacia el backend FastAPI.
 * Maneja token JWT desde localStorage, errores RFC 7807, retries básicos.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const TOKEN_KEY = "evidence_ai_access_token";
const REFRESH_KEY = "evidence_ai_refresh_token";

export class ApiError extends Error {
  constructor(
    public status: number,
    public title: string,
    public detail: string,
    public type: string = "about:blank",
    public errors?: unknown,
  ) {
    super(`${title}: ${detail}`);
  }
}

export const tokenStorage = {
  get: (): string | null =>
    typeof window === "undefined" ? null : localStorage.getItem(TOKEN_KEY),
  getRefresh: (): string | null =>
    typeof window === "undefined" ? null : localStorage.getItem(REFRESH_KEY),
  set: (access: string, refresh: string) => {
    localStorage.setItem(TOKEN_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

async function request<T>(
  path: string,
  options: RequestInit & { auth?: boolean } = {},
): Promise<T> {
  const { auth = true, headers, ...rest } = options;

  const finalHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...(headers as Record<string, string>),
  };

  if (auth) {
    const token = tokenStorage.get();
    if (token) finalHeaders.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, { ...rest, headers: finalHeaders });

  if (!res.ok) {
    let body: any = {};
    try {
      body = await res.json();
    } catch {
      body = { title: res.statusText, detail: "Error desconocido" };
    }
    throw new ApiError(
      res.status,
      body.title ?? "Error",
      body.detail ?? "Error desconocido",
      body.type,
      body.errors,
    );
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string, opts?: { auth?: boolean }) =>
    request<T>(path, { method: "GET", ...opts }),
  post: <T>(path: string, body?: unknown, opts?: { auth?: boolean }) =>
    request<T>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
      ...opts,
    }),
  apiUrl: API_URL,
};
