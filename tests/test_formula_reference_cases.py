"""Independent numerical reference cases for the 63-group formula audit."""
import copy
import json
import math
from pathlib import Path

import pytest
from matintegrity.registry import default_registry
from matintegrity.contracts import canonical_digest

BASELINES = json.loads((Path(__file__).parent / 'data/core_physics_valid_input_baselines.json').read_text(encoding='utf8'))['model_inputs']

def calculate(model_id, **changes):
    payload = copy.deepcopy(BASELINES[model_id])
    payload.update(changes)
    spec = default_registry()._models[model_id]
    result = spec.evaluator(spec.input_type.model_validate_json(json.dumps(payload)))
    assert result.status == 'computed'
    return payload, result.values

def test_group_06_nernst_against_activity_ratio():
    p, v = calculate('degradation.crevice_nernst_potential_history')
    for index, row in enumerate(v['potential_history']):
        quotient = p['species_activity_history']['Fe2+'][index] / p['species_activity_history']['Fe3+'][index]
        expected = p['standard_potential_V'][index] - 8.31446261815324 * p['temperature_K'][index] / 96485.33212331001 * math.log(quotient)
        assert row['potential_V'] == pytest.approx(expected, rel=1e-11)

def test_group_37_norton_nonreference_stress():
    _, v = calculate('creep.norton', stress_Pa=2e8)
    assert v['steady_creep_strain_rate_per_s'] == pytest.approx(3.2e-9)
    assert v['steady_creep_strain'] == pytest.approx(0.00032)

def test_group_39_time_fraction_independent_sum():
    _, v = calculate('creep.time_fraction')
    assert v['time_fraction_damage'] == pytest.approx(0.15)

def test_group_42_miner_independent_sum():
    _, v = calculate('fatigue.miner')
    assert v['damage'] == pytest.approx(0.15)
    assert v['damage_margin'] == pytest.approx(0.85)

def test_group_55_archard_volume_and_depth():
    _, v = calculate('degradation.archard_wear')
    assert v['wear_volume_m3'] == pytest.approx(5e-10, rel=1e-12, abs=0)
    assert v['mean_wear_depth_m'] == pytest.approx(5e-8, rel=1e-12, abs=0)

def test_group_51_rosenthal_points_against_closed_form():
    p, v = calculate('welding.rosenthal_3d_point_source_temperature')
    diffusivity = p['thermal_conductivity_W_m_K'] / (p['density_kg_m3'] * p['specific_heat_J_kg_K'])
    expected = []
    for x,y,z in zip(p['source_relative_x_m'], p['transverse_y_m'], p['depth_z_m']):
        radius = math.sqrt(x*x+y*y+z*z)
        expected.append(p['initial_temperature_K'] + p['absorbed_power_W']/(2*math.pi*p['thermal_conductivity_W_m_K']*radius)*math.exp(-p['travel_speed_m_s']*(x+radius)/(2*diffusivity)))
    assert v['temperature_K'] == pytest.approx(expected, rel=1e-12)

def test_group_10_scc_linear_velocity_time_integral():
    _, v = calculate('degradation.scc_crack_velocity_history')
    assert v['crack_advance_m_by_knot'][-1] == pytest.approx(2.5e-10, rel=1e-12, abs=0)

def test_group_16_coverage_attachment_exact_exponential():
    _, v = calculate('chemistry.caller_scale_coverage_kinetics')
    assert v['scale_history'][1]['covered_area_fraction'] == pytest.approx(1-0.9*math.exp(-0.001*50), rel=1e-12)

def test_group_17_layer_resistances_parallel_surface_flux():
    _, v = calculate('chemistry.layered_scale_diffusion_limit')
    expected = 0.15*0.25/50000 + 0.85*0.25/262500
    assert v['area_average_flux_limit_mol_m2_s'] == pytest.approx(expected, rel=1e-12)

def test_group_18_two_film_nonzero_flux():
    evidence = [{'source_id':'synthetic-input','origin':'synthetic','citation':'Authored two-film algebra case'}]
    _, v = calculate('degradation.wet_co2_two_film_transfer', temperature_K=298.15, co2_fugacity_Pa=10.0, bulk_co2star_mol_m3=2.0, evidence=evidence)
    assert v['signed_gas_to_liquid_CO2_flux_mol_m2_s'] == pytest.approx(4.0)
    assert v['interfacial_fugacity_Pa'] == pytest.approx(6.0)

def test_group_21_blind_slit_nonzero_sink_exact_cosh():
    evidence = [{'source_id':'synthetic-input','origin':'synthetic','citation':'Authored reaction-diffusion case'}]
    _, v = calculate('chemistry.crevice_steady_wall_sink', wall_transfer_velocity_m_s=1.0, mouth_concentration_mol_m3=2.0, evidence=evidence)
    assert v['concentration_mol_m3'] == pytest.approx([2*math.cosh(1-x)/math.cosh(1) for x in v['position_m']], rel=1e-12)
    assert v['inlet_flux_per_mouth_area_mol_m2_s'] == pytest.approx(2*math.tanh(1), rel=1e-12)

