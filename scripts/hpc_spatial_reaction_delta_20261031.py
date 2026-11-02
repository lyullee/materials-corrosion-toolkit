"""Small synthetic interval-source regressions; executed only by the HPC task runner."""
import argparse
import json
import math
from pathlib import Path
import traceback

import numpy as np
from pydantic import ValidationError
from matintegrity.contracts import canonical_digest
from matintegrity.spatial_piecewise_reaction import SpatialPiecewiseMassAction, build_spatial_reaction_callback


def payload():
    return dict(provider_id="synthetic.interval", provider_revision="1", network_id="A-B",
        species_ids=["A", "B"], charge_numbers=[1, 1], elemental_composition={"A":{"X":1},"B":{"X":1}},
        intervals=[dict(start_time_s=0.0,end_time_s=10.0),dict(start_time_s=10.0,end_time_s=20.0)],
        reactions=[dict(reaction_id="A-B",reactants={"A":1},products={"B":1},
            forward_rate_constants=[2.0,4.0],reverse_rate_constants=[0.5,1.0],
            forward_rate_constant_unit="1/s",reverse_rate_constant_unit="1/s",
            calibration_record_id="synthetic-rate",calibration_sha256="a"*64,
            calibration_evidence=[dict(source_id="synthetic-rate",origin="synthetic",citation="Synthetic rate reference",sha256="a"*64)])],
        concentration_activity_approximation_reviewed=True,usage_license_id="CC0-1.0",
        usage_rights_evidence=[dict(source_id="synthetic-rights",origin="synthetic",citation="Synthetic input",license_id="CC0-1.0")],
        computational_use_authorized=True,local_only_authorized=True)


def model(data=None):
    return SpatialPiecewiseMassAction.model_validate_json(json.dumps(payload() if data is None else data,allow_nan=False))


def rejected(fn):
    try:
        fn()
    except (ValueError,ValidationError):
        return
    raise AssertionError("invalid case accepted")


def boundaries():
    x=model(); f=build_spatial_reaction_callback(x); c=np.array([[1.,2.,0.],[2.,1.,0.]])
    for t,k,r in [(0.,2.,.5),(math.nextafter(10.,0.),2.,.5),(10.,4.,1.),(math.nextafter(10.,20.),4.,1.),(20.,4.,1.)]:
        expected=k*c[0]-r*c[1]
        np.testing.assert_array_equal(f(t,c),np.vstack((-expected,expected)))
    for t in (-1.,math.nextafter(0.,-1.),math.nextafter(20.,math.inf),math.inf,math.nan,True):
        rejected(lambda t=t:f(t,c))
    assert f.configuration_sha256==canonical_digest(x.model_dump(mode="json"))
    assert f.interval_support_s==(0.,20.)


def closure():
    f=build_spatial_reaction_callback(model())
    for n in (1,3,19):
        c=np.arange(2*n,dtype=float).reshape(2,n)/10
        result=f(10.,c)
        assert result.shape==(2,n)
        np.testing.assert_array_equal(result.sum(axis=0),np.zeros(n))
    for c in (np.ones(2),np.ones((3,2)),np.array([[-1.],[1.]]),np.array([[math.nan],[1.]])):
        rejected(lambda c=c:f(0.,c))
    cases=[]
    p=payload();p['charge_numbers']=[1,2];cases.append(p)
    p=payload();p['elemental_composition']['B']['X']=2;cases.append(p)
    p=payload();p['reactions'][0]['forward_rate_constant_unit']='mol/s';cases.append(p)
    p=payload();p['intervals'][1]['start_time_s']=11.;cases.append(p)
    p=payload();p['reactions'][0]['forward_rate_constants']=[1.];cases.append(p)
    p=payload();p['reactions'][0]['calibration_sha256']='b'*64;cases.append(p)
    for p in cases:rejected(lambda p=p:model(p))


def activity():
    p=payload();p.update(activity_provider_id="synthetic.gamma",activity_provider_revision="2",activity_configuration_sha256="b"*64)
    x=model(p)
    def gamma(t,c):return np.array([[2.,3.],[4.,5.]])
    gamma.provider_id="synthetic.gamma";gamma.provider_revision="2";gamma.configuration_sha256="b"*64
    f=build_spatial_reaction_callback(x,activity_coefficients=gamma); c=np.array([[1.,2.],[3.,4.]])
    extent=2*c[0]*np.array([2.,3.])-.5*c[1]*np.array([4.,5.])
    np.testing.assert_array_equal(f(0.,c),np.vstack((-extent,extent)))
    assert f.activity_configuration_sha256=="b"*64 and f.activity_provider_revision=="2"
    rejected(lambda:build_spatial_reaction_callback(x))
    rejected(lambda:build_spatial_reaction_callback(model(),activity_coefficients=gamma))
    gamma.configuration_sha256="c"*64
    rejected(lambda:build_spatial_reaction_callback(x,activity_coefficients=gamma))
    p['activity_provider_revision']=None;rejected(lambda:model(p))
    for field in ('concentration_activity_approximation_reviewed','computational_use_authorized','local_only_authorized'):
        p=payload();p[field]=False;rejected(lambda p=p:model(p))


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument('--task',choices=['boundaries','closure','activity'],required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
    result=dict(task=args.task,synthetic_only=True)
    try:
        globals()[args.task]();result['status']='passed'
    except Exception:
        result.update(status='failed',traceback=traceback.format_exc())
    Path(args.output).write_text(json.dumps(result,indent=2),encoding='utf-8')
    if result['status']!='passed':raise SystemExit(1)
