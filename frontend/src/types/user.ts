/** Matches backend app/schemas/user.py. */

export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** GET /users/me returns a hand-built subset, not the full UserRead. */
export interface CurrentUser {
  id: number;
  username: string;
  email: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}
