/**
 * Matches backend app/schemas/translation.py. The processing
 * pipeline currently always targets English — there is no
 * language-selection capability to expose.
 */

export interface Translation {
  id: number;
  video_id: number;
  language: string;
  subtitle: string;
  created_at: string;
}
