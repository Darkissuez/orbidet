import numpy as np
from pytest import fixture, mark, skip
from unittest.mock import patch
from pathlib import Path

from beyond.config import config
from beyond.dates.eop import Eop
from beyond.frames.stations import create_station
from beyond.io.tle import Tle
from beyond.propagators.keplernum import KeplerNum
from beyond.dates import Date, timedelta
from beyond.env.solarsystem import get_body
from beyond.env import jpl

np.set_printoptions(linewidth=200)


@fixture(autouse=True, scope="session")
def config_override():
    """Create a dummy config dict containing basic data
    """
    config.set("eop", "missing_policy", "pass")


@fixture
def common_env():
    with patch('beyond.dates.date.EopDb.get') as m:
        m.return_value = Eop(
            x=-0.00951054166666622, y=0.31093590624999734, dpsi=-94.19544791666682,
            deps=-10.295645833333051, dy=-0.10067361111115315, dx=-0.06829513888889051,
            lod=1.6242802083331438, ut1_utc=0.01756018472222477, tai_utc=36.0
        )
        yield


@fixture
def station(common_env):
    return create_station('Toulouse', (43.604482, 1.443962, 172.))


@fixture
def iss_tle(common_env):
    return Tle("""ISS (ZARYA)
1 25544U 98067A   18124.55610684  .00001524  00000-0  30197-4 0  9997
2 25544  51.6421 236.2139 0003381  47.8509  47.6767 15.54198229111731""")


@fixture
def molniya_tle(common_env):
    return Tle("""MOLNIYA 1-90
1 24960U 97054A   18123.22759647  .00000163  00000-0  24467-3 0  9999
2 24960  62.6812 182.7824 6470982 294.8616  12.8538  3.18684355160009""")


@fixture(params=["tle", "ephem"])
def orbit(request, iss_tle):

    orb = iss_tle.orbit()

    if request.param == "tle":
        return orb
    elif request.param == "ephem":
        start = Date(2018, 4, 5, 16, 50)
        stop = timedelta(hours=6)
        step = timedelta(seconds=15)

        return orb.ephem(start=start, stop=stop, step=step)
    elif request.param == "kepler":
        orb.propagator = KeplerNum(
            timedelta(seconds=60),
            get_body('Earth')
        )
        return orb


@fixture(params=["tle", "ephem"])
def molniya(request, molniya_tle):

    orb = molniya_tle.orbit()

    if request.param == "tle":
        return orb
    elif request.param == "ephem":
        start = Date(2018, 4, 5, 16, 50)
        stop = timedelta(hours=15)
        step = timedelta(minutes=1)

        return orb.ephem(start=start, stop=stop, step=step)


@fixture
def jplfiles():
    config.set('env', 'jpl', 'files', [
        str(Path(__file__).parent / "data" / "jpl" / "de403_2000-2020.bsp"),
        str(Path(__file__).parent / "data" / "jpl" / "pck00010.tpc"),
        str(Path(__file__).parent / "data" / "jpl" / "gm_de431.tpc"),
    ])

    jpl.create_frames()


def _skip_if_no_mpl():
    """Specific for dynamically skipping the test if matplotlib is not present
    as it is not a dependency of the library, but merely a convenience
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return True
    else:
        return False


def pytest_configure(config):
    """Declare the skip_if_no_mpl marker in pytest's '--markers' helper option
    This has no actual effect on the tests
    """
    config.addinivalue_line(
        "markers", "mpl: Test using matplotlib. Skipped if matplotlib not available"
    )
    config.addinivalue_line(
        "markers", "jpl: Test using beyond.env.jpl functions and classes"
    )


def pytest_runtest_setup(item):
    """This function is called for each test case.
    It looks if the test case has the skip_if_no_mpl decorator. If so, skip the test case
    """
    if _skip_if_no_mpl() and list(item.iter_markers(name="mpl")):
        skip("matplotlib not installed")
