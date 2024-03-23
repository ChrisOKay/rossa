from __future__ import annotations

import dataclasses
import operator
from functools import reduce
from itertools import product
from typing import Optional

import numpy as np


def get_combinations(parameters: dict) -> list[dict]:
    """Create combinations from given parameters.

    This function generates a list of combinations from the given parameters. It first determines the maximum depth of
    the parameters and identifies the inner keys. It then generates the outer combinations by iterating over each level
    up to the maximum depth, creating a ParameterCombination object for each level, and adding the combinations to the
    outer combinations list.

    After generating the outer combinations, the function iterates over each outer combination, creating a new
    ParameterCombination object for each combination of the default parameters and the outer parameters, and extending
    the combinations list with the combinations from the ParameterCombination object.

    Args:
        parameters (dict): The parameters from which to generate combinations.

    Returns:
        list[dict]: A list of combinations generated from the parameters.
    """
    check_validity(parameters)
    setups, teardowns, yield_values, tests, outer_combinations = dataclasses.astuple(_extract_skeleton(parameters))
    # start with all outer setups
    combinations = [{"setup": setups}]
    for outer_combination in product(*outer_combinations):
        outer_parameters = reduce(operator.ior, outer_combination, {})
        outer_index = lambda i: outer_parameters[f"__index_{i}"]  # noqa E731
        # if a new loop has started, append teardown & setup
        for i, (setup, teardown) in enumerate(zip(setups, teardowns)):
            if i == 0:
                continue
            if outer_index(i) == 0 and outer_index(i-1) != 0:
                combinations.extend([{"teardown": teardown}])
                combinations.extend([{"setup": setup}])
        for i_inner, p in enumerate(tests):
            inner_parameters = p.copy()
            setup = inner_parameters.pop('setup', None)
            teardown = inner_parameters.pop('teardown', None)
            yield_test = inner_parameters.pop('yield', yield_values)
            all_parameters = outer_parameters | inner_parameters
            c = _get_indexed_combinations(ParameterCombination(all_parameters),
                                          len(setups), i_inner)
            for _c in c:
                _c["yield"] = yield_test
            combinations.extend([{"setup": setup}])
            combinations.extend(c)
            combinations.extend([{"teardown": teardown}])
    # append reversed teardowns
    combinations.extend([{"teardown": teardowns[::-1]}])
    return combinations


def check_validity(parameters: dict) -> None:
    """This function checks the validity of the provided parameters.

    It ensures that there is a main loop in the parameters and
    that outer loops do not consist of parallel loops.

    Args:
        parameters (dict): The parameters to be checked.

    Raises:
        ValueError: If no main loop is found or if an outer loop has of parallel loops.
    """
    try:
        outer_loop = parameters["main"]
    except KeyError:
        raise ValueError("No main loop found.")
    while any(next_loop := [v for v in outer_loop.values() if isinstance(v, dict)]):
        if len(next_loop) > 1 and any(
                isinstance(v, dict) for next_next_loop in next_loop for v in
                next_next_loop.values()):
            raise ValueError("Outer loops must not consist of parallel loops.")
        outer_loop = next_loop[0]

@dataclasses.dataclass
class LoopSkeleton:
    """A data class that represents the skeleton of the main loop.

    Attributes:
        setups (list): A list of setup operations to be performed.
        teardowns (list): A list of teardown operations to be performed after the loop.
        yield_values (Optional[list]): A list of values to be yielded by the loop.
        tests (list): A list of tests to be performed in the loop.
        outer_combinations (list): A list of combinations for the outer loop.
    """
    setups: list
    teardowns: list
    yield_values: Optional[list]
    tests: list
    outer_combinations: list


def _extract_skeleton(parameters: dict) -> LoopSkeleton:
    outer_combinations = []
    this_level = parameters["main"]
    setups = []
    teardowns = []
    yield_values = None
    i_level = 0
    # extract outer combinations, setups and teardowns
    while True:
        setups.append(this_level.pop('setup', None))
        teardowns.append(this_level.pop('teardown', None))
        yield_values = this_level.pop('yield_values', yield_values)
        p = {k: v for k, v in this_level.items() if not isinstance(v, dict)}
        c = _get_indexed_combinations(ParameterCombination(p), i_level)
        outer_combinations.append(c)
        next_level = [v for v in this_level.values() if isinstance(v, dict)]
        if not next_level:
            raise ValueError(
                "No inner loops found, see manual for construction of main loop.")
        if not any(isinstance(v, dict) for v in next_level[0].values()):
            tests = next_level
            for test in tests:
                test["setup"] = fill_template(parameters, test.get("setup", None))
                test["teardown"] = fill_template(parameters, test.get("teardown", None))
            break
        this_level = next_level[0]
        i_level += 1
    new_setups = [s for s in fill_template(parameters, setups)]
    new_teardowns = [t for t in fill_template(parameters, teardowns)]

    return LoopSkeleton(new_setups, new_teardowns, yield_values, tests, outer_combinations)


