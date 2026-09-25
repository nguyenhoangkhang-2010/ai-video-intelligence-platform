"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";

import { useNovaAttention } from "@/components/3d/NovaAttentionContext";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import { toApiError } from "@/lib/axios";
import { ROUTES } from "@/lib/constants";
import { validateEmail, validateLoginPassword } from "@/lib/validation";

export default function LoginPage() {
  const { login } = useAuth();
  const { notice } = useNovaAttention();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    const emailError = validateEmail(email);
    const passwordError = validateLoginPassword(password);
    setFieldErrors({ email: emailError ?? undefined, password: passwordError ?? undefined });
    if (emailError || passwordError) return;

    setFormError(null);
    setIsSubmitting(true);
    notice("thinking");
    try {
      await login({ email, password });
      // A brief acknowledgement before the redirect to /library actually
      // happens (useAuth drives that navigation) - Nova visibly reacts
      // to the real outcome rather than the page just vanishing.
      notice("excited", 1000);
    } catch (error) {
      setFormError(toApiError(error).message);
      notice("idle");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div>
      <h1 className="font-display text-heading-lg font-semibold text-text-primary">Welcome back</h1>
      <p className="mt-1.5 text-body-sm text-text-muted">Sign in to continue to your workspace.</p>

      <form onSubmit={handleSubmit} noValidate className="mt-7 flex flex-col gap-4">
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          onFocus={() => notice("attention", 1200)}
          error={fieldErrors.email}
        />
        <Input
          label="Password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          onFocus={() => notice("attention", 1200)}
          error={fieldErrors.password}
        />

        {formError && (
          <p role="alert" className="rounded border border-error/30 bg-error-muted px-3 py-2 text-body-sm text-error">
            {formError}
          </p>
        )}

        <Button type="submit" isLoading={isSubmitting} fullWidth className="mt-1">
          Sign in
        </Button>
      </form>

      <p className="mt-6 text-center text-body-sm text-text-muted">
        Don&apos;t have an account?{" "}
        <Link href={ROUTES.register} className="font-medium text-accent hover:text-accent-hover">
          Create one
        </Link>
      </p>
    </div>
  );
}
