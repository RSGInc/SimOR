# ActivitySim
# See full license in LICENSE.txt.
import logging

import numpy as np
import pandas as pd

from activitysim.core import (
    config,
    expressions,
    los,
    estimation,
    simulate,
    tracing,
    workflow,
)
from activitysim.core.configuration.logit import (
    LogitComponentSettings,
    PreprocessorSettings,
)
from activitysim.core.interaction_simulate import interaction_simulate


logger = logging.getLogger(__name__)

PNR_LOT_DEST_COLUMN = "pnr_zone_id"


class ParkAndRideLotChoiceSettings(LogitComponentSettings, extra="forbid"):
    """
    Settings for the `external_identification` component.
    """

    LANDUSE_PNR_SPACES_COLUMN: str
    """lists the column name in the land use table that contains the number of park-and-ride spaces available in the zone"""

    TRANSIT_SKIMS_FOR_ELIGIBILITY: list[str] | None = None
    """A list of skim names to use for filtering choosers to only those with destinations that have transit access.
    If None, all tours are considered eligible for park-and-ride lot choice."""

    explicit_chunk: float = 0
    """
    If > 0, use this chunk size instead of adaptive chunking.
    If less than 1, use this fraction of the total number of rows.
    """

    preprocessor: PreprocessorSettings | None = None
    """FIXME preprocessor can be removed once preprocessor / annotator work is pulled in."""

    # FIXME need to add alts preprocessor as well


def filter_chooser_to_transit_accessible_destinations(
    state: workflow.State,
    choosers: pd.DataFrame,
    pnr_alts: pd.DataFrame,
    network_los: los.Network_LOS,
    model_settings: ParkAndRideLotChoiceSettings,
) -> pd.DataFrame:
    """
    Filter choosers to only those with destinations that have transit access.
    We look at the skims and check the destination has any non-zero terms for transit access.
    We get the skims to check from the model settings.
    """
    # all choosers are eligible if transit skims are not provided
    if model_settings.TRANSIT_SKIMS_FOR_ELIGIBILITY is None:
        logger.info(
            "No transit skims provided for park-and-ride lot choice model. All tours are eligible."
        )
        return choosers

    skim_dict = network_los.get_default_skim_dict()
    unique_destinations = choosers["destination"].unique()
    unique_lot_locations = pnr_alts.index.values

    for skim_name in model_settings.TRANSIT_SKIMS_FOR_ELIGIBILITY:
        if "__" in skim_name:
            # If the skim name contains '__', it is a 3D skim
            # we need to pass the skim name as a tuple to the lookup method
            skim_name = tuple(skim_name.split("__"))
        if skim_name not in skim_dict.skim_info.omx_keys.keys():
            raise ValueError(
                f"Skim '{skim_name}' not found in the skim dictionary."
                "Please update the model setting TRANSIT_SKIMS_FOR_ELIGIBILITY with valid skim names."
            )
        # Filter choosers to only those with destinations that have transit access
        # want to check whether ANY of the lot locations have transit access to EVERY destination
        transit_accessible = [
            (
                skim_dict.lookup(
                    unique_lot_locations,
                    np.full(shape=len(unique_lot_locations), fill_value=dest),
                    skim_name,
                )
                > 0
            ).any()
            for dest in unique_destinations
        ]

    eligible_destinations = unique_destinations[transit_accessible]
    filtered_choosers = choosers[choosers["destination"].isin(eligible_destinations)]

    logger.info(
        f"Filtered tours to {len(filtered_choosers)} with transit access to their destination."
        f" Total number of tours: {len(choosers)}."
        f" Percentage of tours with transit access at destination: "
        f"{len(filtered_choosers) / len(choosers) * 100:.2f}%"
    )

    return filtered_choosers


