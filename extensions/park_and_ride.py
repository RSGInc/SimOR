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
    TourModeComponentSettings,
)
from activitysim.abm.models.util import annotate, school_escort_tours_trips
from activitysim.core.interaction_simulate import interaction_simulate
from activitysim.abm.models.util.mode import run_tour_mode_choice_simulate
from activitysim.abm.models.tour_mode_choice import get_trip_mc_logsums_for_all_modes
from activitysim.core.util import assign_in_place, reindex


logger = logging.getLogger(__name__)


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

    PNR_LOT_DEST_COLUMN: str = "pnr_zone_id"
    """column name in the tours table that will contain the park-and-ride lot destination zone id."""

    preprocessor: PreprocessorSettings | None = None
    """FIXME preprocessor can be removed once preprocessor / annotator work is pulled in."""

    # FIXME need to add alts preprocessor as well


class TourModeWtihPNRComponentSettings(TourModeComponentSettings, extra="forbid"):
    PNR_LOT_DEST_COLUMN: str = "pnr_zone_id"
    """column name in the tours table that will contain the park-and-ride lot destination zone id."""


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


def setup_skims(
    model_settings,
    network_los: los.Network_LOS,
    choosers: pd.DataFrame,
    add_periods: bool = True,
):
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
    pnr_lot_dest_col_name = model_settings.PNR_LOT_DEST_COLUMN
    out_time_col_name = "start"
    in_time_col_name = "end"

    # creating skim wrappers
    odt_skim_stack_wrapper = skim_dict.wrap_3d(
        orig_key=orig_col_name, dest_key=dest_col_name, dim3_key="out_period"
    )
    olt_skim_stack_wrapper = skim_dict.wrap_3d(
        orig_key=orig_col_name, dest_key=pnr_lot_dest_col_name, dim3_key="out_period"
    )
    ldt_skim_stack_wrapper = skim_dict.wrap_3d(
        orig_key=pnr_lot_dest_col_name, dest_key=dest_col_name, dim3_key="out_period"
    )
    dot_skim_stack_wrapper = skim_dict.wrap_3d(
        orig_key=dest_col_name, dest_key=orig_col_name, dim3_key="in_period"
    )
    dlt_skim_stack_wrapper = skim_dict.wrap_3d(
        orig_key=dest_col_name, dest_key=pnr_lot_dest_col_name, dim3_key="in_period"
    )
    lot_skim_stack_wrapper = skim_dict.wrap_3d(
        orig_key=pnr_lot_dest_col_name, dest_key=orig_col_name, dim3_key="in_period"
    )
    od_skim_stack_wrapper = skim_dict.wrap(orig_col_name, dest_col_name)
    do_skim_stack_wrapper = skim_dict.wrap(dest_col_name, orig_col_name)
    ol_skim_stack_wrapper = skim_dict.wrap(orig_col_name, pnr_lot_dest_col_name)
    ld_skim_stack_wrapper = skim_dict.wrap(pnr_lot_dest_col_name, dest_col_name)

    skims = {
        "odt_skims": odt_skim_stack_wrapper,
        "olt_skims": olt_skim_stack_wrapper,
        "ldt_skims": ldt_skim_stack_wrapper,
        "dot_skims": dot_skim_stack_wrapper,
        "dlt_skims": dlt_skim_stack_wrapper,
        "lot_skims": lot_skim_stack_wrapper,
        "od_skims": od_skim_stack_wrapper,
        "do_skims": do_skim_stack_wrapper,
        "ol_skims": ol_skim_stack_wrapper,
        "ld_skims": ld_skim_stack_wrapper,
        "orig_col_name": orig_col_name,
        "dest_col_name": dest_col_name,
        "pnr_lot_dest_col_name": pnr_lot_dest_col_name,
        "out_time_col_name": out_time_col_name,
        "in_time_col_name": in_time_col_name,
    }

    if add_periods:
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

    # don't create estimation data bundle if model is being called from another model
    if state.get_rn_generator().step_name != "park_and_ride_lot_choice":
        estimator = None
    else:
        estimator = estimation.manager.begin_estimation(
            state, "park_and_ride_lot_choice"
        )

    spec = state.filesystem.read_model_spec(file_name=model_settings.SPEC)
    coefficients = state.filesystem.read_model_coefficients(model_settings)
    model_spec = simulate.eval_coefficients(state, spec, coefficients, estimator)
    locals_dict = model_settings.CONSTANTS

    pnr_alts = land_use[land_use[model_settings.LANDUSE_PNR_SPACES_COLUMN] > 0]
    pnr_alts[model_settings.PNR_LOT_DEST_COLUMN] = pnr_alts.index.values

    choosers = filter_chooser_to_transit_accessible_destinations(
        state,
        tours_merged,
        pnr_alts,
        network_los,
        model_settings,
    )

    skims = setup_skims(model_settings, network_los, choosers)
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

    if estimator:
        estimator.write_coefficients(model_settings=model_settings)
        estimator.write_coefficients_template(model_settings=model_settings)
        estimator.write_spec(model_settings)
        estimator.write_model_settings(model_settings, model_settings_file_name)
        # in production, all choosers with a transit accessible destination are selected as choosers
        # but in estimation, it would only be those who actually reported a pnr lot
        # unclear exactly how to handle this, but for now, we will write all choosers
        estimator.write_choosers(choosers)
        estimator.write_alternatives(pnr_alts)

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

    if estimator:
        # careful -- there could be some tours in estimation data that are not transit accessible
        # but still reported a pnr location
        # warning! untested code!
        estimator.write_choices(choices)
        choices = estimator.get_survey_values(
            choices, "tours", model_settings.PNR_LOT_DEST_COLUMN
        )
        estimator.write_override_choices(choices)
        estimator.end_estimation()

    choices = choices.reindex(tours.index, fill_value=-1)

    tours[model_settings.PNR_LOT_DEST_COLUMN] = choices

    state.add_table("tours", tours)

    if trace_hh_id:
        state.tracing.trace_df(tours, label=trace_label, warn_if_empty=True)


