# Python Truth Layer Module Contract

## Purpose

The Python Truth Layer owns factual analysis only.

It may load safe audio inputs, calculate verified metrics, represent analysis state, select relevant evidence, compare allowed sources, preserve report facts, and prepare interpretation packets for the AI layer.

## Non-Negotiables

- No final user-facing advice.
- No canned recommendations.
- No fake metric values.
- No placeholder values returned as real analysis.
- No hardcoded local paths.
- No secrets.
- No copied old repo code.
- No backend, plugin, or AI adapter behavior.
- No hidden reference-pool use outside Reference Mode.

## Module Responsibilities

- `audio_loader.py`: audio input loading contract.
- `level_metrics.py`: sample peak, RMS, headroom, and ceiling-state contract.
- `loudness_metrics.py`: loudness and loudness range contract.
- `stereo_metrics.py`: stereo, correlation, mid/side, and mono-safety contract.
- `frequency_metrics.py`: frequency-band evidence contract.
- `tonal_balance.py`: tonal-balance summary contract.
- `dynamics_metrics.py`: dynamic range and crest behavior contract.
- `transient_metrics.py`: transient/punch evidence contract.
- `analysis_state.py`: source, mode, confidence, freshness, and packet state contract.
- `metric_relevance.py`: evidence-selection contract.
- `compare_ab.py`: Compare Mode A/B-only contract.
- `reference_compare.py`: Reference Mode target comparison contract.
- `export_history.py`: export history preservation contract.
- `progress_memory.py`: progress trend preservation contract.
- `interpretation_packet.py`: AI input packet contract.
- `report_writer.py`: factual report output contract.
- `config_paths.py`: portable path resolution contract.
- `privacy.py`: privacy and consent-screening contract.
- `validation.py`: validation and failure-state contract.

## Implementation Status

Only public interfaces are defined in this phase.

All public functions/classes must raise `NotImplementedError` until the next approved implementation phase.

## Controlling Contracts

- `docs/MASTER_IMPLEMENTATION_CHECKLIST.md`
- `docs/NO_DRIFT_CONTRACT.md`
- `docs/MODE_CONTRACT.md`
- `docs/SOURCE_OF_TRUTH_CONTRACT.md`
- `docs/METRIC_RELEVANCE_CONTRACT.md`
- `docs/REPORT_CONTRACT.md`
- `docs/RELEASE_ACCEPTANCE_GATES.md`

