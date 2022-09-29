from otter.test_files import test_case
from pytest import approx

OK_FORMAT = False

name = "q1"
points = 2

@test_case()
def test_basic_tension(tension_norm):
    assert tension_norm(9.81, 3, 2) == approx(421, abs=1.1), "Your tension_norm function didn't handle the base case correctly."

# EOF