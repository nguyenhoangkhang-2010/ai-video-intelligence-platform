import { AxiosError, AxiosHeaders } from "axios";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { NovaAttentionProvider } from "@/components/3d/NovaAttentionContext";
import { AuthProvider } from "@/hooks/useAuth";
import * as authService from "@/services/auth";

import LoginPage from "./page";

/**
 * Login is the one journey every other page depends on - if this
 * breaks, nothing else in the product is reachable. These tests cover
 * the real golden path (credentials in, redirect to /library) and the
 * two failure modes a person actually hits (empty fields, wrong
 * credentials), through the real AuthProvider/useAuth - only the HTTP
 * layer (@/services/auth) and next/navigation are mocked.
 */
vi.mock("@/services/auth");

const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

function axiosErrorWithResponse(status: number, data: unknown): AxiosError {
  const error = new AxiosError("Request failed", String(status));
  error.response = {
    status,
    data,
    statusText: "",
    headers: {},
    config: { headers: new AxiosHeaders() },
  };
  return error;
}

function renderLoginPage() {
  return render(
    <NovaAttentionProvider>
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    </NovaAttentionProvider>,
  );
}

describe("LoginPage", () => {
  beforeEach(() => {
    vi.mocked(authService.login).mockReset();
    vi.mocked(authService.getCurrentUser).mockReset();
    pushMock.mockReset();
    // AuthProvider's mount effect checks for a stored token (see
    // lib/token.ts) and calls getCurrentUser() if one exists - the
    // successful-login test below stores a real one via setToken(),
    // which would otherwise leak into the next test's initial render.
    window.localStorage.clear();
  });

  it("shows validation errors and never calls the API when submitted empty", async () => {
    const user = userEvent.setup();
    renderLoginPage();

    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
    expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    expect(authService.login).not.toHaveBeenCalled();
  });

  it("logs in with valid credentials and redirects to the library", async () => {
    vi.mocked(authService.login).mockResolvedValue({
      access_token: "a-real-looking-token",
      token_type: "bearer",
    });
    vi.mocked(authService.getCurrentUser).mockResolvedValue({
      id: 1,
      username: "alice",
      email: "alice@example.com",
    });

    const user = userEvent.setup();
    renderLoginPage();

    await user.type(screen.getByLabelText(/^email$/i), "alice@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "correct-password");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(authService.login).toHaveBeenCalledWith({
        email: "alice@example.com",
        password: "correct-password",
      });
    });
    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/library"));
  });

  it("shows the server's real error message on wrong credentials, without redirecting", async () => {
    vi.mocked(authService.login).mockRejectedValue(
      axiosErrorWithResponse(401, { detail: "Incorrect email or password" }),
    );

    const user = userEvent.setup();
    renderLoginPage();

    await user.type(screen.getByLabelText(/^email$/i), "alice@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "wrong-password");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/incorrect email or password/i);
    expect(pushMock).not.toHaveBeenCalled();
  });
});
