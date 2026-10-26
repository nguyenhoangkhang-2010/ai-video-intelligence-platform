"""
Vietnamese speech-recognition benchmark: word error rate (WER),
character error rate (CER) and speed of each Whisper model size, on a
public dataset with human-made reference transcripts.

Why a public dataset: WER needs a reference transcript that a person
wrote, not one produced by the same model being measured. Google's
FLEURS (Vietnamese, `vi_vn`) is used by default - read speech with
verified human transcriptions, CC-BY-4.0 - so anyone can reproduce the
numbers.

Two steps (run from backend/, with PYTHONPATH covering `app` and `ai`):

1. Download and prepare the data (once). Fetches FLEURS vi_vn from the
   Hugging Face Hub into --out (the test split is a few hundred MB) and
   writes a manifest: one `audio_path<TAB>reference` line per clip.

       python scripts/benchmark_asr_wer.py prepare-fleurs --out D:/datasets/fleurs-vi

2. Run the benchmark on that manifest (any manifest in the same format
   works - e.g. your own recordings with hand-checked transcripts):

       python scripts/benchmark_asr_wer.py run \
           --manifest D:/datasets/fleurs-vi/manifest.tsv \
           --models small,medium --limit 200 \
           --report ../docs/benchmarks/asr-wer.md

Reported per model: corpus WER and CER (edits summed over all clips,
see ai.evaluation.metrics.asr), the error breakdown, and the real-time
factor (transcription time / audio duration; below 1.0 is faster than
real time) on the machine it ran on.
"""
import argparse
import csv
import json
import platform
import tarfile
import time
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from ai.evaluation.metrics.asr import corpus_error_rates


FLEURS_REPO = "google/fleurs"
FLEURS_LANGUAGE = "vi_vn"


@dataclass
class ModelResult:
    model: str
    clips: int
    audio_seconds: float
    transcribe_seconds: float
    wer: float
    cer: float
    substitutions: int
    deletions: int
    insertions: int
    reference_words: int

    @property
    def real_time_factor(self) -> float:
        return self.transcribe_seconds / self.audio_seconds if self.audio_seconds else 0.0


# --- data preparation --------------------------------------------------------


def read_fleurs_tsv(tsv_path: Path) -> list[tuple[str, str]]:
    """(file_name, raw human transcription) rows from a FLEURS split TSV."""
    rows = []
    with tsv_path.open(encoding="utf-8", newline="") as handle:
        for record in csv.reader(handle, delimiter="\t", quoting=csv.QUOTE_NONE):
            if len(record) < 3:
                continue
            rows.append((record[1], record[2]))
    return rows


def write_manifest(entries: list[tuple[Path, str]], manifest_path: Path) -> None:
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        for audio_path, reference in entries:
            handle.write(f"{audio_path.as_posix()}\t{reference.strip()}\n")


def read_manifest(manifest_path: Path, limit: int | None = None) -> list[tuple[Path, str]]:
    entries = []
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or "\t" not in line:
            continue
        audio, reference = line.split("\t", 1)
        entries.append((Path(audio), reference))
        if limit is not None and len(entries) >= limit:
            break
    return entries


def prepare_fleurs(out_dir: Path, split: str) -> Path:
    from huggingface_hub import hf_hub_download

    out_dir.mkdir(parents=True, exist_ok=True)
    tsv = Path(
        hf_hub_download(
            FLEURS_REPO,
            f"data/{FLEURS_LANGUAGE}/{split}.tsv",
            repo_type="dataset",
            local_dir=out_dir,
        )
    )
    archive = Path(
        hf_hub_download(
            FLEURS_REPO,
            f"data/{FLEURS_LANGUAGE}/audio/{split}.tar.gz",
            repo_type="dataset",
            local_dir=out_dir,
        )
    )

    audio_dir = out_dir / "audio" / split
    audio_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as tar:
        tar.extractall(audio_dir, filter="data")

    files = {path.name: path for path in audio_dir.rglob("*.wav")}
    entries = [
        (files[name], reference)
        for name, reference in read_fleurs_tsv(tsv)
        if name in files and reference.strip()
    ]

    manifest = out_dir / "manifest.tsv"
    write_manifest(entries, manifest)
    print(f"Prepared {len(entries)} clips -> {manifest}")
    return manifest


# --- benchmark ---------------------------------------------------------------


def audio_duration_seconds(path: Path) -> float:
    import soundfile

    info = soundfile.info(str(path))
    return info.frames / info.samplerate


