"""Metric relevance routing for factual evidence selection.

Responsibility:
    Select metric families based on user intent, active mode, available metric
    families, and optional risk flags.

This module must not generate final user-facing advice, canned response text,
metric values, report writing, compare analysis, or reference comparison.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Sequence


class MetricFamily(str, Enum):
    """Metric families available to factual routing."""

    LEVEL = "level"
    LOUDNESS = "loudness"
    STEREO = "stereo"
    FREQUENCY = "frequency"
    TONAL_BALANCE = "tonal_balance"
    DYNAMICS = "dynamics"
    TRANSIENTS = "transients"
    REFERENCE = "reference"
    COMPARE = "compare"
    REPORT = "report"
    HISTORY = "history"


class UserIntentCategory(str, Enum):
    """Coarse intent categories for metric-family routing."""

    GENERAL_ANALYZE = "general_analyze"
    SATURATION = "saturation"
    COMPRESSION = "compression"
    LIMITING = "limiting"
    EQ = "eq"
    STEREO_WIDTH = "stereo_width"
    VOCAL = "vocal"
    MASTERING = "mastering"
    COMPARE = "compare"
    REFERENCE_TARGET = "reference_target"
    REPORT_REQUEST = "report_request"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class MetricRelevanceResult:
    """Factual metric-routing result with no interpretation prose."""

    intent: UserIntentCategory
    mode: str | None
    primary_metrics: tuple[MetricFamily, ...]
    secondary_metrics: tuple[MetricFamily, ...]
    excluded_metrics: tuple[MetricFamily, ...]
    reason_codes: tuple[str, ...]
    requires_reference_context: bool
    requires_compare_context: bool


_SATURATION_TERMS = ("saturat", "distort", "drive", "clipper", "harmonic")
_COMPRESSION_TERMS = ("compress", "compressor", "gain reduction", "attack", "release")
_LIMITING_TERMS = ("limit", "limiter", "ceiling", "true peak")
_EQ_TERMS = ("eq", "equaliz", "frequency", "tone", "tonal", "low", "mid", "high")
_STEREO_TERMS = ("stereo", "width", "wide", "mono", "correlation", "side")
_VOCAL_TERMS = ("vocal", "voice", "singer", "rap", "lead")
_MASTERING_TERMS = ("master", "mastering", "lufs", "loudness")
_COMPARE_TERMS = ("compare", "versus", " vs ", "a/b", "difference", "changed")
_REFERENCE_TERMS = ("reference", "target", "match", "closer to")
_REPORT_TERMS = ("report", "export", "summary", "save")


def _coerce_metric_family(value: MetricFamily | str) -> MetricFamily:
    if isinstance(value, MetricFamily):
        return value
    return MetricFamily(str(value))


def _coerce_intent(value: UserIntentCategory | str) -> UserIntentCategory:
    if isinstance(value, UserIntentCategory):
        return value
    return UserIntentCategory(str(value))


def _contains_any(text: str, terms: Sequence[str]) -> bool:
    return any(term in text for term in terms)


def classify_user_intent(question: str) -> UserIntentCategory:
    """Classify a question into a factual routing intent."""
    text = question.lower()
    if _contains_any(text, _COMPARE_TERMS):
        return UserIntentCategory.COMPARE
    if _contains_any(text, _REFERENCE_TERMS):
        return UserIntentCategory.REFERENCE_TARGET
    if _contains_any(text, _REPORT_TERMS):
        return UserIntentCategory.REPORT_REQUEST
    if _contains_any(text, _SATURATION_TERMS):
        return UserIntentCategory.SATURATION
    if _contains_any(text, _COMPRESSION_TERMS):
        return UserIntentCategory.COMPRESSION
    if _contains_any(text, _LIMITING_TERMS):
        return UserIntentCategory.LIMITING
    if _contains_any(text, _STEREO_TERMS):
        return UserIntentCategory.STEREO_WIDTH
    if _contains_any(text, _VOCAL_TERMS):
        return UserIntentCategory.VOCAL
    if _contains_any(text, _MASTERING_TERMS):
        return UserIntentCategory.MASTERING
    if _contains_any(text, _EQ_TERMS):
        return UserIntentCategory.EQ
    if text.strip():
        return UserIntentCategory.GENERAL_ANALYZE
    return UserIntentCategory.UNKNOWN


def filter_available_metrics(
    selected: Sequence[MetricFamily],
    available: Sequence[MetricFamily] | None,
) -> tuple[MetricFamily, ...]:
    """Return selected metric families that are present in available families."""
    selected_tuple = tuple(_coerce_metric_family(metric) for metric in selected)
    if available is None:
        return selected_tuple
    available_set = {_coerce_metric_family(metric) for metric in available}
    return tuple(metric for metric in selected_tuple if metric in available_set)


def mode_allows_reference(mode: str | None, intent: UserIntentCategory) -> bool:
    """Return whether the mode and intent allow reference context."""
    normalized_mode = None if mode is None else mode.lower()
    if normalized_mode == "reference":
        return True
    return intent == UserIntentCategory.REFERENCE_TARGET


def mode_allows_compare(mode: str | None, intent: UserIntentCategory) -> bool:
    """Return whether the mode and intent allow compare context."""
    normalized_mode = None if mode is None else mode.lower()
    if normalized_mode == "compare":
        return True
    return intent == UserIntentCategory.COMPARE


def _base_metric_plan(intent: UserIntentCategory) -> tuple[tuple[MetricFamily, ...], tuple[MetricFamily, ...]]:
    plans: dict[UserIntentCategory, tuple[tuple[MetricFamily, ...], tuple[MetricFamily, ...]]] = {
        UserIntentCategory.SATURATION: (
            (MetricFamily.TONAL_BALANCE, MetricFamily.FREQUENCY, MetricFamily.LEVEL, MetricFamily.LOUDNESS),
            (MetricFamily.DYNAMICS, MetricFamily.TRANSIENTS),
        ),
        UserIntentCategory.COMPRESSION: (
            (MetricFamily.DYNAMICS, MetricFamily.TRANSIENTS, MetricFamily.LEVEL, MetricFamily.LOUDNESS),
            (),
        ),
        UserIntentCategory.LIMITING: (
            (MetricFamily.LEVEL, MetricFamily.LOUDNESS, MetricFamily.DYNAMICS),
            (MetricFamily.TRANSIENTS,),
        ),
        UserIntentCategory.EQ: (
            (MetricFamily.FREQUENCY, MetricFamily.TONAL_BALANCE),
            (),
        ),
        UserIntentCategory.STEREO_WIDTH: (
            (MetricFamily.STEREO,),
            (MetricFamily.FREQUENCY,),
        ),
        UserIntentCategory.VOCAL: (
            (MetricFamily.FREQUENCY, MetricFamily.TONAL_BALANCE, MetricFamily.DYNAMICS, MetricFamily.LEVEL),
            (MetricFamily.LOUDNESS, MetricFamily.TRANSIENTS),
        ),
        UserIntentCategory.MASTERING: (
            (MetricFamily.LEVEL, MetricFamily.LOUDNESS, MetricFamily.TONAL_BALANCE, MetricFamily.STEREO, MetricFamily.DYNAMICS),
            (MetricFamily.FREQUENCY, MetricFamily.TRANSIENTS),
        ),
        UserIntentCategory.COMPARE: (
            (MetricFamily.COMPARE, MetricFamily.LEVEL, MetricFamily.LOUDNESS, MetricFamily.DYNAMICS),
            (MetricFamily.STEREO, MetricFamily.FREQUENCY, MetricFamily.TONAL_BALANCE),
        ),
        UserIntentCategory.REFERENCE_TARGET: (
            (MetricFamily.REFERENCE, MetricFamily.LEVEL, MetricFamily.LOUDNESS, MetricFamily.TONAL_BALANCE),
            (MetricFamily.STEREO, MetricFamily.DYNAMICS, MetricFamily.FREQUENCY),
        ),
        UserIntentCategory.REPORT_REQUEST: (
            (MetricFamily.REPORT,),
            (MetricFamily.LEVEL, MetricFamily.LOUDNESS, MetricFamily.DYNAMICS, MetricFamily.STEREO),
        ),
        UserIntentCategory.GENERAL_ANALYZE: (
            (MetricFamily.LEVEL, MetricFamily.LOUDNESS, MetricFamily.FREQUENCY, MetricFamily.TONAL_BALANCE, MetricFamily.STEREO, MetricFamily.DYNAMICS),
            (MetricFamily.TRANSIENTS,),
        ),
        UserIntentCategory.UNKNOWN: (
            (MetricFamily.LEVEL, MetricFamily.LOUDNESS, MetricFamily.FREQUENCY, MetricFamily.TONAL_BALANCE, MetricFamily.STEREO, MetricFamily.DYNAMICS),
            (MetricFamily.TRANSIENTS,),
        ),
    }
    return plans[intent]


def _unique_metrics(metrics: Sequence[MetricFamily]) -> tuple[MetricFamily, ...]:
    seen: set[MetricFamily] = set()
    ordered: list[MetricFamily] = []
    for metric in metrics:
        if metric not in seen:
            seen.add(metric)
            ordered.append(metric)
    return tuple(ordered)


def select_relevant_metric_families(
    intent: UserIntentCategory | str,
    mode: str | None = None,
    available_metrics: Sequence[MetricFamily] | None = None,
    risk_flags: Sequence[str] | None = None,
) -> MetricRelevanceResult:
    """Select relevant metric families for a factual routing intent."""
    normalized_intent = _coerce_intent(intent)
    primary_plan, secondary_plan = _base_metric_plan(normalized_intent)
    normalized_mode = None if mode is None else mode.lower()

    if mode_allows_compare(normalized_mode, normalized_intent):
        primary_plan = _unique_metrics((MetricFamily.COMPARE, *primary_plan))
    if mode_allows_reference(normalized_mode, normalized_intent):
        primary_plan = _unique_metrics((MetricFamily.REFERENCE, *primary_plan))

    risk_codes = tuple(str(flag).lower() for flag in (risk_flags or ()))
    if "clip" in risk_codes or "ceiling" in risk_codes:
        primary_plan = _unique_metrics((*primary_plan, MetricFamily.LEVEL))
    if "mono" in risk_codes or "correlation" in risk_codes:
        primary_plan = _unique_metrics((*primary_plan, MetricFamily.STEREO))

    selected_primary = filter_available_metrics(primary_plan, available_metrics)
    selected_secondary = filter_available_metrics(secondary_plan, available_metrics)
    available_set = None if available_metrics is None else {_coerce_metric_family(metric) for metric in available_metrics}
    selected_set = set(selected_primary) | set(selected_secondary)
    excluded = () if available_set is None else tuple(metric for metric in (*primary_plan, *secondary_plan) if metric not in selected_set)

    mode_codes = (f"mode_{normalized_mode}",) if normalized_mode else ()

    return MetricRelevanceResult(
        intent=normalized_intent,
        mode=normalized_mode,
        primary_metrics=selected_primary,
        secondary_metrics=selected_secondary,
        excluded_metrics=_unique_metrics(excluded),
        reason_codes=(normalized_intent.value, *mode_codes, *risk_codes),
        requires_reference_context=normalized_mode == "reference" or normalized_intent == UserIntentCategory.REFERENCE_TARGET,
        requires_compare_context=normalized_mode == "compare" or normalized_intent == UserIntentCategory.COMPARE,
    )


def select_relevant_metrics(
    *,
    user_question: str | None,
    mode: str,
    available_metrics: dict[str, Any],
    source_state: dict[str, Any],
) -> list[str]:
    """Compatibility wrapper returning selected metric-family values."""
    del source_state
    available = tuple(MetricFamily(key) for key, value in available_metrics.items() if value)
    result = select_relevant_metric_families(
        classify_user_intent(user_question or ""),
        mode=mode,
        available_metrics=available,
    )
    return [metric.value for metric in (*result.primary_metrics, *result.secondary_metrics)]


def explain_relevance_selection(selected_metrics: list[str]) -> list[dict[str, Any]]:
    """Return factual metadata for selected metric-family keys."""
    return [{"metric_family": _coerce_metric_family(metric).value, "selected": True} for metric in selected_metrics]
