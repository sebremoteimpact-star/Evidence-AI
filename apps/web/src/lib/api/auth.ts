import { apiClient, tokenStorage } from "./client";

export interface User {
  id: string;
  email: string;
  name: string | null;
  locale: string;
  is_admin: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  access_expires_at: string;
  refresh_expires_at: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  name?: string;
  locale?: "es" | "en";
}

export const authApi = {
  async register(payload: RegisterPayload): Promise<{ user: User; tokens: TokenPair }> {
    const res = await apiClient.post<{ user: User; tokens: TokenPair }>(
      "/api/v1/auth/register",
      payload,
      { auth: false },
    );
    tokenStorage.set(res.tokens.access_token, res.tokens.refresh_token);
    return res;
  },

  async login(email: string, password: string): Promise<TokenPair> {
    const tokens = await apiClient.post<TokenPair>(
      "/api/v1/auth/login",
      { email, password },
      { auth: false },
    );
    tokenStorage.set(tokens.access_token, tokens.refresh_token);
    return tokens;
  },

  logout() {
    tokenStorage.clear();
  },

  isAuthenticated(): boolean {
    return tokenStorage.get() !== null;
  },
};
