"""XR-77 model-level rig data for the Roblox handoff: identity, channels (with durations + gameplay rules), named
flight-mode poses, realistic physics, weapon / sensor systems, collision boxes, notes, and the Blender showcase
timeline (scrub it to watch every mechanism move).
"""
from .lib import *
from common import rig, poses

CH = [  # name, seconds 0->1, description, rules
    ('Canopy', 3.0, 'one-piece canopy opens (front rises 48 deg)',
     ['ground only, below 30 km/h', 'auto-close before takeoff']),
    ('GearUp', 5.5, 'landing gear retracts forward, then the gear doors close',
     ['only when airborne (no wheel touching the ground)', 'HighSpeed must be 0 before the gear comes down']),
    ('VTOL', 4.0, 'lift-fan doors + louvres, auxiliary inlets, roll-post doors, swivel nozzles turn 90 deg down; '
                  'lift-fan rotors spin', ['HighSpeed must be 0', 'max 280 km/h with VTOL deployed',
                                          'hover thrust comes from LiftFan_Exhaust + Exhaust_L/R + RollPost_L/R']),
    ('Flaps', 2.0, 'flaperons droop 25 deg + leading-edge flaps 15 deg', ['auto-on with VTOL and below 400 km/h']),
    ('HighSpeed', 6.0, 'outer wing panels droop 60 deg, inlet spikes slide aft',
     ['airborne only with GearUp = 1 and VTOL = 0', 'use above ~900 km/h (Mach 0.8)']),
    ('Speedbrake', 1.0, 'two dorsal speed brakes rise 50 deg', []),
    ('MainBays', 1.6, 'main weapon bay doors open (0-0.45), then the launchers drop 0.58 m (0.45-1)',
     ['stores in the main bays can only be released at 1', 'open bays break stealth (larger radar signature)']),
    ('SideBays', 1.2, 'side bay doors open, then the drop rails lower the SRM-4s', ['release only at 1']),
    ('Gun', 0.6, 'gun bay door drops open (barrels spin while firing)', ['fire only at 1']),
    ('BellyTurret', 2.5, 'belly doors open, the twin-gun turret lowers 0.8 m',
     ['deploy only when airborne (aimed down on the ground the guns would hit the runway)', 'aim only at 1']),
    ('DorsalLaser', 2.5, 'dorsal doors open, the Helios energy turret rises 0.62 m', ['fire only at 1']),
    ('Recon', 3.0, 'chine camera bays open + cameras lower; belly recon ball lowers 0.45 m', []),
    ('Countermeasures', 1.2, 'flare / chaff doors open, DIRCM turrets pop out, decoy cap opens and the towed decoy slides out',
     []),
    ('Emergency', 3.0, 'arrestor hook drops + ram-air turbine swings into the airflow', []),
    ('Radome', 3.0, 'radome swings open to the right (radar maintenance)', ['ground only, engines off']),
    ('EnginePanels', 2.5, 'four engine access panels swing up 110 deg', ['ground only, engines off']),
    ('Service', 2.0, 'avionics bay doors + engine service hatches open', ['ground only']),
    ('Refuel', 1.5, 'air-refuelling receptacle door opens', ['airborne, below 600 km/h']),
    ('EngineRun', 4.0, 'engines spooled up (fans spin)', ['0 = engines off']),
]