def setup_skims(state, network_los: los.Network_LOS, choosers: pd.DataFrame):
    """
    Setup skims for the park-and-ride lot choice model.

    o = tour origin
    d = tour destination
    l = parking lot location
    t = tour start time
    r = tour return time

    building skims from origin to lot and lot to destination
    also building skims in reverse direction during return time.
    """
    skim_dict = network_los.get_default_skim_dict()

    # setup skim keys
    orig_col_name = "home_zone_id"
    dest_col_name = "destination"
    lot_dest_col_name = PNR_LOT_DEST_COLUMN
    out_time_col_name = "start"
    in_time_col_name = "end"

    # creating skim wrappers
    odt_skim_stack_wrapper = skim_dict.wrap_3d(
        orig_key=orig_col_name, dest_key=dest_col_name, dim3_key="out_period"
    )
    olt_skim_stack_wrapper = skim_dict.wrap_3d(
        orig_key=orig_col_name, dest_key=lot_dest_col_name, dim3_key="out_period"
    )
    ldt_skim_stack_wrapper = skim_dict.wrap_3d(
        orig_key=lot_dest_col_name, dest_key=dest_col_name, dim3_key="out_period"
    )
    dot_skim_stack_wrapper = skim_dict.wrap_3d(
        orig_key=dest_col_name, dest_key=orig_col_name, dim3_key="in_period"
    )
    dlt_skim_stack_wrapper = skim_dict.wrap_3d(
        orig_key=dest_col_name, dest_key=lot_dest_col_name, dim3_key="in_period"
    )
    lot_skim_stack_wrapper = skim_dict.wrap_3d(
        orig_key=lot_dest_col_name, dest_key=orig_col_name, dim3_key="in_period"
    )

    skims = {
        "odt_skims": odt_skim_stack_wrapper,
        "olt_skims": olt_skim_stack_wrapper,
        "ldt_skims": ldt_skim_stack_wrapper,
        "dot_skims": dot_skim_stack_wrapper,
        "dlt_skims": dlt_skim_stack_wrapper,
        "lot_skims": lot_skim_stack_wrapper,
        "orig_col_name": orig_col_name,
        "dest_col_name": dest_col_name,
        "lot_dest_col_name": lot_dest_col_name,
        "out_time_col_name": out_time_col_name,
        "in_time_col_name": in_time_col_name,
    }

    choosers["out_period"] = network_los.skim_time_period_label(
        choosers[out_time_col_name]
    )
    choosers["in_period"] = network_los.skim_time_period_label(
        choosers[in_time_col_name]
    )

    return skims


@workflow.step
def park_and_ride_lot_choice(
    state: workflow.State,
    tours: pd.DataFrame,
    tours_merged: pd.DataFrame,
    land_use: pd.DataFrame,
    network_los: los.Network_LOS,
    model_settings: ParkAndRideLotChoiceSettings | None = None,
    model_settings_file_name: str = "park_and_ride_lot_choice.yaml",
    trace_label: str = "park_and_ride_lot_choice",
    trace_hh_id: bool = False,
) -> None:
    """
    This model predicts which lot location would be used for a park-and-ride tour.
    """
    if model_settings is None:
        model_settings = ParkAndRideLotChoiceSettings.read_settings_file(
            state.filesystem,
            model_settings_file_name,
        )

    estimator = estimation.manager.begin_estimation(state, "park_and_ride_lot_choice")

    spec = state.filesystem.read_model_spec(file_name=model_settings.SPEC)
    coefficients = state.filesystem.read_model_coefficients(model_settings)
    model_spec = simulate.eval_coefficients(state, spec, coefficients, estimator)
    locals_dict = model_settings.CONSTANTS

    pnr_alts = land_use[land_use[model_settings.LANDUSE_PNR_SPACES_COLUMN] > 0]
    pnr_alts[PNR_LOT_DEST_COLUMN] = pnr_alts.index.values

    choosers = filter_chooser_to_transit_accessible_destinations(
        state,
        tours_merged,
        pnr_alts,
        network_los,
        model_settings,
    )

    skims = setup_skims(state, network_los, choosers)
    locals_dict.update(skims)

    # FIXME: add alts preprocessors
    expressions.annotate_preprocessors(
        state,
        df=choosers,
        locals_dict=locals_dict,
        skims={},  # not including skims because lot alt destination not in chooser table
        model_settings=model_settings,
        trace_label=trace_label,
    )

    choices = interaction_simulate(
        state,
        choosers=choosers,
        alternatives=pnr_alts,
        spec=model_spec,
        skims=skims,
        log_alt_losers=state.settings.log_alt_losers,
        locals_d=locals_dict,
        trace_label=trace_label,
        trace_choice_name=trace_label,
        estimator=estimator,
        explicit_chunk_size=model_settings.explicit_chunk,
        compute_settings=model_settings.compute_settings,
    )

    choices = choices.reindex(tours.index, fill_value=-1)

    tours[PNR_LOT_DEST_COLUMN] = choices

    state.add_table("tours", tours)

    if trace_hh_id:
        state.tracing.trace_df(tours, label=trace_label, warn_if_empty=True)
