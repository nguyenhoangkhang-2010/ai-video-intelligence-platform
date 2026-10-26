import { api } from "@/lib/axios";
import { API_V1_URL } from "@/lib/constants";
import type { ProcessingJob } from "@/types/processing";
import type { MediaTokenResponse, Video, VideoStatusResponse, VideoUpdatePayload } from "@/types/video";

export async function listVideos(): Promise<Video[]> {
  const { data } = await api.get<Video[]>("/videos");
  return data;
}

export async function getVideo(videoId: number): Promise<Video> {
  const { data } = await api.get<Video>(`/videos/${videoId}`);
  return data;
}

export async function getVideoStatus(videoId: number): Promise<VideoStatusResponse> {
  const { data } = await api.get<VideoStatusResponse>(`/videos/${videoId}/status`);
  return data;
}

export async function getVideoProcessingJobs(videoId: number): Promise<ProcessingJob[]> {
  const { data } = await api.get<ProcessingJob[]>(`/videos/${videoId}/processing-jobs`);
  return data;
}

export async function updateVideo(videoId: number, payload: VideoUpdatePayload): Promise<Video> {
  const { data } = await api.put<Video>(`/videos/${videoId}`, payload);
  return data;
}

export async function deleteVideo(videoId: number): Promise<void> {
  await api.delete(`/videos/${videoId}`);
}

export interface UploadVideoOptions {
  onProgress?: (percent: number) => void;
  signal?: AbortSignal;
}

export async function uploadVideo(file: File, options: UploadVideoOptions = {}): Promise<Video> {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await api.post<Video>("/videos/upload", formData, {
    signal: options.signal,
    onUploadProgress: (event) => {
      if (!options.onProgress || !event.total) return;
      options.onProgress(Math.round((event.loaded / event.total) * 100));
    },
  });
  return data;
}

/**
 * Short-lived, video-scoped token for the media endpoints below (see
 * backend app/auth/jwt.py::create_media_token). Never the caller's own
 * long-lived access token — that token is never placed in a URL.
 */
export async function getMediaToken(videoId: number): Promise<MediaTokenResponse> {
  const { data } = await api.get<MediaTokenResponse>(`/videos/${videoId}/media-token`);
  return data;
}

/**
 * Playback URL for the native <video> element. `mediaToken` is passed
 * as a query parameter because a browser media element cannot attach
 * an Authorization header — this is the one endpoint that accepts
 * that (see backend app/auth/dependencies.py::get_current_user_for_media
 * and docs/api/rest_api.md). Callers must fetch the token via
 * getMediaToken/useMediaToken first — it is never the main access
 * token.
 */
export function getVideoStreamUrl(videoId: number, mediaToken: string): string {
  const url = new URL(`${API_V1_URL}/videos/${videoId}/stream`);
  url.searchParams.set("token", mediaToken);
  return url.toString();
}

/**
 * URL for this video's real, ffmpeg-extracted representative frame.
 * Same scoped-media-token-as-query-param pattern as getVideoStreamUrl,
 * since an <img> element can't attach an Authorization header either
 * (see backend app/auth/dependencies.py::get_current_user_for_media).
 *
 * Callers must gate rendering on `video.has_thumbnail` - this always
 * returns a URL, but the server 404s if no frame was extracted (still
 * processing, or extraction failed), so this is only meant to be used
 * once has_thumbnail is true.
 */
export function getVideoThumbnailUrl(videoId: number, mediaToken: string): string {
  const url = new URL(`${API_V1_URL}/videos/${videoId}/thumbnail`);
  url.searchParams.set("token", mediaToken);
  return url.toString();
}
