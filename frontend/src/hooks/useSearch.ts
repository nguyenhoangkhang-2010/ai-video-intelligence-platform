import { useMutation } from "@tanstack/react-query";

import * as searchService from "@/services/search";

export function useVideoSearch(videoId: number) {
  return useMutation({
    mutationFn: (query: string) => searchService.searchVideo(videoId, query),
  });
}
