# Blender models for Survival Island

Every model is built 100 % from Python scripts (Blender 5.2.2) and ships as a **Roblox handoff package** in
`../exports/<Model>/` — see `../docs/MODEL_HANDOFF_STANDARD.md`. Give that folder to the Roblox chat.

| Model | Build | Package |
|---|---|---|
| XR-77 "Umbra" VTOL strike-recon fighter | `bpy-run blender/build_xr77.py` | `exports/XR77_Umbra/` |
| TX-6 "Bastion" armoured super-SUV | `bpy-run blender/build.py` | `exports/TX6_Bastion_Roblox.fbx` + rig JSON (older format) |

---

# XR-77 "Umbra" — how to use these files

**What this is:** an original, classified-prototype-style strike / reconnaissance fighter: SR-71-style chined Mach-3
airframe + next-generation stealth shaping, VTOL (lift fan + swivel nozzles), drooping wing tips for high speed, and
an admin weapons fit. Pictures: `../renders/xr77/`. Roblox package: `../exports/XR77_Umbra/`.

## Open it
Open `XR77_Umbra.blend` in Blender 5.2 and press **Space**: the showcase timeline (frames 1–500) plays
parked → service (canopy, radome, engine panels open) → VTOL → cruise (gear up) → high speed (tips droop) → combat
(every weapon out) → recon → emergency landing → parked.

## The 10 advanced features
1. **VTOL:** hybrid-electric contra-rotating lift fan (rear-hinged top door, folding belly doors, steering louvres),
   auxiliary inlets, two-bearing swivel nozzles that turn the exhaust 90° down, wing roll-post jets (`LiftFan_*`, `Nozzle_*`, `RollPost_*`)
2. **Variable geometry:** outer wing panels droop 60° (XB-70 style) on piano hinges, leading-edge flaps, flaperons (`Wingtip_*`, `LEFlap_*`, `Flaperon_*`)
3. **Adaptive engines:** translating inlet shock spikes, fan faces, cores with FADEC / pumps / pipes / harnesses, afterburner, heat shields (`Spike_*`, `Engine_*`)
4. **Internal weapon bays:** two main bays with drop launchers (LRM-9 missiles, GBU-X glide bombs), two side bays (SRM-4) (`MainBay_*`, `SideBay_*`, `Store_*`)
5. **Sensors:** AESA radar under an opening radome, chin EO targeting window, IRST dome, 5 IR apertures, air-data probes, antennas
6. **Deployable recon:** chine camera bays (cameras lower out) + belly recon ball turret (`Recon_*`)
7. **Cockpit:** one-piece gold canopy, ejection seat + harness, panoramic display, HUD, side-stick, throttle, consoles, warnings, oxygen
8. **Engine / exhaust:** swivel nozzles with petals + actuators, turbine exit + flameholders, burnt-titanium shrouds, ceramic decoy stinger
9. **Transforming configuration:** VTOL ↔ cruise ↔ high speed through the channels / poses above
10. **Defensive / emergency:** flare + chaff magazines, pop-out DIRCM laser turrets, towed decoy, arrestor hook, ram-air turbine, nav / strobe / formation lights

Admin weapons: M77 7-barrel rotary cannon (chin blister), belly turret with twin rotary guns, pop-up "Helios" energy
turret, wing pylons with twin missile rails — all fictional.

## Rebuild / check / render / export
```
bpy-run blender/build_xr77.py                       # rebuild the .blend (~35 s)
bpy-run blender/check_model.py xr77                 # floating parts + clashes in every pose + budget (~5 s)
bpy-run blender/render_model.py xr77 out.png "front34;rear34" 960 32 combat
bpy-run blender/export_handoff.py xr77              # -> exports/XR77_Umbra/ (verified by re-importing the FBX)
```

---

# TX-6 "Bastion" — how to use these files

**What this is:** an original armoured military super-SUV (Terradyne Gurkha *inspired*) for Survival Island,
built 100 % from Python scripts in Blender 5.2.2. Pictures are in `../renders/`.

## Open it
Open `TX6_Bastion.blend` in Blender 5.2. Press **Space** to play the showcase animation (frames 1–180):
armour flips up, missile pods rise, the sensor mast raises, the turret turns and the barrels spin, then the doors,
lockers and spare-wheel carrier open. Scrub to frame **140** to see everything deployed.

## The 10 special systems
1. Rotating roof turret with a sling seat for a second player (`Turret_Rotor`, `Seat_Gunner`)
2. Fictional 6-barrel rotary cannon with ammo box + feed chute; barrels spin (`Turret_Barrels`)
3. Concealed missile bays: roof hatches open, lifts raise 6-tube pods that tilt up (`Missile_*`)
4. Deployable armour: windshield shield + 4 flip-up window shutters with vision slits (`Deploy_*`)
5. Folding/telescoping sensor mast with spinning radar head + EO/IR ball (`Sensor_*`)
6. Side equipment lockers: left = slide-out recon drone + cases, right = ammo / medical / comms (`Locker_*`)
7. Heavy front bumper: winch, red D-ring shackles, grille guard, LED bars, fog lamps, skid plate
8. Military lighting: LED headlights, NATO blackout + IR lamps, roof light bar, amber beacons, searchlight,
   work floods, caged tail lamps
9. Double-wishbone suspension with coil-overs, extra dampers, CV shafts, brakes, 47" tyres on beadlock rims
10. Rear equipment: swing-out spare carrier, ladder, jerry can, pintle hitch, tools on the sides

## Rebuild / check / export (for Claude or anyone with Python + bpy)
```
bpy-run blender/build.py                 # rebuild the .blend from the scripts (~3 s)
bpy-run blender/checks.py deploy         # floating parts, collisions, triangle budget
bpy-run blender/render.py out.png "front34;rear34" 960 32
bpy-run blender/export_roblox.py         # -> exports/TX6_Bastion_Roblox.fbx + TX6_Bastion_Rig.json
```
Want to change something? Edit the matching script in `tx6/` (e.g. `bumpers.py` for the bumper) and rebuild.