def benchmark_model(
    model_name: str,
    entries: list[tuple[Path, str]],
    device: str,
    compute_type: str,
    language: str,
) -> ModelResult:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, device=device, compute_type=compute_type)

    pairs = []
    audio_seconds = 0.0
    transcribe_seconds = 0.0

    for index, (audio_path, reference) in enumerate(entries, start=1):
        audio_seconds += audio_duration_seconds(audio_path)
        started = time.perf_counter()
        segments, _ = model.transcribe(str(audio_path), language=language, beam_size=5)
        hypothesis = " ".join(segment.text.strip() for segment in segments)
        transcribe_seconds += time.perf_counter() - started
        pairs.append((reference, hypothesis))
        if index % 25 == 0:
            print(f"  {model_name}: {index}/{len(entries)} clips")

    words, chars = corpus_error_rates(pairs)
    return ModelResult(
        model=model_name,
        clips=len(entries),
        audio_seconds=round(audio_seconds, 1),
        transcribe_seconds=round(transcribe_seconds, 1),
        wer=round(words.rate, 4),
        cer=round(chars.rate, 4),
        substitutions=words.substitutions,
        deletions=words.deletions,
        insertions=words.insertions,
        reference_words=words.reference_length,
    )


def render_report(results: list[ModelResult], manifest: Path, device: str, compute_type: str) -> str:
    lines = [
        "# Vietnamese speech recognition (WER)",
        "",
        f"Measured {date.today().isoformat()} with `scripts/benchmark_asr_wer.py` on "
        f"`{manifest.name}` ({results[0].clips if results else 0} clips), "
        f"faster-whisper on `{device}` / `{compute_type}`, {platform.processor() or platform.machine()}.",
        "",
        "Corpus WER/CER = errors summed over every clip / reference words (characters). "
        "Both sides are normalized (Unicode NFC, lowercase, punctuation removed); "
        "Vietnamese diacritics are kept, so a wrong tone mark counts as an error. "
        "RTF = transcription time / audio duration (lower is faster; < 1 is faster than real time).",
        "",
        "| Model | WER | CER | Substitutions | Deletions | Insertions | RTF |",
        "|---|---|---|---|---|---|---|",
    ]
    for result in results:
        lines.append(
            f"| `{result.model}` | {result.wer:.1%} | {result.cer:.1%} | {result.substitutions} | "
            f"{result.deletions} | {result.insertions} | {result.real_time_factor:.2f} |"
        )
    lines += [
        "",
        f"Reference words: {results[0].reference_words if results else 0}. "
        "Audio is read speech (FLEURS), which is cleaner than typical video audio - "
        "expect higher WER on real uploads with music, overlap or noise.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    prep = sub.add_parser("prepare-fleurs", help="download FLEURS vi_vn and write a manifest")
    prep.add_argument("--out", type=Path, required=True)
    prep.add_argument("--split", default="test", choices=["train", "dev", "test"])

    run = sub.add_parser("run", help="benchmark Whisper models on a manifest")
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--models", default="small,medium", help="comma-separated faster-whisper model names")
    run.add_argument("--limit", type=int, default=None, help="only the first N clips")
    run.add_argument("--device", default="cpu")
    run.add_argument("--compute-type", default="int8")
    run.add_argument("--language", default="vi")
    run.add_argument("--report", type=Path, default=None, help="write a markdown report here")
    run.add_argument("--json", type=Path, default=None, help="write raw results as JSON here")

    args = parser.parse_args()

    if args.command == "prepare-fleurs":
        prepare_fleurs(args.out, args.split)
        return

    entries = read_manifest(args.manifest, args.limit)
    if not entries:
        raise SystemExit(f"No clips found in {args.manifest}")

    results = []
    for model_name in [name.strip() for name in args.models.split(",") if name.strip()]:
        print(f"Benchmarking {model_name} on {len(entries)} clips...")
        result = benchmark_model(model_name, entries, args.device, args.compute_type, args.language)
        print(f"  WER {result.wer:.1%}  CER {result.cer:.1%}  RTF {result.real_time_factor:.2f}")
        results.append(result)

    report = render_report(results, args.manifest, args.device, args.compute_type)
    print()
    print(report)

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8")
    if args.json:
        args.json.write_text(
            json.dumps([{**asdict(r), "real_time_factor": r.real_time_factor} for r in results], indent=2),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
