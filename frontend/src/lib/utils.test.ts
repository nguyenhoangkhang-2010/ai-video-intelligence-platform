import { describe, expect, it } from "vitest";

import {
  cn,
  formatBytes,
  formatTimecode,
  jobStatusLabel,
  parseQuizOptions,
  quizTypeLabel,
  truncate,
  videoStatusLabel,
} from "@/lib/utils";

describe("cn", () => {
  it("joins truthy class names and drops falsy ones", () => {
    expect(cn("a", false, "b", null, undefined, "c")).toBe("a b c");
  });
});

describe("formatTimecode", () => {
  it("formats sub-hour durations as m:ss", () => {
    expect(formatTimecode(0)).toBe("0:00");
    expect(formatTimecode(65)).toBe("1:05");
    expect(formatTimecode(599)).toBe("9:59");
  });

  it("formats hour-plus durations as h:mm:ss", () => {
    expect(formatTimecode(3661)).toBe("1:01:01");
  });

  it("never fabricates a timestamp for invalid input", () => {
    expect(formatTimecode(Number.NaN)).toBe("0:00");
    expect(formatTimecode(-5)).toBe("0:00");
    expect(formatTimecode(Number.POSITIVE_INFINITY)).toBe("0:00");
  });
});

describe("formatBytes", () => {
  it("scales through units", () => {
    expect(formatBytes(0)).toBe("0 B");
    expect(formatBytes(512)).toBe("512 B");
    expect(formatBytes(1536)).toBe("1.5 KB");
    expect(formatBytes(5 * 1024 * 1024)).toBe("5.0 MB");
  });
});

describe("truncate", () => {
  it("returns the original text when already short enough", () => {
    expect(truncate("hello", 10)).toBe("hello");
  });

  it("breaks on a word boundary rather than mid-word", () => {
    // Naive slicing at 12 chars would cut "the quick br" mid-word;
    // truncate must back up to the space before "br" instead.
    expect(truncate("the quick brown fox jumps", 12)).toBe("the quick…");
  });
});

describe("status label mappers", () => {
  it("maps every real Video.status value to a distinct human label", () => {
    expect(videoStatusLabel("uploaded")).toBe("Uploaded");
    expect(videoStatusLabel("processing")).toBe("Processing");
    expect(videoStatusLabel("processed")).toBe("Ready");
    expect(videoStatusLabel("failed")).toBe("Failed");
  });

  it("maps every real ProcessingJob.status value to a distinct human label", () => {
    expect(jobStatusLabel("PENDING")).toBe("Queued");
    expect(jobStatusLabel("RUNNING")).toBe("Running");
    expect(jobStatusLabel("COMPLETED")).toBe("Completed");
    expect(jobStatusLabel("FAILED")).toBe("Failed");
  });

  it("maps every real Quiz.type value to a distinct human label", () => {
    expect(quizTypeLabel("multiple_choice")).toBe("Multiple choice");
    expect(quizTypeLabel("true_false")).toBe("True / False");
    expect(quizTypeLabel("short_answer")).toBe("Short answer");
  });
});

describe("parseQuizOptions", () => {
  it("splits a comma-joined options string and trims whitespace", () => {
    expect(parseQuizOptions("A, B ,C")).toEqual(["A", "B", "C"]);
  });

  it("returns an empty array for null (true_false/short_answer questions)", () => {
    expect(parseQuizOptions(null)).toEqual([]);
  });
});
