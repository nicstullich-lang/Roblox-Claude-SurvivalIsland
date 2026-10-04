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
