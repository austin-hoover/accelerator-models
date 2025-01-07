from sns_orbit_models import SNS_RING
from sns_orbit_models import SNS_LINAC
from sns_orbit_models import SNS_BTF



def test_sns_ring():
    model = SNS_RING()
    model.add_all_aperture_and_collimator_nodes()


def test_sns_linac():
    model = SNS_LINAC()


def test_sns_btf():
    model = SNS_BTF()