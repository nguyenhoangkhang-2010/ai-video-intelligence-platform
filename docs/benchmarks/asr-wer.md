# Vietnamese speech recognition (WER)

**Finding:** on Vietnamese read speech, Whisper `medium` makes about 41% fewer
word errors than `small`. Word error rate drops from 21.5% to 12.6%. That is
why the project transcribes with `medium`. The cost is speed: on a CPU-only
laptop, `medium` runs slower than real time.

## Setup

- **Data.** The first 200 clips of the `test` split of
  [FLEURS](https://huggingface.co/datasets/google/fleurs) `vi_vn`: 42 minutes
  of audio and 6,193 reference words. These are human transcriptions of read
  Wikipedia sentences.
- **Engine.** faster-whisper 1.2.1 with `language=vi`, running on the CPU
  with `int8` compute: an Intel Core 12th gen (Family 6 Model 154) with no GPU.
  These are the same settings the processing pipeline uses.
- **Metrics.** Both are computed on the whole corpus (`ai/evaluation/metrics/asr.py`):
  - WER = (substitutions + deletions + insertions) ÷ reference words, summed
    over all clips.
  - CER is the same calculation over characters, ignoring spaces.
- **Normalization.** Both sides are normalized first: Unicode NFC, lowercase,
  punctuation removed. **Diacritics are kept.** A wrong tone mark (*chợ* vs
  *chờ*) is a real error in Vietnamese and is counted as one.
- **RTF.** Transcription time ÷ audio duration. Below 1 means faster than real
  time.
- **Date.** Run on 2026-10-26.

Reproduce from `backend/`:

```bash
python scripts/benchmark_asr_wer.py prepare-fleurs --out D:/data/fleurs_vi --split test
python scripts/benchmark_asr_wer.py run --manifest D:/data/fleurs_vi/manifest.tsv \
    --models small,medium --limit 200 --report ../docs/benchmarks/asr-wer.md
```

## Results

| Model | WER | CER | Substitutions | Deletions | Insertions | RTF (CPU, int8) |
|---|---|---|---|---|---|---|
| `small` | 21.5% | 12.2% | 1,140 | 86 | 107 | 0.41 |
| `medium` | **12.6%** | **7.2%** | 658 | 53 | 67 | 2.11* |

\* `medium` shared the CPU for most of its run with a reranker benchmark
([reranker-vi.md](reranker-vi.md)), so this RTF is pessimistic. Even run
alone, `medium` on this CPU is not real-time. A GPU (`WHISPER_DEVICE=cuda`)
is the intended path for long uploads.

## What it means

- **Substitutions dominate:** about 85% of errors for both models. Whisper
  rarely drops or invents words. Most of its mistakes are wrong syllables,
  often a wrong tone. Search and RAG partly absorb this:
  - hybrid retrieval matches on meaning (BGE-M3) as well as exact words;
  - the reranker reads whole passages.
- **`medium` is the quality floor for Vietnamese.** At 21.5% WER, `small`
  garbles about one word in five. That flows directly into summaries,
  translations and chat answers.
- **Speed is the trade-off.** On CPU, a 10-minute upload takes roughly 4
  minutes with `small` and over 20 minutes with `medium`. The project sets
  `WHISPER_MODEL=medium` and leaves `small` as an option for fast drafts.

## Limits

- FLEURS is clean read speech, one speaker per clip. Real uploads have music,
  crosstalk, noise and spontaneous speech, so expect higher WER there.
  This table compares models; it does not predict WER on any one video.
- The 200 clips are a subset of the 857-clip test split, because running
  `medium` on CPU is slow. Corpus WER on 6,000+ reference words is stable
  enough to compare models, but the last decimal place is not significant.
