# AI Processing Pipeline

One Celery task (`app.workers.video_processor.process_video`) runs every
stage below in order, updating `ProcessingJob.progress`/`current_step` as it
goes. All stages run in a single task today — there is no per-stage retry;
a failure anywhere re-runs the whole pipeline on reprocess (see
`app/pipelines/video_pipeline.py`).

```mermaid
flowchart TD
    Upload["POST /videos/upload<br/>(multipart, validated: extension allowlist,<br/>size cap, filename sanitized)"] --> Job["ProcessingJob created (PENDING)<br/>Video created (status=uploaded)"]
    Job --> Claim["claim_for_running()<br/>atomic PENDING → RUNNING"]

    Claim --> ASR["Transcription stage<br/>ai/speech (faster-whisper)<br/>+ optional VAD, optional diarization (off by default)"]
    ASR -->|"real ASR segments,<br/>never fabricated timestamps"| Transcript[("Transcript<br/>text, language, word_count")]

    Transcript --> Summary["Summary stage<br/>ai/summarization (Ollama)<br/>— single 'default' strategy today"]
    Transcript --> Embed["Embedding stage<br/>ai/embedding (BGE-M3)<br/>chunking → dense vectors"]
    Transcript --> Translation["Translation stage<br/>ai/translation (Ollama)<br/>target fixed to 'en'; skipped if source already 'en'"]
    Transcript --> Chapter["Chapter stage<br/>ai/chapter_detection<br/>embedding-based topic segmentation<br/>+ LLM chapter titles"]
    Transcript --> Quiz["Quiz stage<br/>ai/quiz_generation (Ollama)<br/>MCQ / true-false / short-answer"]
    Transcript --> Flash["Flashcard stage<br/>ai/flashcards (Ollama)<br/>+ TSV Anki export"]

    Summary --> SummaryDB[("summaries")]
    Embed --> FAISS[("FAISS index<br/>+ embeddings table<br/>(FileLock-guarded add/replace)")]
    Translation --> TranslationDB[("translations")]
    Chapter --> ChapterDB[("chapters<br/>start_time/end_time derived<br/>ONLY from real ASR segments")]
    Quiz --> QuizDB[("quizzes")]
    Flash --> FlashDB[("flashcards")]

    SummaryDB --> Done["Video.status = processed<br/>ProcessingJob.status = COMPLETED"]
    FAISS --> Done
    TranslationDB --> Done
    ChapterDB --> Done
    QuizDB --> Done
    FlashDB --> Done

    Claim -->|"any stage raises"| Failed["ProcessingJob.status = FAILED<br/>Video.status = failed<br/>error_message persisted"]

    style Upload fill:#1a1a1a,stroke:#c88a4a,color:#eee
    style Done fill:#1a1a1a,stroke:#7fa98c,color:#eee
    style Failed fill:#1a1a1a,stroke:#c96b57,color:#eee
```

## What is intentionally NOT in this pipeline

- **Speaker diarization** (`ai/diarization`) is implemented and wired into
  the speech stage, but gated behind `SPEECH_DIARIZATION_ENABLED=false` by
  default, and has no frontend surface.
- **Knowledge graph extraction** (`ai/knowledge_graph`) is implemented as
  standalone domain logic but is deliberately never called from this
  pipeline — no table, no endpoint (see that module's own docstring for the
  rationale: computing it live would mean uncached, non-deterministic LLM
  calls per request, and persisting it is a separate, larger change).
- **Multiple summary strategies**: the schema (`Summary.type`) allows for
  more than one, but only a single "default" summarizer exists today.