def fill_template(parameters: dict, values: Optional[list] = None) -> list:
    """This function fills the setup and teardown templates with the corresponding parameters.

    Args:
        parameters (dict): The parameters dictionary.
        values (list): The list of setup templates or teardown templates.

    Returns:
        new_values (list): The list of filled setup templates or teardown templates.
    """
    if values is None:
        return []
    values = flatten_multidimensional_list(values)
    new_values = []
    for value in values:
        if value is None or isinstance(value, dict):
            new_values.append(value)
            continue
        try:
            p = parameters[value]
            p.pop('setup', None)
            p.pop('teardown', None)
            new_values.append(ParameterCombination(p).combinations)
        except (TypeError, KeyError):
            raise ValueError(f"Template {value} not found in parameters.")
    return new_values

def flatten_multidimensional_list(lst: list) -> list:
    """Flatten a multidimensional list.

    This function flattens a multidimensional list by recursively iterating over the list and flattening each sublist.

    Args:
        lst (list): The multidimensional list to be flattened.

    Returns:
        list: The flattened list.
    """
    flat_list = []
    for item in lst:
        if isinstance(item, list):
            flat_list.extend(flatten_multidimensional_list(item))
        else:
            flat_list.append(item)
    return flat_list


def _get_indexed_combinations(parameter_combination: ParameterCombination,
                              i_level: int, i_inner: Optional[int] = None) -> list[dict]:
    """Add indices to combinations.

    This function adds indices to the combinations based on the level and whether the combinations are inner or not.
    For inner combinations, a list of indices is created and added to the combination under the key "__index".
    For outer combinations, the index is added to the combination under the key "__index_{level}".

    Args:
        parameter_combination (ParameterCombination): An instance of ParameterCombination class.
        i_level (int): The level of the combinations.
        i_inner (Optional[int]): The index of the inner combination. Defaults to None.

    Returns:
        list[dict]: The list of combinations with indices added.
    """
    combinations = parameter_combination.combinations
    for i in range(len(combinations)):
        combinations[i][f"__index_{i_level}"] = i
        if i_inner is not None:
            combinations[i]["__index"] = [combinations[i][f"__index_{level}"] for level in range(i_level + 1)]
            combinations[i]["__index_test"] = i_inner
    return combinations


class ParameterCombination:
    """Parameter combination via product and zips."""

    def __init__(self, parameters: dict):
        parameters = {k: (v if isinstance(v, list) else [v]) for k, v in
                      parameters.items()}
        self.names, self.values = parameters.keys(), parameters.values()
        self.shape = tuple(len(val) for val in self.values if len(val) > 1)

    @property
    def combinations(self) -> list[dict]:
        """Get parameter combinations.

        Returns: list of parameter combination dictionaries.
        """
        pure_names = [name.split("#")[0] for name in self.names]
        all_combinations = [
            dict(zip(pure_names, combination)) for combination in product(*self.values)
        ]
        i_valid = self.combination_index.flatten()
        return np.array(all_combinations)[i_valid].tolist()

    @property
    def combination_index(self) -> np.array:
        """Get index matrix for current combination.

        Returns: logical index matrix.
        """
        indices = [self.get_zip_index(name) for name in self.zip_groups]
        return np.logical_and.reduce(indices)

    def get_zip_index(self, zip_group: Optional[str] = None) -> np.array:
        """Extracts a boolean index for given zip group.

        This is a combination of slice (for non-zip) and range (for zip) operations.

        Args:
            zip_group: name of current zip group or None for full index
        Returns: A boolean index.
        """
        zip_index = np.zeros(self.shape).astype(bool)
        index_slicer = (
            range(ndim) if name and name == zip_group else slice(None)
            for name, ndim in zip(self.zip_groups, self.shape)
        )
        try:
            zip_index[tuple(index_slicer)] = True
        except IndexError:
            raise ValueError(
                (
                    "Mismatch in zip_group length. Please ensure that "
                    "zip groups have the same amount of values."
                )
            )
        return zip_index

    @property
    def zip_groups(self) -> list[Optional[str]]:
        """Extracts list of zip-modifier names with len(values) > 1.

        Returns: list of zip names or None (if no suitable modifier was found).
        """
        return [
            self.get_zip_group(name)
            for name, values in zip(self.names, self.values)
            if len(values) > 1
        ]

    @staticmethod
    def get_zip_group(name: str) -> Optional[str]:
        """Extracts zip-modifier name.

        Returns: zip name or None (if no suitable modifier was found).
        """
        match = name.split("#zip_")
        return match[1].split("#")[0] if len(match) > 1 else None
