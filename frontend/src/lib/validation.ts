/** Small, dependency-free client-side validation helpers for the auth forms. */

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateEmail(value: string): string | null {
  if (!value.trim()) return "Email is required.";
  if (!EMAIL_PATTERN.test(value)) return "Enter a valid email address.";
  return null;
}

export function validateUsername(value: string): string | null {
  if (!value.trim()) return "Username is required.";
  if (value.trim().length < 3) return "Username must be at least 3 characters.";
  return null;
}

export function validatePassword(value: string): string | null {
  if (!value) return "Password is required.";
  if (value.length < 8) return "Password must be at least 8 characters.";
  return null;
}

export function validateLoginPassword(value: string): string | null {
  if (!value) return "Password is required.";
  return null;
}
