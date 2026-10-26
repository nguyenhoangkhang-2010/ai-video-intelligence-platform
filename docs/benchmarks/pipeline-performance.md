# Video processing pipeline: where the time goes

**Finding:** on a CPU-only machine, about 94% of the time spent processing a
video goes to LLM generation, not to speech recognition. Two changes cut
end-to-end processing of the same 100-second video from **18m 42s to 8m 16s
(2.3× faster)**, with no new hardware and no smaller model:

1. turning off qwen3's hidden reasoning mode;
2. writing each chapter's title and summary in one LLM call instead of two.

The summary stage is left out of both totals; see [Limits](#limits).

## Setup

- **Hardware.** Intel Core 12th gen (Family 6 Model 154), 40 GB RAM, no GPU.
  Docker Desktop on WSL2. The Celery worker is limited to 8 CPUs and 7 GB.
- **Models.** faster-whisper `medium` (CPU, `int8`) and Ollama `qwen3:8b`
  (Q4_K_M), running on the host CPU.
- **Video.** The same 100-second Vietnamese clip (`source18.mp4`), uploaded
  twice on 2026-10-26:
  - video 20 ran on the code before these changes;
  - video 21 ran on the code after them.
- **Source of the numbers.** The pipeline's own records:
  `processing_stages.started_at` and `finished_at` for each video's latest job.
  Nothing was instrumented specially for this measurement.

Reproduce:

```bash
docker compose cp backend/scripts/report_stage_timings.py api:/app/backend/scripts/
docker compose exec api python scripts/report_stage_timings.py --video-ids 20,21
```

## Results

| Stage | Before (video 20) | After (video 21) | Speed-up |
|---|---|---|---|
| metadata | 0s | 0s | – |
| transcription (Whisper) | 1m 05s | 1m 12s | – |
| embedding (BGE-M3) | 10s | 9s | – |
| translation | 3m 36s | 1m 30s | 2.4× |
| quiz | 5m 51s | 3m 18s | 1.8× |
| chapter | 5m 34s | 40s | **8.4×** |
| flashcard | 2m 26s | 1m 27s | 1.7× |
| **Total (excluding summary)** | **18m 42s** | **8m 16s** | **2.3×** |

A longer video from the same day (video 19, 187 seconds, before the changes)
spent:

- 39 minutes in total;
- 20 of those minutes in the chapter stage alone;
- only 2 minutes in Whisper.

### Why qwen3's thinking mode mattered

qwen3 writes a hidden chain of reasoning before every answer unless told not
to. Measured directly against Ollama with the same Vietnamese summarization
prompt, two calls each:

| Thinking | Output tokens | Time per call |
|---|---|---|
| on (Ollama default) | 404–459 | 75–85 s |
| off (`"think": false`) | 153–178 | 27–29 s |

The answers are about the same length (575–704 characters either way). With
thinking on, about 60% of the generated tokens were reasoning that the
pipeline throws away. Generation speed is the same in both cases, about 6
tokens/s on this CPU, so the time saved is exactly the tokens saved.

## What changed

- **`OLLAMA_THINK=false`** (new setting, on by default). `OllamaClient` sends
  `"think": false` on both the normal and the streaming calls, so RAG chat
  answers start sooner too. Leave the setting empty to not send the option,
  for models that reject it.
- **One LLM call per chapter.** `ChapterLabeler.describe()` asks for
  `{"title", "summary"}` as JSON:
  - unusable output falls back to the previous two separate calls, so quality
    never drops below the old behaviour;
  - if Ollama itself fails, it uses the non-LLM fallback title instead of
    trying twice more.
- **Whisper loaded once per worker.** Each processing task builds a new
  pipeline, so `medium` (about 1.5 GB) used to be reloaded from disk for every
  video. It is now cached per worker process. This does not show up in the
  table above, because video 21 was the first task after a worker restart;
  it saves the load time on every video after that.
- **`scripts/report_stage_timings.py`.** Produces the table above from any
  processed videos.

## Limits

- **One video.** These are single runs on one video, not averages. The
  thinking measurement is the more controlled one: same prompt, repeated.
  LLM stage times also vary with how much each prompt makes the model write.
- **Summary not compared.** Video 21's summary stage failed: Ollama hit
  `std::bad_alloc` while loading the model, because the host had run out of
  Windows commit memory. This is an environment limit (small pagefile), not
  a code path. The stage was not re-run, so summary is excluded from both
  totals rather than compared unfairly.
- **CPU only.** On a GPU, LLM generation is one to two orders of magnitude
  faster and the balance between stages changes. The relative wins
  (fewer tokens, fewer calls) still apply.
