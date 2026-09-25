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
