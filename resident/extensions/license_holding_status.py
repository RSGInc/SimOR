# ActivitySim
# See full license in LICENSE.txt.
from __future__ import annotations

import logging
import pandas as pd

from activitysim.core import (
    config,
    estimation,
    expressions,
    simulate,
    tracing,
    workflow,
)

from activitysim.core.configuration.base import PreprocessorSettings, PydanticReadable
from activitysim.core.configuration.logit import LogitComponentSettings

logger = logging.getLogger("activitysim")


class LicenseHoldingStatusSettings(LogitComponentSettings, extra="forbid"):
    """
    Settings for the 'license_holding_status' model.
    """

    LICENSE_STATUS_ALT: int = 0
    """Value that specifies if the person has a driver's license (can drive)."""

    CHOOSE_FILTER_COLUMN_NAME: str | None = None
    """Column name in the dataframe to filter persons eligible for license holding status model."""


@workflow.step
def license_holding_status(
    state: workflow.State,
    persons_merged: pd.DataFrame,
    persons: pd.DataFrame,
    model_settings: LicenseHoldingStatusSettings | None = None,
    model_settings_file_name: str = "license_holding_status.yaml",
    trace_label: str = "license_holding_status",
) -> None:
    """
    This model predicts whether a person holds a driver's license or not.
    The output from this model is TRUE (if the person holds a license) or FALSE (if not).
    """
    if model_settings is None:
        model_settings = LicenseHoldingStatusSettings.read_settings_file(
            state.filesystem, model_settings_file_name
        )

    choosers = persons_merged
    chooser_filter_columun_name = model_settings.CHOOSE_FILTER_COLUMN_NAME
    if chooser_filter_columun_name:
        choosers = choosers[(choosers[chooser_filter_columun_name])]
    logger.info("Running %s with %d persons", trace_label, len(choosers))

    estimator = estimation.manager.begin_estimation(state, "license_holding_status")

    constants = config.get_model_constants(model_settings)

    # - preprocessor
    expressions.annotate_preprocessors(
        state,
        df=choosers,
        locals_dict=constants,
        skims=None,
        model_settings=model_settings,
        trace_label=trace_label,
    )

    model_spec = state.filesystem.read_model_spec(file_name=model_settings.SPEC)
    coefficients_df = state.filesystem.read_model_coefficients(model_settings)
    model_spec = simulate.eval_coefficients(
        state, model_spec, coefficients_df, estimator
    )
    nest_spec = config.get_logit_model_settings(model_settings)

    if estimator:
        estimator.write_model_settings(model_settings, model_settings_file_name)
        estimator.write_spec(model_settings)
        estimator.write_coefficients(coefficients_df, model_settings)
        estimator.write_choosers(choosers)

    choices = simulate.simple_simulate(
        state,
        choosers=choosers,
        spec=model_spec,
        nest_spec=nest_spec,
        locals_d=constants,
        trace_label=trace_label,
        trace_choice_name="has_license",
        estimator=estimator,
        compute_settings=model_settings.compute_settings,
    )

    has_license = model_settings.LICENSE_STATUS_ALT
    choices = choices == has_license

    if estimator:
        estimator.write_choices(choices)
        choices = estimator.get_survey_values(choices, "persons", "has_license")
        estimator.write_override_choices(choices)
        estimator.end_estimation()

    persons["has_license"] = choices.reindex(persons.index).fillna(0).astype(bool)

    state.add_table("persons", persons)

    tracing.print_summary(
        "license_holding_status", persons.has_license, value_counts=True
    )

    if state.settings.trace_hh_id:
        state.tracing.trace_df(persons, label=trace_label, warn_if_empty=True)

    expressions.annotate_tables(
        state,
        locals_dict=constants,
        skims=None,
        model_settings=model_settings,
        trace_label=trace_label,
    )
