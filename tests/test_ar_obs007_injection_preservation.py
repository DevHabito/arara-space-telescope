"""Synthetic-only regressions for AR-OBS007-P02, no data downloads."""

import hashlib
import json
import unittest

import numpy as np

from scripts.ar_obs007_injection_preservation import (
    DEPTH, DURATION, EMBARGO_SIDE, FIRST_START, FLANK, LAMBDA,
    PROTOCOL, SHIFT, SPACING, METHODS,
    analyze, assemble_eligible, digest, fixed_events, injection_mask,
    partition, recovery, ridge_predict,
)


def source_fixture():
    ids=np.arange(100,112,dtype=np.int32)
    rng=np.random.default_rng(71)
    order=rng.permutation(len(ids))
    cube=np.zeros((12,2,2),dtype=float)
    for i in range(12):
        cube[i]=np.array([[10.0+i*.1,5.0+i*.05],[1.0,3.0]])
    cube=cube[order]
    choose=np.array([[True,True],[False,False]])
    lc={
        "cadences":ids[::-1],
        "rows":len(ids),
        "time":1500+np.arange(len(ids))[::-1],
        "quality":np.zeros(12,dtype=int),
        "sap_flux":np.array([15+i*.15 for i in range(12)][::-1],dtype=float),
    }
    vectors={
        "cadences":ids[::-1],
        "midtime":1500+np.arange(len(ids))[::-1],
        "quat_bins":np.full(12,60.),
        "quat_stddev":np.ones((12,4))*.000001,
        "median_features":np.column_stack((
            ids[::-1]*1.e-7,
            np.sin(ids[::-1])*1.e-7,
            np.cos(ids[::-1])*1.e-7,
        )),
    }
    return (ids[order],np.zeros(12,dtype=int),
            1500+np.arange(len(ids))[order],cube,choose,lc,vectors)


def synthetic_data(n=5000, with_quats=True, seed=20261121):
    rng=np.random.default_rng(seed)
    pld=np.maximum(
        1/21 + rng.normal(scale=.003,size=(n,21)), .001
    )
    pld=pld/pld.sum(axis=1)[:,None]
    q=rng.normal(size=(n,3))
    # Q describes real photometric variation only when with_quats is true.
    base=.6*pld[:,0]-.8*pld[:,1]
    if with_quats:
        base+=.7*q[:,0]-.5*q[:,1]
    base+=rng.normal(scale=.1,size=n)
    sap=1000*(1+0.012*base)
    return {"cadences":np.arange(150000,150000+n,dtype=int),
            "sap":sap,"pixels":pld*sap[:,None],
            "pld":pld,"quat":q}


class InjectionPreservationTests(unittest.TestCase):
    def test_frozen_constants(self):
        self.assertEqual(PROTOCOL,"AR-OBS007-P02")
        self.assertEqual(DEPTH,.005)
        self.assertEqual(DURATION,12)
        self.assertEqual(FLANK,12)
        self.assertEqual(EMBARGO_SIDE,120)
        self.assertEqual(SHIFT,97)
        self.assertEqual(LAMBDA,10)
        self.assertEqual(FIRST_START,250)
        self.assertEqual(SPACING,500)
        self.assertEqual(len(METHODS),4)

    def test_exact_cadence_join_and_pld_fractions(self):
        out=assemble_eligible(*source_fixture())
        self.assertEqual(out["counts"]["eligible"],12)
        np.testing.assert_array_equal(out["cadences"],np.arange(100,112))
        self.assertEqual(out["pld"].shape,(12,2))
        np.testing.assert_allclose(np.sum(out["pld"],axis=1),1.0)

    def test_sap_integrity_gate_rejects_source_mismatch(self):
        fixture=list(source_fixture())
        fixture[5]["sap_flux"][0]*=1.02
        with self.assertRaises(ValueError):
            assemble_eligible(*fixture)

    def test_quality_flag_exclusions_are_not_imputed(self):
        fixture=list(source_fixture())
        fixture[1][0]=32
        cadence=int(fixture[0][0])
        fixture[5]["quality"][np.where(fixture[5]["cadences"]==cadence)[0][0]]=32
        out=assemble_eligible(*fixture)
        self.assertEqual(out["counts"]["eligible"],11)

    def test_frozen_events_only_on_consecutive_complete_windows(self):
        ids=np.arange(10000,12000)
        starts=fixed_events(ids)
        self.assertEqual(starts,[250,750,1250,1750])
        broken=ids.copy()
        broken[745:]+=4
        self.assertEqual(fixed_events(broken),[250,1250,1750])
        m=injection_mask(2000,starts)
        self.assertEqual(np.count_nonzero(m),4*DURATION)
        with self.assertRaises(ValueError):
            injection_mask(100,[0,4])

    def test_ridge_uses_only_training_data(self):
        rng=np.random.default_rng(3)
        tr=rng.normal(size=(100,4))
        yy=rng.normal(size=100)
        te=rng.normal(size=(20,4))
        a=ridge_predict(tr,yy,te)
        b=ridge_predict(tr,yy,te)
        np.testing.assert_array_equal(a,b)

    def test_partition_embargo_and_training_blocks(self):
        split=partition(5000)
        self.assertEqual(split["train_end"],2880)
        self.assertEqual(split["test_start"],3120)
        self.assertEqual(split["test_rows"],1880)
        self.assertEqual(split["embargo"],240)
        self.assertTrue(split["evaluable"])

    def test_informative_quaternions_reduce_heldout_scatter(self):
        out=analyze(synthetic_data())
        self.assertGreater(out["incremental_squared_rms_gain"],.05)
        self.assertEqual(out["hypotheses"]["H1_incremental_short_timescale"],
                         "SUPPORTED_IN_SELECTED_PRODUCTS")
        self.assertEqual(out["hypotheses"]["H3_shift_control"],
                         "SUPPORTED_IN_SELECTED_PRODUCTS")
        self.assertTrue(out["injection"]["max_normalized_pld_fraction_change"]<=1e-12)

    def test_idealized_injection_is_recovered_as_advertised(self):
        out=analyze(synthetic_data())
        self.assertGreaterEqual(out["injection"]["train_events"],3)
        self.assertGreaterEqual(out["injection"]["test_events"],3)
        self.assertAlmostEqual(
            out["injection_recovery"]["RAW"]["median_recovered_fraction"],
            1.0,places=10
        )
        self.assertEqual(
            out["hypotheses"]["H2_injection_preservation"],
            "SUPPORTED_IN_SELECTED_PRODUCTS",
        )

    def test_uninformative_quaternion_should_not_add_value(self):
        out=analyze(synthetic_data(with_quats=False))
        self.assertEqual(out["hypotheses"]["H1_incremental_short_timescale"],
                         "NOT_SUPPORTED_IN_SELECTED_PRODUCTS")

    def test_not_evaluable_injections_are_not_reported_as_failures(self):
        out=analyze(synthetic_data(n=2000))
        self.assertEqual(out["hypotheses"]["H2_injection_preservation"],"NOT_EVALUABLE")

    def test_recovery_of_fixed_differential_imprint(self):
        flux=np.ones(200)*1000
        difference=np.zeros(200)
        difference[50:62]=-DEPTH
        result=recovery(difference,flux,[50],1000)
        self.assertAlmostEqual(result["median_recovered_fraction"],1.0,places=12)

    def test_digest_is_canonical(self):
        self.assertEqual(digest({"b":5,"a":1}),
                         hashlib.sha256(b'{"a":1,"b":5}').hexdigest())


if __name__=="__main__":
    unittest.main()
