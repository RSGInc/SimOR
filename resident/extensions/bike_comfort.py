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
from activitysim.core.configuration.base import PreprocessorSettings
from activitysim.core.configuration.logit import LogitComponentSettings

logger = logging.getLogger("activitysim")


class BikeComfortSettings(LogitComponentSettings, extra="forbid"):
    """
    Settings for the 'bike_comfort' model.
    """

    CHOOSE_FILTER_COLUMN_NAME: str = "adult"
    """Column name in the dataframe to filter persons eligible for license holding status model."""


@workflow.step
def bike_comfort(
    state: workflow.State,
    persons_merged: pd.DataFrame,
    persons: pd.DataFrame,
    model_settings: BikeComfortSettings | None = None,
    model_settings_file_name: str = "bike_comfort.yaml",
    trace_label: str = "bike_comfort",
) -> None:
    """
    This model predicts the bike comfort level for each person.
    The alternatives of this model are NoWyNoHow, InterestedButConcerned, EnthsuedAndConfident, StrongAndFearless
    """

    if model_settings is None:
        model_settings = BikeComfortSettings.read_settings_file(
            state.filesystem,
            model_settings_file_name,
        )

    choosers = persons_merged
    chooser_filter_columun_name = model_settings.CHOOSE_FILTER_COLUMN_NAME
    choosers = choosers[(choosers[chooser_filter_columun_name])]
    logger.info("Running %s with %d persons", trace_label, len(choosers))

    estimator = estimation.manager.begin_estimation(state, "bike_comfort")

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
        trace_choice_name="bike_comfort",
        estimator=estimator,
        compute_settings=model_settings.compute_settings,
    )

    choices = pd.Series(model_spec.columns[choices.values], index=choices.index)
    bike_comfort_cat = pd.api.types.CategoricalDtype(
        model_spec.columns.tolist() + [""],
        ordered=False,
    )

    choices = choices.astype(bike_comfort_cat)

    if estimator:
        estimator.write_choices(choices)
        choices = estimator.get_survey_values(choices, "persons", "bike_comfort")
        estimator.write_override_choices(choices)
        estimator.end_estimation()

    persons["bike_comfort"] = choices.reindex(persons.index).fillna("")

    state.add_table("persons", persons)

    tracing.print_summary("bike_comfort", persons.bike_comfort, value_counts=True)

    if state.settings.trace_hh_id:
        state.tracing.trace_df(persons, label=trace_label, warn_if_empty=True)

    expressions.annotate_tables(
        state,
        locals_dict=constants,
        skims=None,
        model_settings=model_settings,
        trace_label=trace_label,
    )
