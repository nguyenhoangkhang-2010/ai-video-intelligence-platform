import { api } from "@/lib/axios";
import type { ProcessingJob } from "@/types/processing";

export async function listProcessingJobs(): Promise<ProcessingJob[]> {
  const { data } = await api.get<ProcessingJob[]>("/processing-jobs");
  return data;
}

export async function getProcessingJob(jobId: number): Promise<ProcessingJob> {
  const { data } = await api.get<ProcessingJob>(`/processing-jobs/${jobId}`);
  return data;
}
