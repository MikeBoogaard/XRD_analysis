"""A malformed configuration must never promote provisional science to verified."""
import json
import pytest
from rsm_toolkit import (RSMError, CoplanarGeometry, VectorGeometry,
                         RSMConfiguration, load_configuration)


@pytest.mark.parametrize("value",["false","true",0,1,None])
def test_verification_requires_boolean(value):
    with pytest.raises(RSMError,match="boolean"):
        CoplanarGeometry(calibration_verified=value,calibration_reference="example")
    with pytest.raises(RSMError,match="boolean"):
        VectorGeometry((0,1,0),(0,1,0),(),(),calibration_verified=value,calibration_reference="example")
    with pytest.raises(RSMError,match="boolean"):
        RSMConfiguration(allow_provisional=value)


@pytest.mark.parametrize("payload",['{', '[]', 'null', '{"geometry": "coplanar"}',
                                     '{"geometry": {"type":"coplanar", "calibration_verified":"false"}}'])
def test_invalid_configuration_has_clear_error(tmp_path,payload):
    path=tmp_path/"config.json"
    path.write_text(payload)
    with pytest.raises(RSMError):load_configuration(path)


def test_false_is_not_verified(tmp_path):
    path=tmp_path/"config.json"
    path.write_text(json.dumps({"geometry":{"type":"coplanar","calibration_verified":False},"allow_provisional":True}))
    c=load_configuration(path)
    assert c.geometry.calibration_verified is False
    assert c.allow_provisional is True
