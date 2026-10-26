import { api } from "@/lib/axios";
import { API_V1_URL } from "@/lib/constants";
import type { VisualSegment } from "@/types/visual";

export async function getVisualSegments(videoId: number): Promise<VisualSegment[]> {
  const { data } = await api.get<VisualSegment[]>(`/videos/${videoId}/visual-segments`);
  return data;
}

/**
 * URL of a visual segment's keyframe. Same scoped media-token query
 * param as getVideoThumbnailUrl, since an <img> can't send headers.
 * Only meaningful when the segment's `has_frame` is true.
 */
export function getVisualFrameUrl(videoId: number, segmentId: number, mediaToken: string): string {
  const url = new URL(`${API_V1_URL}/videos/${videoId}/visual-segments/${segmentId}/frame`);
  url.searchParams.set("token", mediaToken);
  return url.toString();
}
