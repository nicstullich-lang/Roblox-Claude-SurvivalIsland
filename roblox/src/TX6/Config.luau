--!nonstrict
--[[
	TX-6 "Bastion" - settings you can tune.

	This ModuleScript lives in ReplicatedStorage.TX6 so the server AND every client read the same numbers.
	Units: studs (1 stud = 0.28 m), seconds, degrees unless noted.
	Change a number, press Play, and the vehicle uses it - no other script needs editing.
]]

local Config = {}

-- ===================================================================== who can spawn it
Config.SpawnKey = Enum.KeyCode.F4            -- admins: F4 = spawn in front of you, Shift+F4 = remove it
Config.ChatCommand = "/tx6"                  -- admins: "/tx6" spawns, "/tx6 remove" removes
Config.OneVehiclePerAdmin = true
Config.RestrictSeatsToAdmins = false         -- true = only admins may drive / use the turret

-- ===================================================================== driving (4x4)
Config.MaxSpeed = 95                         -- studs/s forward  (95 studs/s = 96 km/h)
Config.ReverseSpeed = 30                     -- studs/s
Config.Acceleration = 34                     -- studs/s^2 when you press W
Config.BrakeDecel = 70                       -- studs/s^2 when braking / handbrake
Config.CoastDecel = 6                        -- engine braking when no key is pressed
Config.SteerMaxDeg = 32                      -- front wheel angle when slow
Config.SteerMaxDegAtSpeed = 9                -- front wheel angle at top speed (stops roll-overs)
Config.SteerSpeed = 3.5                      -- how fast the wheels turn (rad/s)
Config.HandbrakeKey = Enum.KeyCode.X
Config.FlipKey = Enum.KeyCode.R              -- driver: puts the vehicle back on its wheels when tipped over

-- suspension (the code computes spring stiffness from the real mass, these shape the feel)
Config.SuspensionSag = 0.55                  -- studs the springs compress under the vehicle's weight
Config.SuspensionDamping = 0.55              -- 0.3 = bouncy, 1.0 = very stiff damping
Config.SuspensionUp = 0.9                    -- studs of bump travel
Config.SuspensionDown = 1.1                  -- studs of droop travel
Config.ChassisDensity = 4.0                  -- heavier = more planted, slower to accelerate
Config.TireFriction = 1.6

-- ===================================================================== driver keys
Config.LightsKey = Enum.KeyCode.L
Config.BeaconsKey = Enum.KeyCode.B
Config.ArmorKey = Enum.KeyCode.G             -- windshield shield + window shutters
Config.MastKey = Enum.KeyCode.M              -- sensor / radar mast (driver or gunner)
Config.HornKey = Enum.KeyCode.H
Config.HornSoundId = ""                      -- paste a sound asset id like "rbxassetid://123" to enable the horn
Config.EngineSoundId = ""                    -- optional looping engine sound

-- ===================================================================== turret + rotary cannon (gunner)
Config.TurretPitchMin = -8
Config.TurretPitchMax = 40
Config.GunFireRate = 16                      -- rounds per second
Config.GunDamage = 9                         -- per hit
Config.GunHeadshotMultiplier = 1.5
Config.GunRange = 900
Config.GunSpreadDeg = 1.1
Config.GunHeatPerShot = 0.011                -- 1.0 = overheated
Config.GunCoolPerSecond = 0.28
Config.GunOverheatResume = 0.35              -- heat must fall below this after an overheat
Config.GunSpinUpTime = 0.35                  -- barrels must spin this long before firing

-- ===================================================================== lock-on missiles (gunner)
Config.MissileKeyDeploy = Enum.KeyCode.R     -- open the roof bays / stow them again
Config.MissileKeyFire = Enum.KeyCode.F       -- fire at the locked target (right mouse button also fires)
Config.MissilesPerPod = 6
Config.MissileReloadTime = 8                 -- seconds to reload one missile (into whichever pod is not full)
Config.MissileCooldown = 0.6                 -- seconds between launches
Config.MissileLockTime = 1.0                 -- seconds the target must stay in the lock cone
Config.MissileLockConeDeg = 6
Config.MissileKeepLockConeDeg = 14
Config.MissileRange = 550                    -- doubled while the sensor mast is raised
Config.MissileSpeedStart = 70
Config.MissileSpeedMax = 230
Config.MissileAccel = 260
Config.MissileTurnRateDeg = 140              -- degrees per second it can turn
Config.MissileLifetime = 7
Config.MissileDamage = 120                   -- at the centre of the blast
Config.MissileBlastRadius = 16

-- ===================================================================== damage
Config.DamagePlayers = true                  -- false = weapons only hurt NPCs / zombies
-- Every hit goes through this function, so it can be wired into CombatService later.
-- It tags the Humanoid with a "creator" ObjectValue (classic Roblox kill credit) then applies damage.
function Config.DealDamage(attacker: Player?, humanoid: Humanoid, amount: number, weapon: string)
	if humanoid.Health <= 0 then
		return
	end
	if attacker then
		local old = humanoid:FindFirstChild("creator")
		if old then
			old:Destroy()
		end
		local tag = Instance.new("ObjectValue")
		tag.Name = "creator"
		tag.Value = attacker
		tag.Parent = humanoid
		game:GetService("Debris"):AddItem(tag, 3)
	end
	humanoid:SetAttribute("LastHitWeapon", weapon)
	humanoid:TakeDamage(amount)
end

-- ===================================================================== admin check (mirrors AdminService.Allowed)
function Config.IsAdmin(player: Player): boolean
	if game:GetService("RunService"):IsStudio() then
		return true
	end
	if player:GetAttribute("IsAdmin") == true then
		return true
	end
	if game.CreatorType == Enum.CreatorType.User then
		return player.UserId == game.CreatorId
	end
	local ok, rank = pcall(function()
		return player:GetRankInGroupAsync(game.CreatorId)
	end)
	return ok and rank >= 255
end

return Config
