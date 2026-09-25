import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as videosService from "@/services/videos";
import { TERMINAL_VIDEO_STATUSES, PROCESSING_POLL_INTERVAL_MS } from "@/lib/constants";
import type { Video } from "@/types/video";

export const videoKeys = {
  all: ["videos"] as const,
  list: () => [...videoKeys.all, "list"] as const,
  detail: (id: number) => [...videoKeys.all, "detail", id] as const,
  status: (id: number) => [...videoKeys.all, "status", id] as const,
  jobs: (id: number) => [...videoKeys.all, "jobs", id] as const,
};

export function useVideos() {
  return useQuery({
    queryKey: videoKeys.list(),
    queryFn: videosService.listVideos,
  });
}

/** Polls while the video is uploaded/processing; stops once processed/failed. */
export function useVideo(videoId: number) {
  return useQuery({
    queryKey: videoKeys.detail(videoId),
    queryFn: () => videosService.getVideo(videoId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (!status) return false;
      return TERMINAL_VIDEO_STATUSES.includes(status as "processed" | "failed")
        ? false
        : PROCESSING_POLL_INTERVAL_MS;
    },
  });
}

export function useVideoProcessingJobs(videoId: number, enabled = true) {
  return useQuery({
    queryKey: videoKeys.jobs(videoId),
    queryFn: () => videosService.getVideoProcessingJobs(videoId),
    enabled,
    refetchInterval: (query) => {
      const jobs = query.state.data;
      if (!jobs) return false;
      const stillActive = jobs.some((job) => job.status === "PENDING" || job.status === "RUNNING");
      return stillActive ? PROCESSING_POLL_INTERVAL_MS : false;
    },
  });
}

export function useDeleteVideo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (videoId: number) => videosService.deleteVideo(videoId),
    onSuccess: (_data, videoId) => {
      queryClient.setQueryData<Video[]>(videoKeys.list(), (current) =>
        current?.filter((video) => video.id !== videoId),
      );
    },
  });
}
