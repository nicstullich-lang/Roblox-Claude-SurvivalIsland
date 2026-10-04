--!nonstrict
--[[
	TX-6 "Bastion" - client visuals (StarterPlayerScripts). Runs on every player's machine.

	For every vehicle tagged "TX6_Vehicle" it smoothly animates all moving parts from the server's attributes
	(Motor6D.Transform), switches the lights / beacons / brake lights, hides the vehicle's prompts while you sit
	inside it, and draws weapon effects (tracers, muzzle flash, impacts, missiles, explosions).
	Visual only - nothing here can change gameplay.
]]

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Debris = game:GetService("Debris")

local Shared = require(ReplicatedStorage:WaitForChild("TX6"):WaitForChild("Shared"))
local Config, Rig = Shared.Config, Shared.Rig
local player = Players.LocalPlayer
local camera = workspace.CurrentCamera

local fxFolder = Instance.new("Folder")
fxFolder.Name = "TX6_FX"
fxFolder.Parent = workspace

-- ====================================================================== notices (toast)
local toastGui = Instance.new("ScreenGui")
toastGui.Name = "TX6_Toast"
toastGui.ResetOnSpawn = false
toastGui.Parent = player:WaitForChild("PlayerGui")
local toast = Instance.new("TextLabel")
toast.BackgroundColor3 = Color3.fromRGB(18, 20, 16)
toast.BackgroundTransparency = 0.25
toast.Size = UDim2.fromOffset(460, 34)
toast.Position = UDim2.new(0.5, -230, 0, 90)
toast.Font = Enum.Font.GothamBold
toast.TextSize = 15
toast.TextColor3 = Color3.fromRGB(255, 210, 120)
toast.Visible = false
toast.Parent = toastGui
Instance.new("UICorner").Parent = toast
local toastId = 0
local function showToast(msg: string)
	toastId += 1
	local id = toastId
	toast.Text = msg
	toast.Visible = true
	task.delay(2.6, function()
		if toastId == id then
			toast.Visible = false
		end
	end)
end

-- ====================================================================== effects
local function fxPart(size: Vector3, cf: CFrame, color: Color3, material: Enum.Material?): Part
	local p = Instance.new("Part")
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	p.Size = size
	p.CFrame = cf
	p.Color = color
	p.Material = material or Enum.Material.Neon
	p.Parent = fxFolder
	return p
end

local function near(pos: Vector3, dist: number): boolean
	return (camera.CFrame.Position - pos).Magnitude < dist
end

local function tracer(from: Vector3, to: Vector3, hit: boolean)
	if not near(from, 1500) then
		return
	end
	local len = (to - from).Magnitude
	if len < 0.5 then
		return
	end
	local mid = from:Lerp(to, 0.5)
	local t = fxPart(Vector3.new(0.14, 0.14, len), CFrame.lookAt(mid, to), Color3.fromRGB(255, 196, 96))
	t.Transparency = 0.15
	Debris:AddItem(t, 0.05)
	local flash = fxPart(Vector3.new(1.1, 1.1, 1.1), CFrame.new(from), Color3.fromRGB(255, 220, 140))
	flash.Shape = Enum.PartType.Ball
	local pl = Instance.new("PointLight")
	pl.Range = 14
	pl.Brightness = 4
	pl.Color = Color3.fromRGB(255, 200, 120)
	pl.Parent = flash
	Debris:AddItem(flash, 0.045)
	if hit then
		local spark = fxPart(Vector3.new(0.2, 0.2, 0.2), CFrame.new(to), Color3.new(1, 1, 1))
		spark.Transparency = 1
		local pe = Instance.new("ParticleEmitter")
		pe.Rate = 0
		pe.Lifetime = NumberRange.new(0.15, 0.35)
		pe.Speed = NumberRange.new(12, 26)
		pe.SpreadAngle = Vector2.new(180, 180)
		pe.LightEmission = 1
		pe.Color = ColorSequence.new(Color3.fromRGB(255, 220, 120), Color3.fromRGB(255, 120, 40))
		pe.Size = NumberSequence.new(0.18, 0)
		pe.Parent = spark
		pe:Emit(8)
		Debris:AddItem(spark, 0.6)
	end
end

local missiles = {}
local function missileModel(cf: CFrame)
	local body = fxPart(Vector3.new(0.38, 0.38, 2.3), cf, Color3.fromRGB(205, 208, 200), Enum.Material.SmoothPlastic)
	local nose = fxPart(Vector3.new(0.26, 0.26, 0.45), cf * CFrame.new(0, 0, -1.3), Color3.fromRGB(40, 40, 40),
		Enum.Material.SmoothPlastic)
	local a0 = Instance.new("Attachment")
	a0.Position = Vector3.new(0.15, 0, 1.15)
	a0.Parent = body
	local a1 = Instance.new("Attachment")
	a1.Position = Vector3.new(-0.15, 0, 1.15)
	a1.Parent = body
	local trail = Instance.new("Trail")
	trail.Attachment0 = a0
	trail.Attachment1 = a1
	trail.Lifetime = 1.4
	trail.MinLength = 0.1
	trail.WidthScale = NumberSequence.new(1, 6)
	trail.Color = ColorSequence.new(Color3.fromRGB(235, 225, 210), Color3.fromRGB(120, 120, 120))
	trail.Transparency = NumberSequence.new(0.2, 1)
	trail.LightEmission = 0.2
	trail.Parent = body
	local glow = Instance.new("PointLight")
	glow.Range = 12
	glow.Brightness = 3
	glow.Color = Color3.fromRGB(255, 150, 60)
	glow.Parent = body
	return body, nose
