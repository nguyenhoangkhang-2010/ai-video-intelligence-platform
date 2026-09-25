/**
 * Matches backend app/schemas/summary.py. `type` is currently always
 * "default" — only one summarization strategy is implemented
 * backend-side, so no summary-type picker exists in the UI.
 */

export interface Summary {
  id: number;
  video_id: number;
  type: string;
  content: string;
  model_name: string;
  created_at: string;
}
