/** Shared, framework-agnostic formatting/utility helpers used across the app. */

/** Minimal className combiner — filters falsy values, no external dependency. */
export function cn(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}

/** Formats whole seconds as `m:ss` or `h:mm:ss` (video duration, timestamps). */
export function formatTimecode(totalSeconds: number): string {
  if (!Number.isFinite(totalSeconds) || totalSeconds < 0) return "0:00";

  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = Math.floor(totalSeconds % 60);

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  }
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

/** Formats an ISO date string as an absolute, locale-aware date + time. */
export function formatDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

/** Formats an ISO date string as a short relative time ("3m ago", "2d ago"). */
export function formatRelativeTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";

  const diffMs = date.getTime() - Date.now();
  const diffSeconds = Math.round(diffMs / 1000);
  const abs = Math.abs(diffSeconds);

  const units: Array<[Intl.RelativeTimeFormatUnit, number]> = [
    ["year", 31536000],
    ["month", 2592000],
    ["week", 604800],
    ["day", 86400],
    ["hour", 3600],
    ["minute", 60],
    ["second", 1],
  ];

  const rtf = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });

  for (const [unit, secondsInUnit] of units) {
    if (abs >= secondsInUnit || unit === "second") {
      const value = Math.round(diffSeconds / secondsInUnit);
      return rtf.format(value, unit);
    }
  }
  return "just now";
}

/** Formats a byte count as a human-readable size (upload file sizes). */
export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const exponent = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1,
  );
  const value = bytes / 1024 ** exponent;
  return `${exponent === 0 ? value : value.toFixed(1)} ${units[exponent]}`;
}

/** Formats an integer word count with locale-aware thousands separators. */
export function formatNumber(value: number): string {
  return new Intl.NumberFormat(undefined).format(value);
}

/** Truncates text to `maxLength` characters, breaking on a word boundary. */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  const cut = text.slice(0, maxLength);
  const lastSpace = cut.lastIndexOf(" ");
  return `${cut.slice(0, lastSpace > 0 ? lastSpace : maxLength)}…`;
}

/** Human-readable label for a Video.status value. */
export function videoStatusLabel(status: string): string {
  switch (status) {
    case "uploaded":
      return "Uploaded";
    case "processing":
      return "Processing";
    case "processed":
      return "Ready";
    case "failed":
      return "Failed";
    default:
      return status;
  }
}

/** Human-readable label for a ProcessingJob.status value. */
export function jobStatusLabel(status: string): string {
  switch (status) {
    case "PENDING":
      return "Queued";
    case "RUNNING":
      return "Running";
    case "COMPLETED":
      return "Completed";
    case "FAILED":
      return "Failed";
    default:
      return status;
  }
}

/** Human-readable label for a Quiz.type value. */
export function quizTypeLabel(type: string): string {
  switch (type) {
    case "multiple_choice":
      return "Multiple choice";
    case "true_false":
      return "True / False";
    case "short_answer":
      return "Short answer";
    default:
      return type;
  }
}

/** Splits a comma-joined Quiz.options string into individual options. */
export function parseQuizOptions(options: string | null): string[] {
  if (!options) return [];
  return options
    .split(",")
    .map((option) => option.trim())
    .filter(Boolean);
}
