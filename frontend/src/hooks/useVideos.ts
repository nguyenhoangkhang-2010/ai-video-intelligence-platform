import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as videosService from "@/services/videos";
import { isTerminalVideoStatus, PROCESSING_POLL_INTERVAL_MS } from "@/lib/constants";
import type { Video } from "@/types/video";

export const videoKeys = {
  all: ["videos"] as const,
  list: () => [...videoKeys.all, "list"] as const,
  detail: (id: number) => [...videoKeys.all, "detail", id] as const,
  status: (id: number) => [...videoKeys.all, "status", id] as const,
  jobs: (id: number) => [...videoKeys.all, "jobs", id] as const,
};

/**
 * Polls while any video in the list hasn't reached a terminal status
 * yet, stopping once every video has (processed or failed) - the same
 * pattern useVideo below uses for a single video. Without this, a
 * video that finishes processing (and gets its real thumbnail) while
 * the person is sitting on /library would never visibly update until
 * they navigated away and back.
 */
export function useVideos() {
  return useQuery({
    queryKey: videoKeys.list(),
    queryFn: videosService.listVideos,
    refetchInterval: (query) => {
      const videos = query.state.data;
      if (!videos) return false;
      const stillProcessing = videos.some((video) => !isTerminalVideoStatus(video.status));
      return stillProcessing ? PROCESSING_POLL_INTERVAL_MS : false;
    },
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
      return isTerminalVideoStatus(status) ? false : PROCESSING_POLL_INTERVAL_MS;
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
