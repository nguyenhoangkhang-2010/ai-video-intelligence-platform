/** Matches backend app/schemas/video.py. */

/** Video.status lifecycle: uploaded -> processing -> processed | failed. */
export type VideoStatus = "uploaded" | "processing" | "processed" | "failed";

export interface Video {
  id: number;
  owner_id: number;
  title: string;
  filename: string;
  language: string;
  duration: number;
  status: VideoStatus;
  /**
   * Whether a representative frame was extracted for this video (see
   * backend app/utils/thumbnail.py). Never the storage key itself -
   * true means getVideoThumbnailUrl(id) will resolve to a real image;
   * false means it's still processing (status === "processing") or
   * extraction failed (status is "processed"/"failed" but there's no
   * frame), which callers must render differently.
   */
  has_thumbnail: boolean;
  created_at: string;
  updated_at: string;
}

export interface VideoStatusResponse {
  id: number;
  status: VideoStatus;
}

export interface VideoUpdatePayload {
  title?: string;
  language?: string;
  status?: VideoStatus;
}
