"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";

import { useNovaAttention } from "@/components/3d/NovaAttentionContext";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import { toApiError } from "@/lib/axios";
import { ROUTES } from "@/lib/constants";
import { validateEmail, validatePassword, validateUsername } from "@/lib/validation";

interface FieldErrors {
  username?: string;
  email?: string;
  password?: string;
}

export default function RegisterPage() {
  const { register } = useAuth();
  const { notice } = useNovaAttention();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    const errors: FieldErrors = {
      username: validateUsername(username) ?? undefined,
      email: validateEmail(email) ?? undefined,
      password: validatePassword(password) ?? undefined,
    };
    setFieldErrors(errors);
    if (errors.username || errors.email || errors.password) return;

    setFormError(null);
    setIsSubmitting(true);
    notice("thinking");
    try {
      await register({ username, email, password });
      notice("excited", 1000);
    } catch (error) {
      const apiError = toApiError(error);
      if (apiError.fieldErrors) {
        const mapped: FieldErrors = {};
        for (const fieldError of apiError.fieldErrors) {
          if (fieldError.field in errors) {
            (mapped as Record<string, string>)[fieldError.field] = fieldError.message;
          }
        }
        setFieldErrors(mapped);
      }
      setFormError(apiError.message);
      notice("idle");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div>
      <h1 className="font-display text-heading-lg font-semibold text-text-primary">Create your account</h1>
      <p className="mt-1.5 text-body-sm text-text-muted">Start turning footage into searchable knowledge.</p>

      <form onSubmit={handleSubmit} noValidate className="mt-7 flex flex-col gap-4">
        <Input
          label="Username"
          autoComplete="username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          onFocus={() => notice("attention", 1200)}
          error={fieldErrors.username}
        />
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
          autoComplete="new-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          onFocus={() => notice("attention", 1200)}
          error={fieldErrors.password}
          hint={!fieldErrors.password ? "At least 8 characters." : undefined}
        />

        {formError && (
          <p role="alert" className="rounded border border-error/30 bg-error-muted px-3 py-2 text-body-sm text-error">
            {formError}
          </p>
        )}

        <Button type="submit" isLoading={isSubmitting} fullWidth className="mt-1">
          Create account
        </Button>
      </form>

      <p className="mt-6 text-center text-body-sm text-text-muted">
        Already have an account?{" "}
        <Link href={ROUTES.login} className="font-medium text-accent hover:text-accent-hover">
          Sign in
        </Link>
      </p>
    </div>
  );
}
