import logging

import numpy as np
import pandas as pd

from activitysim.core import (
    los,
    workflow,
)

from activitysim.abm.models.park_and_ride_lot_choice import (
    ParkAndRideLotChoiceSettings
)

logger = logging.getLogger(__name__)


@workflow.step
def transit_lot_connectivity(
    state: workflow.State,
    land_use: pd.DataFrame,
    network_los: los.Network_LOS,
    model_settings: ParkAndRideLotChoiceSettings | None = None,
    model_settings_file_name: str = "park_and_ride_lot_choice.yaml",
) -> None:
    """
    This model flags landuse zones that have transit access.

    This output is used by the park and ride lot choice model to limit
    the choice set to only tours that have transit access at their destination.
    """
    if model_settings is None:
        model_settings = ParkAndRideLotChoiceSettings.read_settings_file(
            state.filesystem,
            model_settings_file_name,
        )

    skim_dict = network_los.get_default_skim_dict()
    unique_destinations = land_use.index.values
    unique_lot_locations = land_use[
        land_use[model_settings.LANDUSE_PNR_SPACES_COLUMN] > 0
    ].index.values
    transit_accessible = np.full(
        shape=len(unique_destinations), fill_value=False, dtype=bool
    )

    for skim_name in model_settings.TRANSIT_SKIMS_FOR_ELIGIBILITY:
        if "__" in skim_name:
            # If the skim name contains '__', it is a 3D skim
            # we need to pass the skim name as a tuple to the lookup method, e.g. ('WALK_TRANSIT_IVTT', 'MD')
            skim_name = tuple(skim_name.split("__"))

        # Filter choosers to only those with destinations that have transit access
        # want to check whether ANY of the lot locations have transit access to EVERY destination
        transit_accessible_i = [
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
        transit_accessible = np.logical_or(transit_accessible, transit_accessible_i)

    land_use[model_settings.LANDUSE_COL_FOR_PNR_ELIGIBLE_DEST] = transit_accessible

    logger.info(
        f"Marking {transit_accessible.sum()} of {len(land_use)} zones as transit accessible for PNR/ KNR/ TNCNR lot choice"
    )
    state.add_table("land_use", land_use)