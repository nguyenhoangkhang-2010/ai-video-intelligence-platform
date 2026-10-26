import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { NovaAttentionProvider } from "@/components/3d/NovaAttentionContext";
import { AuthProvider } from "@/hooks/useAuth";
import { AUTH_TOKEN_STORAGE_KEY } from "@/lib/constants";
import * as authService from "@/services/auth";

import AuthLayout from "./layout";

/**
 * Regression coverage for the gap found in the UX audit: an already-
 * signed-in visitor landing directly on /login or /register (stale
 * bookmark, browser back) used to just see the form again instead of
 * being sent to their library - the one place RequireAuth's own
 * symmetric behavior (redirect unauthenticated users OUT of protected
 * routes) didn't have a counterpart for authenticated users looking IN
 * at the auth routes. Only the HTTP layer and next/navigation are
 * mocked; AuthProvider/useAuth are real.
 */
vi.mock("@/services/auth");

const replaceMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock }),
}));

function renderAuthLayout() {
  return render(
    <NovaAttentionProvider>
      <AuthProvider>
        <AuthLayout>
          <div data-testid="auth-form">the login form</div>
        </AuthLayout>
      </AuthProvider>
    </NovaAttentionProvider>,
  );
}

describe("AuthLayout", () => {
  beforeEach(() => {
    vi.mocked(authService.getCurrentUser).mockReset();
    replaceMock.mockReset();
    window.localStorage.clear();
  });

  it("redirects an already-authenticated visitor to the library instead of showing the form", async () => {
    window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, "a-real-looking-token");
    vi.mocked(authService.getCurrentUser).mockResolvedValue({
      id: 1,
      username: "alice",
      email: "alice@example.com",
    });

    renderAuthLayout();

    await waitFor(() => expect(replaceMock).toHaveBeenCalledWith("/library"));
    expect(screen.queryByTestId("auth-form")).not.toBeInTheDocument();
  });

  it("renders the form normally for an unauthenticated visitor, with no redirect", async () => {
    renderAuthLayout();

    expect(await screen.findByTestId("auth-form")).toBeInTheDocument();
    expect(replaceMock).not.toHaveBeenCalled();
  });
});
