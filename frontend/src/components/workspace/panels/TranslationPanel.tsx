"use client";

import { useMemo, useState } from "react";

import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { Highlight } from "@/components/ui/Highlight";
import { Icon } from "@/components/ui/Icon";
import { ProcessingState } from "@/components/ui/ProcessingState";
import { Skeleton } from "@/components/ui/Spinner";
import { PanelHeader } from "@/components/workspace/PanelHeader";
import { useTranscript } from "@/hooks/useTranscript";
import { useTranslations } from "@/hooks/useTranslations";
import { toApiError } from "@/lib/axios";
import { isTerminalVideoStatus } from "@/lib/constants";
import type { VideoStatus } from "@/types/video";

/**
 * The processing pipeline currently only ever produces an English
 * translation (see docs/api/rest_api.md, Translation section) — no
 * language selector is shown since there is nothing to select
 * between. `subtitle` is plain translated prose, not real SRT-cue
 * content - confirmed by reading the actual generator (Translator
 * .translate() in ai/translation/translator.py sends the whole
 * transcript to the LLM asking for "the translated text, with no
 * commentary, labels, or explanation" - no timing markers are ever
 * requested or produced). It's rendered as ordinary reading prose,
 * not a monospace/code block implying a structured format that isn't
 * actually there, and no per-segment timestamp is shown since none
 * exists in this data.
 *
 * Reads the real transcript alongside the translation for an honest
 * source/translation reading pair — NOT a synchronized, line-by-line
 * aligner (the API gives no per-segment mapping between the two).
 */
export function TranslationPanel({ videoId, videoStatus }: { videoId: number; videoStatus: VideoStatus }) {
  const translations = useTranslations(videoId, videoStatus);
  const transcript = useTranscript(videoId, videoStatus);
  const [copied, setCopied] = useState(false);
  const [filter, setFilter] = useState("");

  const translation = translations.data?.[0];

  const matchCount = useMemo(() => {
    const trimmed = filter.trim().toLowerCase();
    if (!trimmed || !translation) return 0;
    return translation.subtitle.toLowerCase().split(trimmed).length - 1;
  }, [translation, filter]);

  if (translations.isLoading) {
    return (
      <div className="flex flex-col gap-3 p-5">
        <Skeleton className="h-4 w-1/3" />
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-4 w-full" />
        ))}
      </div>
    );
  }

  if (translations.isError) {
    return <ErrorState error={toApiError(translations.error)} onRetry={() => translations.refetch()} compact />;
  }

  if (!translation) {
    if (!isTerminalVideoStatus(videoStatus)) {
      return (
        <ProcessingState
          icon="translate"
          title="Translation is being generated…"
          description="This updates automatically the moment it's ready — no need to refresh."
        />
      );
    }
    return (
      <EmptyState
        icon="translate"
        title="No translation available"
        description="Processing finished without producing an English translation for this video."
      />
    );
  }

  async function handleCopy() {
    if (!translation) return;
    try {
      await navigator.clipboard.writeText(translation.subtitle);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      // Clipboard access can be denied by the browser — silently no-op,
      // the text is still fully visible and selectable in the panel.
    }
  }

  const hasSource = Boolean(transcript.data?.text);

  return (
    <div className="flex h-full flex-col">
      <PanelHeader
        icon="translate"
        label="Bilingual reading"
        meta={<span className="uppercase tracking-wide">{translation.language}</span>}
        actions={
          <>
            <div className="relative">
              <Icon
                name="search"
                size={13}
                className="pointer-events-none absolute left-2 top-1/2 -translate-y-1/2 text-text-muted"
              />
              <input
                type="text"
                value={filter}
                onChange={(event) => setFilter(event.target.value)}
                placeholder="Find in translation"
                aria-label="Find in translation"
                className="h-7 w-40 rounded border border-border-strong bg-surface-sunken pl-7 pr-2 text-caption text-text-primary placeholder:text-text-muted transition-colors duration-fast focus-visible:outline-2 focus-visible:outline-accent"
              />
            </div>
            {filter.trim() && (
              <span className="whitespace-nowrap text-caption text-text-muted">
                {matchCount} match{matchCount === 1 ? "" : "es"}
              </span>
            )}
            <button
              type="button"
              onClick={handleCopy}
              className="flex items-center gap-1.5 rounded border border-border-strong bg-surface-elevated px-2.5 py-1 text-caption font-medium text-text-secondary transition-colors duration-fast hover:border-accent hover:text-accent"
            >
              <Icon name={copied ? "check" : "copy"} size={12} />
              {copied ? "Copied" : "Copy"}
            </button>
          </>
        }
      />

      <div className="flex-1 overflow-hidden">
        {hasSource ? (
          <div className="grid h-full grid-cols-1 divide-y divide-border overflow-y-auto lg:grid-cols-2 lg:divide-x lg:divide-y-0 lg:overflow-hidden">
            <div className="overflow-y-auto px-6 py-5 lg:h-full">
              <p className="sticky top-0 mb-3 text-label font-semibold uppercase tracking-[0.12em] text-text-muted">
                Original
                {transcript.data && <span className="ml-1.5 text-text-disabled">· {transcript.data.language}</span>}
              </p>
              <p className="max-w-[60ch] whitespace-pre-wrap text-body-lg leading-[1.75] text-text-secondary">
                {transcript.data!.text}
              </p>
            </div>
            <div className="overflow-y-auto px-6 py-5 lg:h-full">
              <p className="sticky top-0 mb-3 text-label font-semibold uppercase tracking-[0.12em] text-atmosphere">
                English translation
              </p>
              <p className="max-w-[60ch] whitespace-pre-wrap text-body-lg leading-[1.75] text-text-secondary">
                <Highlight text={translation.subtitle} query={filter} />
              </p>
            </div>
          </div>
        ) : (
          <div className="h-full overflow-y-auto px-6 py-5">
            <p className="sticky top-0 mb-3 text-label font-semibold uppercase tracking-[0.12em] text-atmosphere">
              English translation
            </p>
            <p className="mx-auto max-w-[68ch] whitespace-pre-wrap text-body-lg leading-[1.75] text-text-secondary">
              <Highlight text={translation.subtitle} query={filter} />
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