end

local function launchFx(id: number, start: CFrame, target: Instance?)
	local body, nose = missileModel(start)
	missiles[id] = {
		body = body, nose = nose, target = target,
		m = { Pos = start.Position, Vel = start.LookVector * Config.MissileSpeedStart, Speed = Config.MissileSpeedStart, Age = 0 },
	}
	local puff = fxPart(Vector3.new(2, 2, 2), start, Color3.fromRGB(200, 200, 200), Enum.Material.SmoothPlastic)
	puff.Transparency = 1
	local pe = Instance.new("ParticleEmitter")
	pe.Rate = 0
	pe.Lifetime = NumberRange.new(0.6, 1.2)
	pe.Speed = NumberRange.new(4, 10)
	pe.SpreadAngle = Vector2.new(40, 40)
	pe.Size = NumberSequence.new(1.2, 4)
	pe.Transparency = NumberSequence.new(0.3, 1)
	pe.Parent = puff
	pe:Emit(14)
	Debris:AddItem(puff, 1.5)
end

local function removeMissile(id: number)
	local ms = missiles[id]
	if ms then
		missiles[id] = nil
		ms.nose:Destroy()
		ms.body.Transparency = 1
		Debris:AddItem(ms.body, 1.4) -- let the smoke trail fade
	end
end

local function hitFx(id: number, pos: Vector3)
	removeMissile(id)
	local ex = Instance.new("Explosion")
	ex.Position = pos
	ex.BlastRadius = Config.MissileBlastRadius
	ex.BlastPressure = 0 -- visual only, the server applies the damage
	ex.DestroyJointRadiusPercent = 0
	ex.ExplosionType = Enum.ExplosionType.NoCraters
	ex.Parent = fxFolder
	local light = fxPart(Vector3.new(1, 1, 1), CFrame.new(pos), Color3.fromRGB(255, 180, 90))
	light.Transparency = 1
	local pl = Instance.new("PointLight")
	pl.Range = 40
	pl.Brightness = 8
	pl.Color = Color3.fromRGB(255, 170, 80)
	pl.Parent = light
	Debris:AddItem(light, 0.25)
end

-- ====================================================================== vehicles
local tracked = {}

local function setLight(st, name: string, on: boolean, brightness: number?)
	local l = st.lights[name]
	if l then
		l.Enabled = on
		if brightness then
			l.Brightness = brightness
		end
	end
end

local function paintParts(list, on: boolean, matName: string)
	local onSpec, offSpec = Rig.Materials[matName], Rig.LightOff[matName]
	local spec = on and onSpec or offSpec
	if not spec then
		return
	end
	for _, p in list do
		p.Material = Enum.Material[spec.Material]
		p.Color = spec.Color
	end
end

local function track(v: Model)
	if tracked[v] then
		return
	end
	local jointsFolder = v:WaitForChild("Joints", 10)
	local remote = v:WaitForChild("TX6Remote", 10)
	if not jointsFolder or not remote then
		return
	end
	local st = {
		joints = {}, progress = {}, lights = {}, prompts = {},
		parts = { LED = {}, Amber = {}, RedLens = {} },
		yaw = 0, pitch = 0, spin = 0, spinSpeed = 0, headSpin = 0,
		lightsKey = nil, conns = {},
	}
	for _, jp in jointsFolder:GetChildren() do
		local m = jp:FindFirstChild("Motor")
		if m and m:IsA("Motor6D") then
			st.joints[string.sub(jp.Name, 3)] = m
		end
	end
	for _, ch in Shared.Channels do
		st.progress[ch] = v:GetAttribute("T_" .. ch) or 0
	end
	for _, d in v:GetDescendants() do
		if d:IsA("BasePart") then
			local mat = d:GetAttribute("TX6Mat")
			if mat and st.parts[mat] then
				table.insert(st.parts[mat], d)
			end
		elseif d:IsA("Light") and d.Parent then
			st.lights[d.Parent.Name] = d
		elseif d:IsA("ProximityPrompt") then
			table.insert(st.prompts, d)
		end
	end
	table.insert(st.conns, remote.OnClientEvent:Connect(function(kind, a, b, c)
		if kind == "Tracer" then
			tracer(a, b, c)
		elseif kind == "MissileLaunch" then
			launchFx(a, b, c)
		elseif kind == "MissileHit" then
			hitFx(a, b)
		elseif kind == "Notice" then
			showToast(tostring(a))
		end
	end))
	tracked[v] = st
