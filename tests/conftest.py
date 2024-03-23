import pytest


@pytest.fixture()
def parameters():
    yield {
        "r_default": {
            "param_1": -1,
            "param_2": -1,
        },
        "r0_first": {
            "param_1": [1,2,3],
            "param_2": ["a", "b", "c"]
        }
    }


@pytest.fixture()
def multilevel_parameters():
    yield {
        "ignore_me": "for testing purposes",
        "r_default": {
            "temperature": 20,
            "param_1": -1,
            "param_2": -1,
            "param_3": -1,
            "param_4": -1,
        },
        "r0_temperature": {
            "temperature": [25,26,27],
        },
        "r1_corner": {
            "param_1": [1,2,3],
            "param_2": ["a", "b"],
        },
        "r2_first": {
            "param_3": [4,5,6],
            "param_4": ["d", "e", "f"]
        }
    }


@pytest.fixture()
def multilevel_zip_parameters():
    yield {
        "r_default": {
            "temperature": 20,
            "param_1": -1,
            "param_2": -1,
            "param_3": -1,
            "param_4": -1,
        },
        "r0_temperature": {
            "temperature": [25,26,27],
        },
        "r1_corner": {
            "param_1#zip_corner": [1,2,3],
            "param_2#zip_corner": ["a", "b", "c"],
        },
        "r2_first": {
            "param_3": [4,5,6],
            "param_4": ["d", "e", "f"]
        }
    }

@pytest.fixture()
def zip_error_parameters():
    yield {
        "r_default": {
            "temperature": 20,
            "param_1": -1,
            "param_2": -1,
            "param_3": -1,
            "param_4": -1,
        },
        "r0_temperature": {
            "temperature": [25,26,27],
        },
        "r1_corner": {
            "param_1#zip_corner": [1,2,3],
            "param_2#zip_corner": ["a", "b"],
        },
        "r2_first": {
            "param_3": [4,5,6],
            "param_4": ["d", "e", "f"]
        }
    }


@pytest.fixture()
def teardown_parameters():
    yield {
        "ignore_me": "for testing purposes",
        "r_default": {
            "temperature": 20,
            "param_1": -1,
            "param_2": -1,
            "param_3": -1,
            "param_4": -1,
        },
        "r0_temperature": {
            "temperature": [25,26,27],
        },
        "r1_corner": {
            "param_1": [1,2,3],
            "param_2": ["a", "b"],
        },
        "r2_first": {
            "param_3": [4,5,6],
            "param_4": ["d", "e", "f"]
        },

        "r2_second": {
            "param_3": [42, 43],
            "param_4": ["y", "z"]
        },

        "r2_teardown": {
            "param_3": 0,
            "param_4": "zzz"
        }
    }