POSES = {
    'service':   dict(channels={'Canopy': 1, 'Radome': 1, 'EnginePanels': 1, 'Service': 1, 'Refuel': 1}, ground=True,
                      description='maintenance on the ground: canopy, radome, engine panels, service + refuel doors open'),
    'vtol':      dict(channels={'VTOL': 1, 'Flaps': 1, 'EngineRun': 1}, ground=True,
                      description='hover / vertical landing configuration (gear down)'),
    'cruise':    dict(channels={'GearUp': 1, 'EngineRun': 1}, ground=False, description='clean normal flight'),
    'highspeed': dict(channels={'GearUp': 1, 'HighSpeed': 1, 'EngineRun': 1}, ground=False,
                      description='supersonic dash: wing tips drooped, spikes aft'),
    'combat':    dict(channels={'GearUp': 1, 'EngineRun': 1, 'MainBays': 1, 'SideBays': 1, 'Gun': 1, 'BellyTurret': 1,
                                'DorsalLaser': 1, 'Countermeasures': 1, 'Speedbrake': 1},
                      inputs={'BellyTurret_Yaw': 35, 'BellyTurret_Pitch': 25, 'Laser_Yaw': -20, 'Laser_Pitch': -12},
                      ground=False, description='every weapon deployed'),
    'recon':     dict(channels={'GearUp': 1, 'EngineRun': 1, 'Recon': 1}, inputs={'Recon_Ball': 40, 'Recon_Head': 35},
                      ground=False, description='reconnaissance sensors deployed'),
    'landing':   dict(channels={'Flaps': 1, 'Speedbrake': 1, 'Emergency': 1, 'EngineRun': 1}, ground=True,
                      description='emergency landing: flaps, speed brakes, hook + RAT out'),
    'allground': dict(channels={'Canopy': 1, 'VTOL': 1, 'Flaps': 1, 'Speedbrake': 1, 'MainBays': 1, 'SideBays': 1,
                                'Gun': 1, 'BellyTurret': 1, 'DorsalLaser': 1, 'Recon': 1, 'Countermeasures': 1,
                                'Emergency': 1, 'Radome': 1, 'EnginePanels': 1, 'Service': 1, 'Refuel': 1},
                      ground=True, description='everything that can open on the ground opened at once (clash test)'),
    'controls':  dict(channels={}, inputs={'Aileron_L': 25, 'Aileron_R': -25, 'Tail_L': 20, 'Tail_R': 20,
                                          'Gear_NoseSteer': 60, 'Flaperon_L': 20, 'Flaperon_R': -20},
                      ground=True, description='control surfaces + nose-wheel steering at full deflection'),
}

SHOWCASE = [(1, 'rest'), (50, 'service'), (100, 'rest'), (150, 'vtol'), (200, 'cruise'), (250, 'highspeed'),
            (300, 'cruise'), (350, 'combat'), (400, 'recon'), (450, 'landing'), (500, 'rest')]


def planform_area():
    """reference wing area (m^2): the full planform minus nothing - centre body + wings."""
    import numpy as np
    xs = np.linspace(0, WING_TIP_X, 400)
    area = 0.0
    for i in range(len(xs) - 1):
        x = 0.5 * (xs[i] + xs[i + 1])
        le = min(wing_le(x), -12.4 + 0.0) if x < 0.0 else wing_le(x)
        # leading edge = the chine/body for small x, the wing LE further out
        ys = [y for y in np.linspace(-12.4, 7.4, 600) if W_(y) >= x]
        y0 = min([wing_le(x)] + ys) if ys else wing_le(x)
        area += (WING_TE - y0) * (xs[i + 1] - xs[i])
    return 2 * area


