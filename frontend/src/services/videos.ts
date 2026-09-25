import { api } from "@/lib/axios";
import { API_V1_URL } from "@/lib/constants";
import { getToken } from "@/lib/token";
import type { ProcessingJob } from "@/types/processing";
import type { Video, VideoStatusResponse, VideoUpdatePayload } from "@/types/video";

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
 * Playback URL for the native <video> element. The token is passed as
 * a query parameter because a browser media element cannot attach an
 * Authorization header — this is the one endpoint that accepts that
 * (see backend app/auth/dependencies.py::get_current_user_for_media
 * and docs/api/rest_api.md).
 */
export function getVideoStreamUrl(videoId: number): string {
  const token = getToken();
  const url = new URL(`${API_V1_URL}/videos/${videoId}/stream`);
  if (token) url.searchParams.set("token", token);
  return url.toString();
}
