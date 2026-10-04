# TX-6 "Bastion" — make it drive in Roblox Studio

You need two files from this repository:

| File | What it is |
|---|---|
| `exports/TX6_Bastion_Roblox.fbx` | the 3D model (all 172 meshes, already in studs) |
| `roblox/TX6_Kit.rbxmx` | the code kit (installer + driving, turret, missiles, doors, lights, spawner) |

## 1. Download

On the GitHub page of the repo, press the green **Code** button → **Download ZIP**, then unzip it
(right-click → Extract All). Make sure the branch picker (top-left of the file list) shows the branch with the
`roblox` and `exports` folders.

## 2. Import the 3D model (once)

1. Open **Survival Island** in Roblox Studio.
2. **Home** tab → **Import 3D** → pick `exports/TX6_Bastion_Roblox.fbx`.
3. Check the settings (same as the VX-9): *Scale Unit* **Stud**, *Scale Factor* **1**, *World Forward* **Front**,
   *World Up* **Top**, *Set Pivot to Scene Origin* ✔, *Upload to Roblox* ✔.
   *File Dimensions* should read about **11.21 × 13.69 × 25.09**.
4. Press **Import**. A model called `TX6_Bastion_Roblox` appears in Workspace. Don't move it.

## 3. Insert the code kit

In the **Explorer** window: right-click **ServerStorage** → **Insert from File…** → pick `roblox/TX6_Kit.rbxmx`.
A folder `TX6_Kit` appears inside ServerStorage.

## 4. Run the installer (one line)

**View** tab → **Command Bar**. Paste this and press Enter:

```lua
require(game.ServerStorage.TX6_Kit.Install)()
```

The **Output** window should say:
`[TX6] Installed: 172 meshes, 31 joints, 0 unknown names. Vehicle stored in ServerStorage.AdminVehicles.TX6_Bastion …`

It also installs these (you don't need to touch them):
- `ReplicatedStorage.TX6` → `Config` (all the numbers you can tune), `RigData`, `Shared`
- `ServerScriptService.TX6_Spawner`
- `StarterPlayer.StarterPlayerScripts.TX6_Visuals` and `TX6_SpawnClient`
- `ServerStorage.TX6_ImportBackup` (so you can re-run the installer later without importing again)

Then **File → Save** (and **Publish** when you are happy).

## 5. Test it

Press **Play** (F5), then:

| Who | Key | What it does |
|---|---|---|
| Admin | **F4** (or chat `/tx6`) | spawns the TX-6 in front of you · **Shift+F4** / `/tx6 remove` removes it |
| Anyone | **E** at the front-left door | get in as **driver** |
| Anyone | **E** at the other doors | ride as passenger |
| Anyone | **T** at a rear door | climb into the **turret** (gunner) |
| Anyone | **F** at doors, rear, side bays, hood, fuel door | open / close it |
| Driver | **W A S D** | drive (4×4, speed-sensitive steering), **X** handbrake |
| Driver | **L** / **B** / **G** / **M** / **H** / **R** | lights / beacons / armour mode / sensor mast / horn / flip upright |
| Gunner | mouse | aim the turret (it follows your crosshair) |
| Gunner | **left click** (hold) | rotary cannon — watch the heat bar |
| Gunner | **R** | open / close the missile bays |
| Gunner | keep the crosshair on a zombie/target for 1 s | **lock on** (red box) |
| Gunner | **F** or **right click** | fire a homing missile (12 missiles, they reload) |
| Gunner | **M** | sensor mast → radar on screen + double missile range |
| Everyone | **Space** | get out |

Gamepads and phones work too (on-screen buttons for brake, fire, missile and bays).

## 6. Tuning

Open `ReplicatedStorage.TX6.Config`. Every number has a comment, for example:
`MaxSpeed`, `Acceleration`, `SteerMaxDeg`, `SuspensionSag` (lower = stiffer), `SuspensionDamping` (higher = less
bounce), `GunDamage`, `MissileDamage`, `DamagePlayers`, `RestrictSeatsToAdmins`, `HornSoundId`.
Weapon hits go through `Config.DealDamage` — that is the one place to connect it to CombatService later.

## 7. If something goes wrong

| Problem | Fix |
|---|---|
| Output: `Import … first` | the imported model isn't in Workspace — do step 2 again (or keep `ServerStorage.TX6_ImportBackup`) |
| Output: `unexpected import size` | re-import with Scale Unit **Stud**, Scale **1**, Forward **Front**, Up **Top** |
| F4 does nothing | you are not an admin in a live server (Studio always counts as admin), or `TX6_Spawner` is missing → run step 4 again |
| Bounces / sits too low | raise `SuspensionDamping` (e.g. 0.8) / lower `SuspensionSag` (e.g. 0.4) |
| Feels slow / too fast | `Acceleration`, `MaxSpeed`, `ChassisDensity` |
| Want to update the code later | insert the new `TX6_Kit.rbxmx`, delete the old `TX6_Kit`, run step 4 again |

All code is server-checked: clients only ask, the server decides (who sits where, aim limits, fire rate, heat,
missile lock range, damage).
