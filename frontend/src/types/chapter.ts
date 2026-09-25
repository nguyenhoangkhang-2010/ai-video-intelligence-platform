/** Matches backend app/schemas/chapter.py. Ordered by start_time by the API. */

export interface Chapter {
  id: number;
  video_id: number;
  title: string;
  start_time: number;
  end_time: number;
  summary: string | null;
}
