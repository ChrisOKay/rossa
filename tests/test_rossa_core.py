import pytest

from rossa.parameters import get_combinations
from rossa.rossa import Rossa


@pytest.fixture()
def full_integration_parameters():
    yield {
        "plugins": ["g-ic"],
        "standard_test": {
            "temperature": 20,
            "param_1": 42,
            "param_2": 42,
            "param_3": 42,
            "param_4": 42,
        },

        "what to do at the end of the test": {
            "temperature": 0,
            "param_1": 0,
            "param_2": 0,
            "param_3": 0,
            "param_4": 0,
        },
        "main": {
            "setup": [{"hardware": "initialize"}],
            "teardown": [{"hardware": "reset"}],
            "thermostat": {
                "temperature": [25, 26, 27],
                "corner": {
                    "param_1#zip_corner": [1, 2, 3],
                    "param_2#zip_corner": ["a", "b", "c"],
                    "tests": {
                        "teardown": ["what to do at the end of the test"],
                        "first": {
                            "setup": ["standard_test"],
                            "param_3": [4, 5, 6],
                            "param_4": ["d", "e", "f"],
                            "yield": ["voltage"],
                            "teardown": ["what to do at the end of the test"],
                        },
                        "second": {
                            "setup": ["standard_test"],
                            "param_1": [7],
                            "param_4": ["t", "b"],
                        },
                        "third": {
                            "setup": ["standard_test"],
                            "param_3": [7],
                            "param_4": ["t", "b"],
                            "teardown": ["what to do at the end of the test"],
                        },
                        "fourth": {
                            "yield": ["current"],
                        }
                    }
                },
            },
        },
    }


def test_rossa_parameters_are_interpreted_as_expected(full_integration_parameters):
    rossa = Rossa(full_integration_parameters)
    assert rossa.parameters == full_integration_parameters


def test_parameters_get_combined_correctly(full_integration_parameters):
    combinations = get_combinations(full_integration_parameters)
    n_teardowns = 0
    n_setups = 0
    i_test_max = 0
    index_max = [0, 0, 0, 0, 0]
    for c in combinations:
        i_test_max = max(i_test_max, c.get("__index_test", 0))
        for i in range(len(index_max)):
            index_max[i] = max(index_max[i], c.get(f"__index_{i}", 0))
        if "teardown" in c:
            n_teardowns += 1
        if "setup" in c:
            n_setups += 1
        # assert that param_1 gets merged correctly and overwrites corner in second test
        if c.get("__index_test", 0) == 1:
            assert c["param_1"] == 7
    assert n_setups == n_teardowns
    assert n_setups > 10
    assert i_test_max == 3  # four test 0..3
    # singleton main, three corner 0..2, three thermostat 0..2,
    # singleton test wrapper for teardown, max nine test param 0..8
    assert index_max == [0, 2, 2, 0, 8]


def test_setup_and_teardown_values_get_replaced_by_appropriate_parameters(full_integration_parameters):
    combinations = get_combinations(full_integration_parameters)
    for c in combinations:
        assert "standard_test" not in str(c.get("setup", []))


def test_parameters_with_parallel_outer_loops_raise_error():
    with pytest.raises(ValueError):
        get_combinations({
            "main": {
                "setup": [{"hardware": "initialize"}],
                "teardown": [{"hardware": "reset"}],
                "outer": {
                    "inner": {
                        "setup": ["standard_test"],
                        "param_1": [1, 2, 3],
                    },
                    "inner2": {
                        "setup": ["standard_test"],
                        "param_2": [4, 5, 6],
                    },
                },
                "second_outer": {
                    "inner": {
                        "setup": ["standard_test"],
                        "param_1": [1, 2, 3],
                    },
                    "inner2": {
                        "setup": ["standard_test"],
                        "param_2": [4, 5, 6],
                    },
                },
            },
        })


def test_parameters_raise_error_if_no_main_loop_is_found():
    with pytest.raises(ValueError):
        get_combinations({
            "outer": {
                "inner": {
                    "setup": ["standard_test"],
                    "param_1": [1, 2, 3],
                },
            },
        })


def test_parameters_raise_error_if_main_loop_contains_no_further_loop():
    with pytest.raises(ValueError):
        get_combinations({
            "main": {
                "setup": ["standard_test"],
                "param_1": [1, 2, 3],
            },
        })


def test_parameters_raise_error_if_zip_groups_have_uneven_length():
    with pytest.raises(ValueError):
        get_combinations({
            "main": {
                "faulty": {
                    "param_1#zip_faulty": [1, 2, 3],
                    "param_2#zip_faulty": ["a", "b"],
                }
            },
        })


def test_parameters_raise_error_if_setup_can_not_be_filled():
    with pytest.raises(ValueError):
        get_combinations({
            "main": {
                "faulty": {
                    "setup": ["unknown"],
                    "param_1": [1, 2, 3],
                }
            },
        })
