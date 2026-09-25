/** Matches backend app/schemas/processing_job.py. */

export type ProcessingJobStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";

export interface ProcessingJob {
  id: number;
  video_id: number;
  job_type: string;
  status: ProcessingJobStatus;
  progress: number;
  current_step: string | null;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
}
