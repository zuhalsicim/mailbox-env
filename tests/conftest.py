import pytest

from mailgen.sampler import sample_instance

# The batch of instances the tests look at: five seeds on every level.
BATCH = [(level, seed) for level in (1, 2, 3) for seed in range(1, 6)]


@pytest.fixture(scope="session", params=BATCH, ids=lambda key: f"level{key[0]}-seed{key[1]}")
def instance(request):
    """One instance of the batch. A test that uses it runs once per instance and must not change it."""
    return sample_instance(*request.param)
