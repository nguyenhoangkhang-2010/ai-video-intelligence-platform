import { api } from "@/lib/axios";
import type { Flashcard } from "@/types/flashcard";

export async function getFlashcards(videoId: number): Promise<Flashcard[]> {
  const { data } = await api.get<Flashcard[]>(`/videos/${videoId}/flashcards`);
  return data;
}

/**
 * Downloads the Anki-importable UTF-8 TSV export (see
 * docs/api/rest_api.md, Flashcards section) and triggers a browser
 * save via a temporary object URL — no server-side file dialog exists,
 * this is purely a client-side file save of the response body.
 */
export async function exportFlashcardsToAnki(videoId: number): Promise<void> {
  const response = await api.get(`/videos/${videoId}/flashcards/export`, {
    responseType: "blob",
  });

  const disposition = response.headers["content-disposition"] as string | undefined;
  const filenameMatch = disposition?.match(/filename="?([^"]+)"?/);
  const filename = filenameMatch?.[1] ?? `video-${videoId}-flashcards.tsv`;

  const url = window.URL.createObjectURL(response.data as Blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