def build():
    rig.model(MODEL, 'XR-77 "Umbra"', 'aircraft',
              'Classified strike-reconnaissance VTOL fighter (original design, admin-only): SR-71-style chined '
              'Mach 3+ airframe with stealth shaping, adaptive-cycle engines with spiked inlets, hybrid-electric lift '
              'fan and swivel nozzles for VTOL, drooping wing tips for high-speed flight, internal + external weapons.',
              crew=1, admin_only=True, length_m=24.6, span_m=15.2, span_highspeed_m=12.8, height_m=5.15)
    for name, dur, desc, rules in CH:
        rig.channel(name, desc, dur, rules)
    rig.pose('rest', {}, {}, 'parked: gear down + gear doors open, everything else closed', ground=True)
    for k, p in POSES.items():
        rig.pose(k, p['channels'], p.get('inputs'), p['description'], p['ground'])
    area = round(planform_area(), 1)
    rig.physics(
        empty_mass_kg=19800, max_takeoff_mass_kg=36500, max_vtol_mass_kg=28000, internal_fuel_kg=11000,
        centre_of_mass_m_blender=[0.0, 1.2, 2.05], centre_of_mass_studs=[0.0, round(2.05 / 0.28, 3), round(1.2 / 0.28, 3)],
        wing_area_m2=area, wheelbase_m=round(MAIN_GEAR['y'] - NOSE_GEAR['y'], 2), main_gear_track_m=2 * MAIN_GEAR['x_wheel'],
        engines='2 x F-140 adaptive-cycle afterburning turbofan (fictional): 155 kN dry / 225 kN with afterburner each',
        lift_fan='hybrid-electric contra-rotating lift fan, 190 kN (fictional)', roll_posts='2 x 9 kN bleed-air jets',
        thrust_to_weight_combat=round(2 * 225000 / (30000 * 9.81), 2),
        top_speed='Mach 3.3 at 24,000 m (~3,500 km/h); 1,450 km/h at sea level',
        cruise_speed_kmh=950, stall_speed_kmh_clean=230, vtol_transition_max_kmh=280, ceiling_m=26000, range_km=4800,
        g_limits=[9.0, -3.0], roll_rate_deg_s=270, sustained_turn_deg_s=22,
        ground_clearance_m=round(Zb_(0.0) - 0.0, 2),
        roblox_speed_hint='the island is ~16,000 studs wide: compress speeds about 3x. Suggested game values: taxi '
                          '25 studs/s, takeoff 110 studs/s, cruise 260 studs/s, afterburner 650 studs/s, HighSpeed '
                          'mode up to 1,200 studs/s; hover/VTOL 0-80 studs/s.',
        roblox_assembly_hint='one invisible root part at the centre of mass (Massless=false, everything else massless) '
                             '+ the collision boxes; fly it with VectorForce / LinearVelocity + AlignOrientation; on '
                             'the ground use raycast suspension at the three wheel groups (rig.wheels).')
    rig.system('M77 Thunder rotary cannon', type='gun', muzzle='Muzzle_Gun', spin_group='Gun_Barrels', channel='Gun',
               rounds=1200, fire_rate_per_s=70, suggested_damage=18, range_studs=1500,
               note='7-barrel (fictional); door must be open (Gun = 1); barrels spin up 0.3 s before firing')
    rig.system('LRM-9 Lancer', type='missile', stores=['Store_LRM_L1', 'Store_LRM_L2'], launch_point='Launch_MainBay_L',
               channel='MainBays', lock_time_s=1.5, range_studs=3000, speed_studs_s=900, suggested_damage=220,
               note='radar-guided long-range missile (fictional); hide the store mesh on launch')
    rig.system('SRM-4 Viper', type='missile',
               stores=['Store_SRM_SideL', 'Store_SRM_SideR', 'Store_SRM_PylonL1', 'Store_SRM_PylonL2',
                       'Store_SRM_PylonR1', 'Store_SRM_PylonR2'],
               launch_points=['Launch_SideBay_L', 'Launch_SideBay_R', 'Launch_PylonL1', 'Launch_PylonL2',
                              'Launch_PylonR1', 'Launch_PylonR2'],
               channel='SideBays (side-bay rounds only; pylon rounds are always ready)', lock_time_s=0.6,
               range_studs=1200, speed_studs_s=750, suggested_damage=140, note='infrared dogfight missile (fictional)')
    rig.system('GBU-X Hammer', type='bomb', stores=['Store_GBU_R1', 'Store_GBU_R2'], launch_point='Launch_MainBay_R',
               channel='MainBays', guidance='glides to the point the EOTS / pilot designates (Sensor_EOTS)',
               blast_radius_studs=40, suggested_damage=400, note='precision glide bomb (fictional)')
    rig.system('Belly twin rotary guns', type='turret', lift='BellyTurret_Lift', yaw='BellyTurret_Yaw',
               pitch='BellyTurret_Pitch', spin_groups=['BellyTurret_Barrels_L', 'BellyTurret_Barrels_R'],
               muzzles=['Muzzle_Belly_L', 'Muzzle_Belly_R'], channel='BellyTurret', fire_rate_per_s=2 * 45,
               suggested_damage=12, range_studs=1200, note='360 deg traverse; elevation from 10 deg up to straight down (90 deg down)')
    rig.system('Helios energy turret', type='beam', lift='Laser_Lift', yaw='Laser_Yaw', pitch='Laser_Pitch',
               muzzle='Muzzle_Laser', channel='DorsalLaser', damage_per_s=120, range_studs=2500, overheat_s=6,
               cooldown_s=4, note='continuous beam (fictional); Laser material glows when firing')
    rig.system('Countermeasures', type='defence', flares=['Flares_L', 'Flares_R'], flares_per_side=36,
               dircm=['DIRCM_Top', 'DIRCM_Bot'], decoy='Decoy_Pod', channel='Countermeasures',
               note='flares + DIRCM defeat locks for ~2 s; the towed decoy pulls radar missiles away while deployed')
    rig.system('Sensors', type='sensors', radar='Sensor_Radar', eots='Sensor_EOTS', irst='Sensor_IRST',
               cameras=['Camera_Chine_L', 'Camera_Chine_R', 'Camera_ReconBall', 'Eye_Pilot'],
               note='radar lock cone 60 deg forward; Recon channel gives zoom camera views + marks targets')
    rig.system('VTOL', type='flight', channel='VTOL', thrust_points=['LiftFan_Exhaust', 'Exhaust_L', 'Exhaust_R'],
               roll_points=['RollPost_L', 'RollPost_R'],
               note='hover balance about the centre of mass (y 1.2 m): lift fan 4.8 m ahead, swivel nozzles 8.5 m behind '
                    '-> fan carries ~64 %, nozzles ~36 % of the weight; roll posts trim roll; transition below 280 km/h')
    rig.system('Stealth', type='signature', note='radar signature is low only with GearUp = 1 and MainBays / SideBays / '
                                                 'Gun / BellyTurret / DorsalLaser / Refuel / Recon all at 0')
    # collision proxies (model space at rest)
    B = [('Box_Nose', (-0.55, -12.40, 1.58), (0.55, -8.90, 2.42), None),
         ('Box_ForwardBody', (-1.05, -8.90, 1.44), (1.05, -4.50, 2.76), None),
         ('Box_Canopy', (-0.50, -9.30, 2.60), (0.50, -5.10, 3.34), 'Canopy'),
         ('Box_CentreBody', (-1.75, -4.50, 1.38), (1.75, 7.40, 2.88), None),
         ('Box_AftBody', (-1.20, 7.40, 1.45), (1.20, 10.85, 2.66), None),
         ('Box_Nacelle_L', (1.72, -4.60, 1.38), (3.18, 8.95, 2.83), None),
         ('Box_Nacelle_R', (-3.18, -4.60, 1.38), (-1.72, 8.95, 2.83), None),
         ('Box_InnerWing_L', (3.18, -1.70, 1.98), (5.20, 7.40, 2.22), None),
         ('Box_InnerWing_R', (-5.20, -1.70, 1.98), (-3.18, 7.40, 2.22), None),
         ('Box_OuterWing_L', (5.20, 1.84, 2.02), (7.60, 7.40, 2.18), 'Wingtip_L'),
         ('Box_OuterWing_R', (-7.60, 1.84, 2.02), (-5.20, 7.40, 2.18), 'Wingtip_R'),
         ('Box_Tail_L', (1.85, 6.05, 2.92), (2.55, 9.80, 5.14), 'Tail_L'),
         ('Box_Tail_R', (-2.55, 6.05, 2.92), (-1.85, 9.80, 5.14), 'Tail_R')]
    for nm, mn, mx, att in B:
        rig.box(nm, mn, mx, 'collision', bpy.data.objects[att] if att else None)
    for n in [
        'Rest pose = parked on the ground: gear DOWN with the gear doors OPEN, everything else closed. GearUp=1 retracts.',
        'Every store (missile / bomb) is its own group: hide it when it is fired and spawn the projectile at the '
        'matching Launch_* point; show it again on rearm.',
        'Interlocks: VTOL and HighSpeed are mutually exclusive; GearUp=1 blocks Canopy / Radome / EnginePanels / '
        'Service; EngineRun must be 0 for Radome / EnginePanels; the wing tips must never droop with the gear down '
        '(they would reach 0.07 m above the ground).',
        'Hinges that are not on a model axis (canted tails, swept leading-edge flaps, avionics doors) give their '
        'axis as a unit vector - rotate about that vector (CFrame.fromAxisAngle).',
        'Flaperons: Flaps channel sets the droop; roll / pitch input adds +/-20 deg on top (motion.control).',
        'Spin groups (fans, rotors, barrels, RAT) only spin while their channel is > 0 (fans: EngineRun).',
        'Lights: navigation red (left tip) / green (right tip) / white tails steady; strobes flash 1 Hz; '
        'formation strips glow dim green at night; landing + taxi lights on the nose gear (only with GearUp = 0).',
        'The canopy glass is tinted gold (Glass material, 0.45 transparency) - the cockpit is visible from outside.',
        'Admin-only aircraft: check admin status on the server before seating a pilot or firing any weapon.',
        'Scale: 87.9 studs long, 54.3 studs span - give it a clear 100 x 70 stud spawn pad.',
    ]:
        rig.note(n)
    bpy.context.scene['rig_preview_frames'] = '{}'
    poses.key_showcase(SHOWCASE)