def test_group_32_leakage_bilinear_spatial_and_time_integral():
    p, v = calculate('fabrication.gasket_calibrated_leakage_history')
    def rate(f):
        delta=(500000+250000*f)/1e6
        return sum(0.001*delta*(1e-6+(1e-9-1e-6)*contact/1e6) for contact in (500000-100000*f,1000000-200000*f))
    assert v['cumulative_molar_leak_amount_mol'] == pytest.approx(10*(rate(0)+4*rate(0.5)+rate(1))/6,rel=1e-12)

def test_group_24_slit_momentum_exponential_and_signed_volume():
    p,v=calculate('corrosion.planar_slit_transient_hydraulic_history')
    flow=p['initial_volumetric_flow_m3_s']; volume=0.0
    for i,row in enumerate(v['interval_results']):
        aperture=p['aperture_by_interval_m'][i]; width=p['transverse_width_m']
        resistance=sum(12*p['dynamic_viscosity_Pa_s']*length/(width*h**3) for length,h in zip(p['cell_widths_m'],aperture))
        inertance=sum(p['density_kg_m3']*length/(width*h) for length,h in zip(p['cell_widths_m'],aperture))
        dt=p['time_s'][i+1]-p['time_s'][i]; steady=p['pressure_drop_by_interval_Pa'][i]/resistance; rate=resistance/inertance
        volume+=steady*dt+(flow-steady)*(1-math.exp(-rate*dt))/rate
        flow=steady+(flow-steady)*math.exp(-rate*dt)
        assert row['end_volumetric_flow_m3_s']==pytest.approx(flow,rel=1e-12)
    assert v['cumulative_signed_volume_history_m3'][-1]==pytest.approx(volume,rel=1e-12)

def test_group_30_piecewise_linear_contact_spring_solution():
    _,v=calculate('fabrication.nonlinear_bolt_gasket_contact')
    opening=1000/(100e6+12.5e6)
    assert v['opening_displacement_m']==pytest.approx(opening,rel=1e-8)
    assert v['gasket_force_N']==pytest.approx(1750-12.5e6*opening,rel=1e-8)

def test_group_31_prony_endpoint_force_balance_closed_form():
    p,v=calculate('fabrication.gasket_prony_joint_history')
    area=p['compression_area_m2']; kh=p['bolt_stiffness_N_m']*p['gasket_compression_height_m']; equilibrium=p['material']['equilibrium_modulus_Pa']
    strain=p['initial_compressive_strain']; initial=strain; branches=p['material']['prony_branches']; stresses=p['material']['initial_branch_stress_Pa']
    preload=area*(equilibrium*strain+sum(stresses))
    for i,row in enumerate(v['response_history'][1:],1):
        dt=p['elapsed_time_s'][i]-p['elapsed_time_s'][i-1]
        decays=[math.exp(-dt/b['relaxation_time_s']) for b in branches]
        weights=[b['modulus_Pa']*b['relaxation_time_s']/dt*(1-d) for b,d in zip(branches,decays)]
        rhs=preload+kh*initial-p['external_separating_force_N'][i]-p['bolt_stiffness_N_m']*p['bolt_free_length_change_m'][i]+area*sum(w*strain-q*d for w,q,d in zip(weights,stresses,decays))
        next_strain=rhs/(area*equilibrium+kh+area*sum(weights))
        stresses=[q*d+w*(next_strain-strain) for q,d,w in zip(stresses,decays,weights)]; strain=next_strain
        assert row['compressive_strain']==pytest.approx(strain,rel=1e-12)
        assert row['branch_stress_Pa']==pytest.approx(stresses,rel=1e-11)

def test_group_44_crossland_proportional_pure_shear():
    _,v=calculate('fatigue.multiaxial_crossland_proportional_limit_screen')
    assert v['crossland_parameter_Pa']==pytest.approx(50e6)
    assert v['maximum_hydrostatic_stress_Pa']==pytest.approx(0)

def test_group_46_j2_perfect_plastic_radial_return():
    p,v=calculate('fatigue.j2_prager_strain_history',strain_tensor_components=[[0,0,0,0,0,0],[0.003,0,0,0,0,0]])
    bulk=p['young_modulus_Pa']/(3*(1-2*p['poisson_ratio'])); pressure=bulk*0.003; yield_stress=p['initial_yield_stress_Pa']
    row=v['response_history'][-1]
    assert row['stress_tensor_components_Pa']==pytest.approx([pressure+2*yield_stress/3,pressure-yield_stress/3,pressure-yield_stress/3,0,0,0],rel=1e-12)
    assert row['von_mises_equivalent_stress_Pa']==pytest.approx(yield_stress,rel=1e-12)

