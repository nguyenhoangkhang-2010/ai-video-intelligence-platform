import pytest

from app.workers.pipeline_metrics import (
    ACTIVE_STAGES,
    PIPELINE_COMPLETED_TOTAL,
    STAGE_DURATION_SECONDS,
    STAGE_EXECUTIONS_TOTAL,
    observe_stage,
    record_pipeline_outcome,
    record_skipped,
)


def _counter_value(counter, **labels) -> float:
    return counter.labels(**labels)._value.get()


def _gauge_value(gauge, **labels) -> float:
    return gauge.labels(**labels)._value.get()


def _histogram_observation_count(histogram, **labels) -> float:
    """
    Read a Histogram's total observation count via the public
    .collect() API (the "<name>_count" sample) rather than any
    private attribute - robust to prometheus_client internals. A
    label combination that has never been observed yet legitimately
    has no sample at all (not an error) - treated as count 0.
    """
    for metric in histogram.collect():
        for sample in metric.samples:
            if sample.name.endswith("_count") and all(
                sample.labels.get(key) == value for key, value in labels.items()
            ):
                return sample.value
    return 0.0


def test_observe_stage_records_success_and_clears_active_gauge():
    stage = "test_stage_success"

    before = _counter_value(STAGE_EXECUTIONS_TOTAL, stage=stage, result="success")

    with observe_stage(stage):
        pass

    after = _counter_value(STAGE_EXECUTIONS_TOTAL, stage=stage, result="success")
    assert after == before + 1

    # Active gauge must return to 0 after a successful exit.
    assert _gauge_value(ACTIVE_STAGES, stage=stage) == 0

    # Duration was recorded (at least one observation).
    assert _histogram_observation_count(STAGE_DURATION_SECONDS, stage=stage) >= 1


def test_observe_stage_records_failure_and_still_clears_active_gauge():
    stage = "test_stage_failure"

    before = _counter_value(STAGE_EXECUTIONS_TOTAL, stage=stage, result="failure")

    with pytest.raises(ValueError):
        with observe_stage(stage):
            raise ValueError("boom")

    after = _counter_value(STAGE_EXECUTIONS_TOTAL, stage=stage, result="failure")
    assert after == before + 1

    # The active-stage gauge must be cleaned up even though the
    # wrapped code raised - this is the whole point of the finally
    # block, not just the happy path.
    assert _gauge_value(ACTIVE_STAGES, stage=stage) == 0

    # A failed execution still recorded a duration observation (it did
    # run for some amount of time before failing).
    assert _histogram_observation_count(STAGE_DURATION_SECONDS, stage=stage) >= 1


def test_observe_stage_never_records_success_and_failure_for_the_same_attempt():
    stage = "test_stage_exclusive_result"

    success_before = _counter_value(STAGE_EXECUTIONS_TOTAL, stage=stage, result="success")
    failure_before = _counter_value(STAGE_EXECUTIONS_TOTAL, stage=stage, result="failure")

    with pytest.raises(RuntimeError):
        with observe_stage(stage):
            raise RuntimeError("boom")

    assert _counter_value(STAGE_EXECUTIONS_TOTAL, stage=stage, result="success") == success_before
    assert _counter_value(STAGE_EXECUTIONS_TOTAL, stage=stage, result="failure") == failure_before + 1


def test_record_skipped_increments_skipped_result_without_duration():
    stage = "test_stage_skipped"

    before = _counter_value(STAGE_EXECUTIONS_TOTAL, stage=stage, result="skipped")
    duration_count_before = _histogram_observation_count(STAGE_DURATION_SECONDS, stage=stage)

    record_skipped(stage)

    after = _counter_value(STAGE_EXECUTIONS_TOTAL, stage=stage, result="skipped")
    assert after == before + 1

    # A skipped stage never executed - no duration observation added.
    duration_count_after = _histogram_observation_count(STAGE_DURATION_SECONDS, stage=stage)
    assert duration_count_after == duration_count_before


def test_record_pipeline_outcome_increments_the_matching_result():
    for result in ("success", "failure", "incomplete"):
        before = _counter_value(PIPELINE_COMPLETED_TOTAL, result=result)
        record_pipeline_outcome(result)
        after = _counter_value(PIPELINE_COMPLETED_TOTAL, result=result)
        assert after == before + 1


def test_metrics_have_no_high_cardinality_labels():
    """
    Explicit guard against the one mistake this module must never
    make: a label that would create one time series per job/video/
    user instead of per (bounded) stage name/result.
    """
    assert STAGE_EXECUTIONS_TOTAL._labelnames == ("stage", "result")
    assert STAGE_DURATION_SECONDS._labelnames == ("stage",)
    assert PIPELINE_COMPLETED_TOTAL._labelnames == ("result",)
    assert ACTIVE_STAGES._labelnames == ("stage",)

    forbidden = {"job_id", "video_id", "user_id", "filename", "uuid"}
    for metric in (STAGE_EXECUTIONS_TOTAL, STAGE_DURATION_SECONDS, PIPELINE_COMPLETED_TOTAL, ACTIVE_STAGES):
        assert forbidden.isdisjoint(metric._labelnames)


def test_safe_swallows_an_underlying_metric_client_error():
    """
    Observability must never break the pipeline: _safe() is the one
    mechanism every metric-recording call in this module goes
    through (see observe_stage/record_skipped/record_pipeline_outcome)
    - if the underlying Prometheus client call itself raises, _safe()
    must swallow it (logging a warning) rather than letting it
    escape, since a metrics bug must never fail a video-processing
    stage.
    """
    from app.workers.pipeline_metrics import _safe

    def _broken():
        raise RuntimeError("prometheus client exploded")

    # Must not raise.
    _safe(_broken)
