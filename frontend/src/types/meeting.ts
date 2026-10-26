import type { ProcessingJob } from "@/types/processing";
import type { Quiz } from "@/types/quiz";
import type { Summary } from "@/types/summary";
import type { Transcript } from "@/types/transcript";
import type { Translation } from "@/types/translation";
import type { Video } from "@/types/video";

/**
 * Matches backend app/schemas/meeting.py::MeetingResponse. Does not
 * include chapters/flashcards (added to the API after this aggregate
 * was last touched) — those are fetched separately.
 */
export interface MeetingResponse {
  video: Video;
  processing_jobs: ProcessingJob[];
  transcript: Transcript | null;
  summaries: Summary[];
  translations: Translation[];
  quizzes: Quiz[];
}