@workflow.step
def tour_mode_choice_with_pnr(
    state: workflow.State,
    tours: pd.DataFrame,
    persons_merged: pd.DataFrame,
    network_los: los.Network_LOS,
    model_settings: TourModeWtihPNRComponentSettings | None = None,
    model_settings_file_name: str = "tour_mode_choice_with_pnr.yaml",
    trace_label: str = "tour_mode_choice_with_pnr",
) -> None:
    """
    Tour mode choice simulate with park-and-ride lot choice.

    This differs from the regular tour mode choice only minimally:
     - it includes the park-and-ride lot skims
     - it will loop park-and-ride lot choice with tour mode choice until all tours
        that select PNR go to a lot with capacity for them.

    FIXME this should probably be merged with actual tour_mode_choice code, but for now
    we will keep it separate to avoid having a separate version of ActivitySim code.
    """

    if model_settings is None:
        model_settings = TourModeWtihPNRComponentSettings.read_settings_file(
            state.filesystem,
            model_settings_file_name,
        )

    logsum_column_name = model_settings.MODE_CHOICE_LOGSUM_COLUMN_NAME
    mode_column_name = "tour_mode"
    segment_column_name = "tour_purpose"

    primary_tours = tours
    assert not (primary_tours.tour_category == "atwork").any()

    logger.info("Running %s with %d tours" % (trace_label, primary_tours.shape[0]))

    tracing.print_summary("tour_types", primary_tours.tour_type, value_counts=True)

    primary_tours_merged = pd.merge(
        primary_tours,
        persons_merged,
        left_on="person_id",
        right_index=True,
        how="left",
        suffixes=("", "_r"),
    )

    constants = {}
    # model_constants can appear in expressions
    constants.update(model_settings.CONSTANTS)

    skims = setup_skims(
        model_settings,
        network_los,
        primary_tours_merged,
        add_periods=False,
    )

    # don't create estimation data bundle if trip mode choice is being called
    # from another model step (i.e. tour mode choice logsum creation)
    if state.get_rn_generator().step_name != "tour_mode_choice_simulate":
        estimator = None
    else:
        estimator = estimation.manager.begin_estimation(state, "tour_mode_choice")
    if estimator:
        estimator.write_coefficients(model_settings=model_settings)
        estimator.write_coefficients_template(model_settings=model_settings)
        estimator.write_spec(model_settings)
        estimator.write_model_settings(model_settings, model_settings_file_name)
        # (run_tour_mode_choice_simulate writes choosers post-annotation)

    # FIXME should normalize handling of tour_type and tour_purpose
    # mtctm1 school tour_type includes univ, which has different coefficients from elementary and HS
    # we should either add this column when tours created or add univ to tour_types
    not_university = (primary_tours_merged.tour_type != "school") | ~(
        primary_tours_merged.is_university.astype(bool)
        if "is_university" in primary_tours_merged.columns
        else False
    )
    primary_tours_merged["tour_purpose"] = primary_tours_merged.tour_type.where(
        not_university, "univ"
    )

    # if trip logsums are used, run trip mode choice and append the logsums
    if model_settings.COMPUTE_TRIP_MODE_CHOICE_LOGSUMS:
        primary_tours_merged = get_trip_mc_logsums_for_all_modes(
            state,
            primary_tours_merged,
            segment_column_name,
            model_settings,
            trace_label,
        )

    choices_list = []
    for tour_purpose, tours_segment in primary_tours_merged.groupby(
        segment_column_name, observed=True
    ):
        logger.info(
            "tour_mode_choice_simulate tour_type '%s' (%s tours)"
            % (
                tour_purpose,
                len(tours_segment.index),
            )
        )

        # name index so tracing knows how to slice
        assert tours_segment.index.name == "tour_id"

        choices_df = run_tour_mode_choice_simulate(
            state,
            tours_segment,
            tour_purpose,
            model_settings,
            mode_column_name=mode_column_name,
            logsum_column_name=logsum_column_name,
            network_los=network_los,
            skims=skims,
            constants=constants,
            estimator=estimator,
            trace_label=tracing.extend_trace_label(trace_label, tour_purpose),
            trace_choice_name="tour_mode_choice",
        )

        tracing.print_summary(
            "tour_mode_choice_simulate %s choices_df" % tour_purpose,
            choices_df.tour_mode,
            value_counts=True,
        )

        choices_list.append(choices_df)

    choices_df = pd.concat(choices_list)

    if estimator:
        estimator.write_choices(choices_df.tour_mode)
        choices_df.tour_mode = estimator.get_survey_values(
            choices_df.tour_mode, "tours", "tour_mode"
        )
        estimator.write_override_choices(choices_df.tour_mode)
        estimator.end_estimation()

    tracing.print_summary(
        "tour_mode_choice_simulate all tour type choices",
        choices_df.tour_mode,
        value_counts=True,
    )

    # so we can trace with annotations
    assign_in_place(
        primary_tours,
        choices_df,
        state.settings.downcast_int,
        state.settings.downcast_float,
    )

    # update tours table with mode choice (and optionally logsums)
    all_tours = tours
    assign_in_place(
        all_tours,
        choices_df,
        state.settings.downcast_int,
        state.settings.downcast_float,
    )

    if (
        state.is_table("school_escort_tours")
        & model_settings.FORCE_ESCORTEE_CHAUFFEUR_MODE_MATCH
    ):
        all_tours = (
            school_escort_tours_trips.force_escortee_tour_modes_to_match_chauffeur(
                state, all_tours
            )
        )

    state.add_table("tours", all_tours)

    # - annotate tours table
    if model_settings.annotate_tours:
        annotate.annotate_tours(state, model_settings, trace_label)

    if state.settings.trace_hh_id:
        state.tracing.trace_df(
            primary_tours,
            label=tracing.extend_trace_label(trace_label, mode_column_name),
            slicer="tour_id",
            index_label="tour_id",
            warn_if_empty=True,
        )