end

local function untrack(v: Model)
	local st = tracked[v]
	if st then
		for _, c in st.conns do
			c:Disconnect()
		end
		tracked[v] = nil
	end
end

for _, v in CollectionService:GetTagged("TX6_Vehicle") do
	if v:IsDescendantOf(workspace) then
		task.spawn(track, v)
	end
end
CollectionService:GetInstanceAddedSignal("TX6_Vehicle"):Connect(function(v)
	if v:IsDescendantOf(workspace) then
		task.spawn(track, v)
	end
end)
CollectionService:GetInstanceRemovedSignal("TX6_Vehicle"):Connect(untrack)

local function lerpAngle(a: number, b: number, t: number): number
	local d = (b - a + math.pi) % (2 * math.pi) - math.pi
	return a + d * t
end

RunService.Stepped:Connect(function(_, dt)
	local myHum = player.Character and player.Character:FindFirstChildOfClass("Humanoid")
	local mySeat = myHum and myHum.SeatPart
	for v, st in tracked do
		if not v.Parent then
			untrack(v)
			continue
		end
		local chassis = v.PrimaryPart
		if not chassis then
			continue
		end
		for _, ch in Shared.Channels do
			st.progress[ch] = Shared.Advance(ch, st.progress[ch], v:GetAttribute("T_" .. ch) or 0, dt)
		end
		-- turret: my own aim if I am the gunner, otherwise the server's (smoothed)
		local cy, cp = v:GetAttribute("ClientYaw"), v:GetAttribute("ClientPitch")
		if cy ~= nil and cp ~= nil then
			st.yaw, st.pitch = cy, cp
		else
			local k = 1 - math.exp(-10 * dt)
			st.yaw = lerpAngle(st.yaw, v:GetAttribute("TurretYaw") or 0, k)
			st.pitch = lerpAngle(st.pitch, v:GetAttribute("TurretPitch") or 0, k)
		end
		local firing = v:GetAttribute("Firing") == true
		local targetSpin = firing and 42 or 0
		st.spinSpeed += math.clamp(targetSpin - st.spinSpeed, -25 * dt, 90 * dt)
		st.spin = (st.spin + st.spinSpeed * dt) % (2 * math.pi)
		if (st.progress.Mast or 0) >= 0.99 then
			st.headSpin = (st.headSpin + 1.6 * dt) % (2 * math.pi)
		else
			st.headSpin = lerpAngle(st.headSpin, 0, math.min(1, 3 * dt))
		end
		if near(chassis.Position, 900) then
			local live = { Yaw = st.yaw, Pitch = st.pitch, Spin = st.spin, HeadSpin = st.headSpin }
			for name, motor in st.joints do
				motor.Transform = Shared.JointTransform(name, st.progress, live)
			end
		end

		-- lights: only touch parts when something changed
		local lightsOn = v:GetAttribute("LightsOn") == true
		local braking = v:GetAttribute("Braking") == true
		local beacons = v:GetAttribute("BeaconsOn") == true
		local phase = beacons and (math.floor(os.clock() * 4) % 2 == 0) or false
		local key = (lightsOn and "1" or "0") .. (braking and "1" or "0") .. (phase and "1" or "0")
		if key ~= st.lightsKey then
			st.lightsKey = key
			paintParts(st.parts.LED, lightsOn, "LED")
			paintParts(st.parts.RedLens, lightsOn or braking, "RedLens")
			paintParts(st.parts.Amber, phase, "Amber")
			for _, n in { "HeadlightL", "HeadlightR", "LightBar", "Searchlight", "Dome" } do
				setLight(st, n, lightsOn)
			end
			for i = 1, 4 do
				setLight(st, "Beacon" .. i, phase)
			end
			setLight(st, "TailL", lightsOn or braking, braking and 4 or 1.5)
			setLight(st, "TailR", lightsOn or braking, braking and 4 or 1.5)
		end

		-- hide this vehicle's prompts while I sit in it
		local inside = mySeat ~= nil and mySeat:IsDescendantOf(v)
		if st.inside ~= inside then
			st.inside = inside
			for _, pp in st.prompts do
				pp.Enabled = not inside
			end
		end
	end

	-- missiles in flight (same maths as the server)
	for id, ms in missiles do
		local tpos = Shared.TargetPosition(ms.target)
		local pos = Shared.MissileStep(ms.m, tpos, dt)
		ms.m.Pos = pos
		local cf = CFrame.lookAt(pos, pos + ms.m.Vel)
		ms.body.CFrame = cf
		ms.nose.CFrame = cf * CFrame.new(0, 0, -1.3)
		if ms.m.Age > Config.MissileLifetime + 1 then
			removeMissile(id)
		end
	end
end)
