"""Utility functions for SyntheMol reactions."""
import json
import pandas as pd
from pathlib import Path

from SyntheMol.constants import REAL_BUILDING_BLOCK_ID_COL, SMILES_COL
from SyntheMol.reactions import Reaction


def set_allowed_reaction_smiles(
        reactions: list[Reaction],
        reaction_to_reactant_to_building_blocks: dict[int, dict[int, set[str]]]
) -> None:
    """Sets the allowed SMILES for each reactant in each Reaction in a list of Reactions.

    Note: Modifies Reactions in place.

    :param reactions: A list of Reactions whose allowed SMILES will be set.
    :param reaction_to_reactant_to_building_blocks: A dictionary mapping from reaction ID
                                                    to reactant index to a set of allowed SMILES.
    """
    for reaction in reactions:
        for reactant_index, reactant in enumerate(reaction.reactants):
            reactant.allowed_smiles = reaction_to_reactant_to_building_blocks[reaction.id][reactant_index]


def load_and_set_allowed_reaction_smiles(
        reactions: list[Reaction],
        reaction_to_reactant_to_building_blocks_path: Path,
        building_blocks_path: Path,
        building_blocks_id_column: str = REAL_BUILDING_BLOCK_ID_COL,
        building_blocks_smiles_column: str = SMILES_COL
) -> None:
    """Loads a mapping of allowed building blocks for each reaction and sets the allowed SMILES for each reaction.

    :param reactions: A list of Reactions whose allowed SMILES will be set.
    :param reaction_to_reactant_to_building_blocks_path: Path to a JSON file mapping from reaction ID
                                                            to reactant index to a set of allowed building block IDs.
    :param building_blocks_path: Path to a CSV file mapping from building block ID to SMILES.
    :param building_blocks_id_column: The name of the column in the building blocks file containing building block IDs.
    :param building_blocks_smiles_column: The name of the column in the building blocks file containing SMILES.
    """
    # Load building blocks
    building_blocks = pd.read_csv(building_blocks_path, sep='\t')

    # Create mapping from building block ID to SMILES
    building_block_id_to_smiles = dict(zip(
        building_blocks[building_blocks_id_column],
        building_blocks[building_blocks_smiles_column]
    ))

    # Load allowed building blocks for each reaction
    with open(reaction_to_reactant_to_building_blocks_path) as f:
        reaction_to_reactant_to_building_block_ids: dict[int, dict[int, set[int]]] = json.load(f)

    # Convert building block IDs to SMILES
    reaction_to_reactant_to_building_blocks = {
        reaction: {
            reactant: {
                building_block_id_to_smiles[building_block_id]
                for building_block_id in building_block_ids
                if building_block_id in building_block_id_to_smiles
            }
            for reactant, building_block_ids in reactant_to_building_block_ids.items()
        } for reaction, reactant_to_building_block_ids in reaction_to_reactant_to_building_block_ids.items()
    }

    # Set allowed building blocks for each reaction
    set_allowed_reaction_smiles(
        reactions=reactions,
        reaction_to_reactant_to_building_blocks=reaction_to_reactant_to_building_blocks
    )
