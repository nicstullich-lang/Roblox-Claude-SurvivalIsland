--!nonstrict
--[[
	TX-6 "Bastion" - server brain (runs inside every spawned vehicle).

	Server-authoritative: clients only ASK (remote events); this script checks who is asking (which seat they are in),
	clamps every number, runs the weapons, applies damage and tells all clients what to show.
	Animated parts are driven by attributes ("T_<channel>" = 0/1 targets, TurretYaw/Pitch, Firing ...);
	every client animates them smoothly with TX6_Visuals.
]]

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local PhysicsService = game:GetService("PhysicsService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local vehicle = script.Parent
local Shared = require(ReplicatedStorage:WaitForChild("TX6"):WaitForChild("Shared"))
local Config, Rig = Shared.Config, Shared.Rig

local chassis: BasePart = vehicle:WaitForChild("Chassis")
local seatsFolder = vehicle:WaitForChild("Seats")
local wheels = vehicle:WaitForChild("Wheels")
local templates = vehicle:WaitForChild("Templates")
local remote: RemoteEvent = vehicle:WaitForChild("TX6Remote")

-- ====================================================================== collision groups
for _, g in { "TX6_Body", "TX6_Wheels" } do
	pcall(function()
		if not PhysicsService:IsCollisionGroupRegistered(g) then
			PhysicsService:RegisterCollisionGroup(g)
		end
	end)
end
pcall(function()
	PhysicsService:CollisionGroupSetCollidable("TX6_Body", "TX6_Wheels", false)
	PhysicsService:CollisionGroupSetCollidable("TX6_Wheels", "TX6_Wheels", false)
end)

-- ====================================================================== state
local targets, progress = {}, {}
for _, ch in Shared.Channels do
	targets[ch] = 0
	progress[ch] = 0
	vehicle:SetAttribute("T_" .. ch, 0)
end
local pods = { L = Config.MissilesPerPod, R = Config.MissilesPerPod }
vehicle:SetAttribute("MissilesL", pods.L)
vehicle:SetAttribute("MissilesR", pods.R)
vehicle:SetAttribute("TurretYaw", 0)
vehicle:SetAttribute("TurretPitch", 0)
vehicle:SetAttribute("Firing", false)
vehicle:SetAttribute("Heat", 0)
vehicle:SetAttribute("Overheated", false)
vehicle:SetAttribute("LightsOn", false)
vehicle:SetAttribute("BeaconsOn", false)
vehicle:SetAttribute("Braking", false)

local function setChannel(ch: string, value: number)
	targets[ch] = value
	vehicle:SetAttribute("T_" .. ch, value)
end

local function notice(player: Player?, text: string)
	if player then
		remote:FireClient(player, "Notice", text)
	end
end

-- ====================================================================== drivetrain helpers
local struts = {}
for _, tag in { "FL", "FR", "RL", "RR" } do
	struts[tag] = wheels:WaitForChild("Strut_" .. tag)
end

local function sprungMass(): number
	local ok, m = pcall(function()
		return chassis.AssemblyMass
	end)
	return (ok and m and m > 0) and m or chassis:GetMass()
end

local function brakeAll()
	local mass = sprungMass()
	for tag, strut in struts do
		local motor = strut:FindFirstChild("Motor")
		if motor then
			motor.AngularVelocity = 0
			motor.MotorMaxTorque = mass * Config.BrakeDecel * Rig.WheelRadius / 4 * 1.5
			motor.MotorMaxAcceleration = 400
		end
		local susp = strut:FindFirstChild("Susp")
		if susp and susp:IsA("CylindricalConstraint") then
			susp.TargetAngle = 0
		end
	end
end

local function tuneSuspension()
	local mass = sprungMass()
	local perWheel = mass / 4
	local k = perWheel * workspace.Gravity / Config.SuspensionSag
	local c = 2 * Config.SuspensionDamping * math.sqrt(k * perWheel)
	for _, strut in struts do
		local spring = strut:FindFirstChild("Spring")
		if spring then
			spring.Stiffness = k
			spring.Damping = c
			spring.FreeLength = Rig.SpringTop + Config.SuspensionSag
		end
	end
	vehicle:SetAttribute("SprungMass", math.floor(mass))
end

task.defer(function()
	RunService.Heartbeat:Wait()
	tuneSuspension()
	brakeAll()
	pcall(function()
		chassis:SetNetworkOwner(nil) -- parked: the server simulates it (no jitter)
	end)
end)

-- ====================================================================== seats
local SEATS = {
	DriverSeat = { Door = "Door_FL", Exit = "Exit_Driver", Client = "TX6_DriverClient", Crew = true },
	PassengerSeat = { Door = "Door_FR", Exit = "Exit_Passenger" },
	RearLeftSeat = { Door = "Door_RL", Exit = "Exit_RearL" },
	RearRightSeat = { Door = "Door_RR", Exit = "Exit_RearR" },
	GunnerSeat = { Door = "Door_RL", Exit = "Exit_Gunner", Client = "TX6_GunnerClient", Crew = true },
}
local occupant: { [string]: Player? } = {}
local givenGui: { [string]: Instance? } = {}
local gun = { firing = false, heat = 0, overheated = false, spin = 0, acc = 0 }

local function occupantCharacters()
	local list = {}
	for _, seat in seatsFolder:GetChildren() do
		if seat:IsA("Seat") or seat:IsA("VehicleSeat") then
			local hum = seat.Occupant
			if hum and hum.Parent then
				table.insert(list, hum.Parent)
			end
		end
	end
	return list
end

local function giveClient(seatName: string, player: Player)
	local info = SEATS[seatName]
	if not info.Client then
		return
	end
	local gui = Instance.new("ScreenGui")
	gui.Name = "TX6_" .. seatName
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	local ref = Instance.new("ObjectValue")
	ref.Name = "Vehicle"
	ref.Value = vehicle
	ref.Parent = gui
	templates:WaitForChild(info.Client):Clone().Parent = gui
	gui.Parent = player:WaitForChild("PlayerGui")
	givenGui[seatName] = gui
end

local function exitTo(char: Model?, exitName: string)
	task.delay(0.1, function()
		local root = char and char:FindFirstChild("HumanoidRootPart")
		if not root or not vehicle.Parent then
			return
		end
		local vcf = Shared.VehicleCF(chassis)
		local p = vcf:PointToWorldSpace(Rig.Points[exitName])
		local _, yaw = vcf:ToEulerAnglesYXZ()
		root.CFrame = CFrame.new(p) * CFrame.Angles(0, yaw, 0)
		root.AssemblyLinearVelocity = chassis.AssemblyLinearVelocity
	end)
end

for seatName, info in SEATS do
	local seat = seatsFolder:WaitForChild(seatName)
	seat:GetPropertyChangedSignal("Occupant"):Connect(function()
		local hum = seat.Occupant
		local prev = occupant[seatName]
		if hum then
			local player = Players:GetPlayerFromCharacter(hum.Parent)
			occupant[seatName] = player
			if player then
				if seatName == "DriverSeat" then
					pcall(function()
						chassis:SetNetworkOwner(player) -- the driver simulates the physics = no input lag
					end)
				end
				giveClient(seatName, player)
			end
		else
			occupant[seatName] = nil
			local gui = givenGui[seatName]
			if gui then
				gui:Destroy()
				givenGui[seatName] = nil
			end
			if seatName == "DriverSeat" then
				vehicle:SetAttribute("Braking", false)
				brakeAll()
				pcall(function()
					chassis:SetNetworkOwner(nil)
				end)
			elseif seatName == "GunnerSeat" then
				gun.firing = false
			end
			if prev then
				exitTo(prev.Character, info.Exit)
			end
		end
	end)
end

-- ====================================================================== prompts (doors, bays, getting in)
local function pulseDoor(ch: string)
	if targets[ch] == 1 then
		return
	end
	setChannel(ch, 1)
	task.delay(1.5, function()
		if vehicle.Parent then
			setChannel(ch, 0)
		end
	end)
end

local function toggleChannel(ch: string, player: Player?)
	local value = targets[ch] == 1 and 0 or 1
	if ch == "Hood" and value == 1 and targets.Armor == 1 then
		notice(player, "Lower the windshield armour first (driver presses " .. Config.ArmorKey.Name .. ")")
		return
	end
	setChannel(ch, value)
end

local function onPrompt(pp: ProximityPrompt, player: Player)
	local char = player.Character
	local hum = char and char:FindFirstChildOfClass("Humanoid")
	if not hum or hum.Health <= 0 or hum.SeatPart then
		return
	end
	local root = char:FindFirstChild("HumanoidRootPart")
	local holder = pp.Parent
	if root and holder and holder:IsA("Attachment") and (root.Position - holder.WorldPosition).Magnitude > pp.MaxActivationDistance + 4 then
		return
	end
	local kind, target = pp:GetAttribute("Kind"), pp:GetAttribute("Target")
	if kind == "Seat" then
		local seat = seatsFolder:FindFirstChild(target)
		local info = SEATS[target]
		if not seat or not info then
			return
		end
		if seat.Occupant then
			notice(player, "That seat is taken")
			return
		end
		if info.Crew and Config.RestrictSeatsToAdmins and not Config.IsAdmin(player) then
			notice(player, "Only admins can crew the TX-6")
			return
		end
		local door = info.Door
		if target == "GunnerSeat" and holder and holder.Name == "P_RearRightDoor" then
			door = "Door_RR"
		end
		pulseDoor(door)
		task.delay(0.35, function()
			if seat.Parent and not seat.Occupant and hum.Parent and hum.Health > 0 and not hum.SeatPart then
				seat:Sit(hum)
			end
		end)
	elseif kind == "Channel" and targets[target] ~= nil then
		toggleChannel(target, player)
	end
end

for _, d in chassis:GetDescendants() do
	if d:IsA("ProximityPrompt") then
		d.Triggered:Connect(function(player)
			onPrompt(d, player)
		end)
	end
end

-- ====================================================================== weapons
local rng = Random.new()
local aimYaw, aimPitch = 0, 0

local function excludeParams()
	local p = RaycastParams.new()
	p.FilterType = Enum.RaycastFilterType.Exclude
	local list = { vehicle }
	for _, c in occupantCharacters() do
		table.insert(list, c)
	end
	p.FilterDescendantsInstances = list
	p.IgnoreWater = true
	return p
end

local function canDamage(hum: Humanoid?): boolean
	if not hum or hum.Health <= 0 then
		return false
	end
	local char = hum.Parent
	for _, c in occupantCharacters() do
		if c == char then
			return false
		end
	end
	if not Config.DamagePlayers and Players:GetPlayerFromCharacter(char) then
		return false
	end
	return true
end

local function fireRound()
	local muzzle = Shared.Muzzle(Shared.VehicleCF(chassis), aimYaw, aimPitch)
	local spread = math.rad(Config.GunSpreadDeg)
	local dir = (muzzle * CFrame.Angles(rng:NextNumber(-spread, spread), rng:NextNumber(-spread, spread), 0)).LookVector
	local result = workspace:Raycast(muzzle.Position, dir * Config.GunRange, excludeParams())
	local hitPos = result and result.Position or (muzzle.Position + dir * Config.GunRange)
	if result then
		local hum = Shared.HumanoidFromPart(result.Instance)
		if canDamage(hum) then
			local mult = (result.Instance.Name == "Head") and Config.GunHeadshotMultiplier or 1
			Config.DealDamage(occupant.GunnerSeat, hum, Config.GunDamage * mult, "TX-6 rotary cannon")
		end
	end
	remote:FireAllClients("Tracer", muzzle.Position, hitPos, result ~= nil)
end

-- missiles: simulated here (authoritative); every client flies an identical visual copy
local live = {}
local nextId = 0
local nextSide = "L"
local lastLaunch = 0
local reloadClock = 0

local function explode(m, pos: Vector3)
	live[m.Id] = nil
	remote:FireAllClients("MissileHit", m.Id, pos)
	local params = OverlapParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { vehicle }
	local done = {}
	for _, p in workspace:GetPartBoundsInRadius(pos, Config.MissileBlastRadius, params) do
		local hum = Shared.HumanoidFromPart(p)
		if hum and not done[hum] then
			done[hum] = true
			if canDamage(hum) then
				local tp = Shared.TargetPosition(hum.Parent) or p.Position
				local k = math.clamp(1 - (tp - pos).Magnitude / Config.MissileBlastRadius, 0.25, 1)
				Config.DealDamage(m.Attacker, hum, Config.MissileDamage * k, "TX-6 lock-on missile")
			end
		end
	end
end

local function launch(player: Player, target: Instance?)
	if typeof(target) ~= "Instance" or not target:IsA("Model") then
		return
	end
	if targets.Missiles ~= 1 or progress.Missiles < 0.999 then
		notice(player, "Open the missile bays first (" .. Config.MissileKeyDeploy.Name .. ")")
		return
	end
	if os.clock() - lastLaunch < Config.MissileCooldown then
		return
	end
	local side = pods[nextSide] > 0 and nextSide or (nextSide == "L" and "R" or "L")
	if pods[side] <= 0 then
		notice(player, "Missile pods empty - reloading")
		return
	end
	local tpos = Shared.TargetPosition(target)
	if not tpos or not canDamage(target:FindFirstChildOfClass("Humanoid")) then
		return
	end
	local range = Config.MissileRange * ((progress.Mast >= 0.99) and 2 or 1)
	if (tpos - chassis.Position).Magnitude > range * 1.15 then
		notice(player, "Target out of range")
		return
	end
	pods[side] -= 1
	nextSide = side == "L" and "R" or "L"
	lastLaunch = os.clock()
	vehicle:SetAttribute("MissilesL", pods.L)
	vehicle:SetAttribute("MissilesR", pods.R)
	local start = Shared.PodLaunch(Shared.VehicleCF(chassis), side)
	nextId += 1
	live[nextId] = {
		Id = nextId, Pos = start.Position, Vel = start.LookVector * Config.MissileSpeedStart,
		Speed = Config.MissileSpeedStart, Age = 0, Target = target, Attacker = player,
	}
	remote:FireAllClients("MissileLaunch", nextId, start, target)
end

local missileParams = RaycastParams.new()
missileParams.FilterType = Enum.RaycastFilterType.Exclude
missileParams.FilterDescendantsInstances = { vehicle }

-- ====================================================================== driver / gunner requests
local buckets = {}
local function allow(player: Player, action: string): boolean
	local key = player.UserId .. action
	local now = os.clock()
	local b = buckets[key]
	local rate = action == "Aim" and 40 or 8
	if not b then
		b = { t = now, n = rate }
		buckets[key] = b
	end
	b.n = math.min(rate, b.n + (now - b.t) * rate)
	b.t = now
	if b.n < 1 then
		return false
	end
	b.n -= 1
	return true
end
Players.PlayerRemoving:Connect(function(player)
	for k in buckets do
		if string.sub(k, 1, #tostring(player.UserId)) == tostring(player.UserId) then
			buckets[k] = nil
		end
	end
end)

local horn: Sound? = nil
if Config.HornSoundId ~= "" then
	local h = Instance.new("Sound")
	h.Name = "Horn"
	h.SoundId = Config.HornSoundId
	h.RollOffMaxDistance = 400
	h.Parent = chassis
	horn = h
end

local function flip()
	local cf = chassis.CFrame
	if cf.UpVector.Y > 0.6 or chassis.AssemblyLinearVelocity.Magnitude > 15 then
		return
	end
	local look = cf.LookVector
	local flat = Vector3.new(look.X, 0, look.Z)
	if flat.Magnitude < 0.1 then
		flat = Vector3.new(0, 0, -1)
	end
	local pos = Shared.VehicleCF(chassis).Position + Vector3.new(0, 6, 0)
	vehicle:PivotTo(CFrame.lookAt(pos, pos + flat.Unit))
	for _, p in vehicle:GetDescendants() do
		if p:IsA("BasePart") then
			p.AssemblyLinearVelocity = Vector3.zero
			p.AssemblyAngularVelocity = Vector3.zero
		end
	end
end

local function toggleArmor(player: Player)
	if targets.Armor == 1 then
		setChannel("Armor", 0)
		return
	end
	if targets.Hood == 1 then
		setChannel("Hood", 0)
		task.spawn(function()
			local t0 = os.clock()
			while progress.Hood > 0.01 and os.clock() - t0 < 3 do
				RunService.Heartbeat:Wait()
			end
			setChannel("Armor", 1)
		end)
		return
	end
	setChannel("Armor", 1)
end

remote.OnServerEvent:Connect(function(player: Player, action, a, b)
	if typeof(action) ~= "string" or not allow(player, action) then
		return
	end
	local isDriver = occupant.DriverSeat == player
	local isGunner = occupant.GunnerSeat == player
	if action == "Aim" and isGunner then
		if typeof(a) == "number" and typeof(b) == "number" and a == a and b == b then
			aimYaw = (a + math.pi) % (2 * math.pi) - math.pi
			aimPitch = math.clamp(b, math.rad(Config.TurretPitchMin), math.rad(Config.TurretPitchMax))
		end
	elseif action == "Fire" and isGunner then
		gun.firing = a == true
	elseif action == "MissileDeploy" and isGunner then
		setChannel("Missiles", targets.Missiles == 1 and 0 or 1)
	elseif action == "Launch" and isGunner then
		launch(player, a)
	elseif action == "Mast" and (isDriver or isGunner) then
		setChannel("Mast", targets.Mast == 1 and 0 or 1)
	elseif action == "Lights" and isDriver then
		vehicle:SetAttribute("LightsOn", not vehicle:GetAttribute("LightsOn"))
	elseif action == "Beacons" and isDriver then
		vehicle:SetAttribute("BeaconsOn", not vehicle:GetAttribute("BeaconsOn"))
	elseif action == "Armor" and isDriver then
		toggleArmor(player)
	elseif action == "Brake" and isDriver then
		vehicle:SetAttribute("Braking", a == true)
	elseif action == "Horn" and isDriver then
		if horn then
			horn:Play()
		end
	elseif action == "Flip" and isDriver then
		flip()
	end
end)

-- ====================================================================== main loop
local attrClock = 0
RunService.Heartbeat:Connect(function(dt)
	for _, ch in Shared.Channels do
		progress[ch] = Shared.Advance(ch, progress[ch], targets[ch], dt)
	end

	-- rotary cannon: spin-up, rate of fire, heat
	local manned = occupant.GunnerSeat ~= nil
	local trying = gun.firing and manned and not gun.overheated
	if trying then
		gun.spin = math.min(Config.GunSpinUpTime, gun.spin + dt)
	else
		gun.spin = math.max(0, gun.spin - dt * 0.5)
	end
	if trying and gun.spin >= Config.GunSpinUpTime then
		gun.acc += dt * Config.GunFireRate
		while gun.acc >= 1 do
			gun.acc -= 1
			fireRound()
			gun.heat += Config.GunHeatPerShot
			if gun.heat >= 1 then
				gun.heat = 1
				gun.overheated = true
				gun.acc = 0
				break
			end
		end
	else
		gun.acc = 0
		gun.heat = math.max(0, gun.heat - Config.GunCoolPerSecond * dt)
	end
	if gun.overheated and gun.heat <= Config.GunOverheatResume then
		gun.overheated = false
	end

	-- missiles in flight
	for _, m in live do
		local tpos = Shared.TargetPosition(m.Target)
		local from = m.Pos
		local to = Shared.MissileStep(m, tpos, dt)
		local hit = workspace:Raycast(from, to - from, missileParams)
		if hit then
			explode(m, hit.Position)
		elseif tpos and (to - tpos).Magnitude < 4 then
			explode(m, to)
		elseif m.Age > Config.MissileLifetime then
			explode(m, to)
		else
			m.Pos = to
		end
	end

	-- missile reload (one at a time into the emptier pod)
	if pods.L < Config.MissilesPerPod or pods.R < Config.MissilesPerPod then
		reloadClock += dt
		if reloadClock >= Config.MissileReloadTime then
			reloadClock = 0
			local side = pods.L <= pods.R and "L" or "R"
			pods[side] += 1
			vehicle:SetAttribute("MissilesL", pods.L)
			vehicle:SetAttribute("MissilesR", pods.R)
		end
	else
		reloadClock = 0
	end

	-- replicate the gunner state ~10 times a second
	attrClock += dt
	if attrClock >= 0.1 then
		attrClock = 0
		vehicle:SetAttribute("TurretYaw", aimYaw)
		vehicle:SetAttribute("TurretPitch", aimPitch)
		vehicle:SetAttribute("Firing", trying)
		vehicle:SetAttribute("Heat", math.floor(gun.heat * 100 + 0.5) / 100)
		vehicle:SetAttribute("Overheated", gun.overheated)
	end
end)
