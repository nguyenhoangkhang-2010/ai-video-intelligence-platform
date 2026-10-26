import { api } from "@/lib/axios";
import type { ProcessingJob } from "@/types/processing";

export async function listProcessingJobs(): Promise<ProcessingJob[]> {
  const { data } = await api.get<ProcessingJob[]>("/processing-jobs");
  return data;
}

/**
 * POST /processing-jobs/{id}/retry - re-dispatches a FAILED job; stages
 * that already completed are skipped server-side. 409 if the job isn't
 * FAILED (e.g. a double click already claimed it).
 */
export async function retryProcessingJob(jobId: number): Promise<ProcessingJob> {
  const { data } = await api.post<ProcessingJob>(`/processing-jobs/${jobId}/retry`);
  return data;
}

export async function getProcessingJob(jobId: number): Promise<ProcessingJob> {
  const { data } = await api.get<ProcessingJob>(`/processing-jobs/${jobId}`);
  return data;
}