def test_group_07_power_law_nonunit_exponent():
    spec=default_registry()._models['corrosion.power_law']
    result=spec.evaluator(spec.input_type(coefficient_m=0.002,exponent=0.5,exposure_s=900,reference_time_s=100))
    assert result.values['penetration_m']==pytest.approx(0.006)

def test_group_13_competing_solids_algebraic_solution():
    _,v=calculate('chemistry.competitive_solid_equilibrium')
    calcium=(5+math.sqrt(25+4*10.01))/2
    assert v['final_aqueous_concentration_mol_m3']==pytest.approx({'Ca2+':calcium,'CO3--':0.01/calcium,'SO4--':10/calcium,'Cl-':10},rel=2e-6)

def test_group_14_reversible_dissociation_riccati_solution():
    _,v=calculate('chemistry.crevice_aqueous_kinetic_network')
    forward=1e-4; reverse=1e-7; discriminant=math.sqrt(forward**2+4*reverse*forward)
    positive=2*forward/(forward+discriminant); negative=(-forward-discriminant)/(2*reverse)
    decay=math.exp(-discriminant*3600); extent=positive*(1-decay)/(1-positive/negative*decay)
    assert v['final_concentration_mol_m3_by_species']==pytest.approx({'H2CO3':1-extent,'H_plus':extent,'HCO3_minus':extent},rel=2e-7)

def test_group_19_cylindrical_one_cell_diffusion_exact_exponential():
    model='integration.wet_co2_cylindrical_transient_transport'; knots=copy.deepcopy(BASELINES[model]['knots'])
    for knot in knots:
        knot['species_boundaries'][0]['bulk_concentration_mol_m3']=0.2
        digest=canonical_digest({k:knot[k] for k in ('time_s','solution_film_thickness_m','species_boundaries','reaction_extent_rates')})
        knot['boundary_record_sha256']=digest
        for evidence in knot['boundary_evidence']: evidence['sha256']=digest
    _,v=calculate(model,knots=knots)
    inner=0.045; outer=0.0451; volume=math.pi*(outer**2-inner**2)
    rate=(2*math.pi*1e-9/math.log(outer/math.sqrt(inner*outer)))/volume
    expected=0.2-0.1*math.exp(-rate)
    assert v['history'][-1]['cell_concentration_mol_m3_by_species']['Fe2+'][0]==pytest.approx(expected,rel=2e-6)

def test_group_22_binary_ambipolar_diffusion_matrix_exponential():
    import numpy as np
    from scipy.linalg import expm
    _,v=calculate('transport.crevice_activity_corrected_nernst_planck_1d')
    rate=1.2e-9/0.005**2
    matrix=np.array([[-3*rate,rate,2*rate,0],[rate,-rate,0,0],[0,0,0,-1],[0,0,0,0]])
    expected=(expm(10*matrix)@np.array([100,100,100,1]))[:2]
    for values in v['state_history'][-1]['species_concentration_mol_m3_by_id'].values():
        assert values==pytest.approx(expected,rel=2e-8)

def test_group_45_itoh_zero_additional_hardening_life_limit():
    model='fatigue.itoh_nonproportional_strain_life'; parameter=copy.deepcopy(BASELINES[model]['parameter_request']);parameter['hardening_coefficient_alpha']=0.0
    _,v=calculate(model,parameter_request=parameter)
    assert v['itoh_strain_range']==pytest.approx(0.002)
    assert v['cycles_to_failure']==pytest.approx(5000,rel=1e-12)

def test_group_53_condensation_film_inventory_from_nonzero_flux():
    _,v=calculate('integration.wet_co2_gas_film_condensation_transfer_history')
    mass=1e-8*500*60*0.01801528
    assert v['final_water_areal_inventory_kg_m2']==pytest.approx(mass,rel=1e-12,abs=0)
    assert v['final_uniform_equivalent_film_thickness_m']==pytest.approx(mass/997,rel=1e-12,abs=0)

def test_group_15_precipitation_and_dissolution_thickness_ledger():
    _,v=calculate('chemistry.caller_surface_scale_kinetics')
    expected=1e-8+3600*(1e-6*0.3-5e-7*0.2)*2e-5
    assert v['final_scale_thickness_m']==pytest.approx(expected,rel=1e-12,abs=0)

def test_group_38_larson_miller_hours_conversion():
    spec=default_registry()._models['creep.larson_miller']
    result=spec.evaluator(spec.input_type(temperature_K=600,constant=20,rupture_time_s=360000))
    assert result.values['parameter_K']==pytest.approx(13200)
