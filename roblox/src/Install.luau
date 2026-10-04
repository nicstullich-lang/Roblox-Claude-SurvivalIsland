--!nonstrict
--[[
	TX-6 "Bastion" - one-time installer (run in Studio EDIT mode from the Command Bar):

		require(game.ServerStorage.TX6_Kit.Install)()

	What it does
	  1. finds the model made by the 3D Importer (exports/TX6_Bastion_Roblox.fbx)
	  2. installs ReplicatedStorage.TX6 (Config / RigData / Shared), the spawner and the client scripts
	  3. turns the 172 imported MeshParts into a working vehicle:
	       physics chassis + collision boxes, 4 sprung wheels (front steering, 4x4 motors),
	       a Motor6D joint for every moving part, seats, ProximityPrompts, lights, materials
	  4. stores the finished vehicle in ServerStorage.AdminVehicles.TX6_Bastion
	Re-running it is safe: it replaces the previous install.
]]

local ServerStorage = game:GetService("ServerStorage")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")
local StarterPlayer = game:GetService("StarterPlayer")
local CollectionService = game:GetService("CollectionService")

local kit = script.Parent

local function part(name: string, size: Vector3, cf: CFrame, parent: Instance): Part
	local p = Instance.new("Part")
	p.Name = name
	p.Size = size
	p.CFrame = cf
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.Transparency = 1
	p.CastShadow = false
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.Parent = parent
	return p
end

local function weld(a: BasePart, b: BasePart, parent: Instance?)
	local w = Instance.new("WeldConstraint")
	w.Part0 = a
	w.Part1 = b
	w.Parent = parent or b
	return w
end

local function attach(name: string, parentPart: BasePart, worldCF: CFrame): Attachment
	local a = Instance.new("Attachment")
	a.Name = name
	a.CFrame = parentPart.CFrame:ToObjectSpace(worldCF)
	a.Parent = parentPart
	return a
end

local function findSource(): Model?
	local direct = workspace:FindFirstChild("TX6_Bastion_Roblox")
	if direct and direct:IsA("Model") then
		return direct
	end
	for _, d in workspace:GetDescendants() do
		if d:IsA("BasePart") and string.sub(d.Name, 1, 14) == "RBX_Body_Paint" then
			return d:FindFirstAncestorOfClass("Model")
		end
	end
	-- re-install without importing again: use the untouched copy saved by the last install
	local backup = ServerStorage:FindFirstChild("TX6_ImportBackup")
	if backup and backup:IsA("Model") then
		local copy = backup:Clone()
		copy.Parent = workspace
		return copy
	end
	return nil
end

-- put the imported model exactly where the Blender export expects it (independent of importer pivot options)
local function normalise(source: Model, Rig)
	local _, size = source:GetBoundingBox()
	local expected = Rig.ImportSize
	if size.Z < expected.Z * 0.5 then
		-- imported in metres instead of studs
		source:ScaleTo(source:GetScale() * Rig.S)
		_, size = source:GetBoundingBox()
		warn("[TX6] import was metre-scale - scaled up by", Rig.S)
	end
	if math.abs(size.Z - expected.Z) > expected.Z * 0.06 or math.abs(size.X - expected.X) > expected.X * 0.06 then
		warn(string.format("[TX6] unexpected import size %.2f x %.2f x %.2f (expected %.2f x %.2f x %.2f) - "
			.. "check the importer used Stud units, scale 1, World Forward = Front, World Up = Top",
			size.X, size.Y, size.Z, expected.X, expected.Y, expected.Z))
	end
	local cf = source:GetBoundingBox()
	local shift = Rig.ImportCenter - cf.Position
	for _, d in source:GetDescendants() do
		if d:IsA("BasePart") then
			d.CFrame = d.CFrame + shift
		end
	end
end

local function install(source: Model?)
	source = source or findSource()
	assert(source, "[TX6] Import exports/TX6_Bastion_Roblox.fbx first (Home > Import 3D), then run the installer again.")

	-- ------------------------------------------------------------------ shared modules -> ReplicatedStorage.TX6
	local old = ReplicatedStorage:FindFirstChild("TX6")
	if old then
		old:Destroy()
	end
	local shared = kit.Shared:Clone()
	shared.Name = "TX6"
	shared.Parent = ReplicatedStorage
	local Shared = require(shared:WaitForChild("Shared"))
	local Rig, Config = Shared.Rig, Shared.Config

	-- ------------------------------------------------------------------ server + client scripts
	for _, s in kit.Server:GetChildren() do
		local prev = ServerScriptService:FindFirstChild(s.Name)
		if prev then
			prev:Destroy()
		end
		s:Clone().Parent = ServerScriptService
	end
	local sps = StarterPlayer:FindFirstChildOfClass("StarterPlayerScripts")
	for _, s in kit.Client:GetChildren() do
		local prev = sps:FindFirstChild(s.Name)
		if prev then
			prev:Destroy()
		end
		s:Clone().Parent = sps
	end

	-- ------------------------------------------------------------------ collision groups (saved in the place)
	local PhysicsService = game:GetService("PhysicsService")
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

	-- keep an untouched copy of the import so the installer can be re-run later without importing again
	if source.Parent ~= ServerStorage then
		local oldBackup = ServerStorage:FindFirstChild("TX6_ImportBackup")
		local fresh = source:Clone()
		fresh.Name = "TX6_ImportBackup"
		if oldBackup then
			oldBackup:Destroy()
		end
		fresh.Parent = ServerStorage
	end

	-- ------------------------------------------------------------------ build the vehicle
	normalise(source, Rig)
	local car = Instance.new("Model")
	car.Name = "TX6_Bastion"
	car.ModelStreamingMode = Enum.ModelStreamingMode.Atomic -- streams in as one piece (StreamingEnabled maps)
	car:SetAttribute("AdminOnly", true)
	car:SetAttribute("Scale", "1 stud = 0.28 m")
	car:SetAttribute("Source", "TX-6 Bastion (Blender build, exports/TX6_Bastion_Roblox.fbx)")

	local folders = {}
	for _, n in { "Joints", "Visual", "Collision", "Wheels", "Seats", "Lights", "Templates" } do
		local f = Instance.new("Folder")
		f.Name = n
		f.Parent = car
		folders[n] = f
	end

	-- physics chassis (the heavy, invisible root part)
	local chassis = part("Chassis", Rig.ChassisSize, CFrame.new(Rig.ChassisCenter), car)
	chassis.CustomPhysicalProperties = PhysicalProperties.new(Config.ChassisDensity, 0.3, 0, 1, 1)
	chassis.RootPriority = 127
	car.PrimaryPart = chassis

	-- collision boxes (the only colliders of the body; bullets / raycasts hit these)
	for _, b in Rig.Collision do
		local c = part(b.Name, b.Size, CFrame.new(b.Center), folders.Collision)
		c.CanCollide = true
		c.CanQuery = true
		c.Massless = true
		c.CollisionGroup = "TX6_Body"
		weld(chassis, c)
	end

	-- joint parts (one per moving group, at its hinge) connected with Motor6Ds
	local jointPart = {}
	for _, name in Rig.JointOrder do
		local j = Rig.Joints[name]
		if not j.Physics then
			local jp = part("J_" .. name, Vector3.new(0.2, 0.2, 0.2), CFrame.new(j.Pivot), folders.Joints)
			jp.Massless = true
			jointPart[name] = jp
		end
	end
	for _, name in Rig.JointOrder do
		local jp = jointPart[name]
		if jp then
			local parentName = Rig.Joints[name].Parent
			local p0 = jointPart[parentName] or chassis
			local m = Instance.new("Motor6D")
			m.Name = "Motor"
			m.Part0 = p0
			m.Part1 = jp
			m.C0 = p0.CFrame:ToObjectSpace(jp.CFrame)
			m.C1 = CFrame.identity
			m.Parent = jp
		end
	end

	-- ------------------------------------------------------------------ physics wheels + suspension + steering
	local R, W = Rig.WheelRadius, Rig.WheelWidth
	local strutOf, wheelOf = {}, {}
	local up = function(pos: Vector3)
		return CFrame.fromMatrix(pos, Vector3.yAxis, Vector3.zAxis) -- attachment X axis points up
	end
	local fwdAxle = function(pos: Vector3)
		return CFrame.fromMatrix(pos, -Vector3.xAxis, Vector3.yAxis) -- X axis = -X so +AngularVelocity drives forward
	end
	for tag, w in Rig.Wheels do
		local c = w.Center
		local strut = part("Strut_" .. tag, Vector3.new(0.6, 0.6, 0.6), CFrame.new(c), folders.Wheels)
		strut.CollisionGroup = "TX6_Wheels"
		strut.CustomPhysicalProperties = PhysicalProperties.new(2, 0.3, 0, 1, 1)
		local wheel = part("Wheel_" .. tag, Vector3.new(W, 2 * R, 2 * R), CFrame.new(c), folders.Wheels)
		wheel.Shape = Enum.PartType.Cylinder
		wheel.CanCollide = true
		wheel.CollisionGroup = "TX6_Wheels"
		wheel.CustomPhysicalProperties = PhysicalProperties.new(0.9, Config.TireFriction, 0.05, 100, 1)
		strutOf[tag], wheelOf[tag] = strut, wheel

		local a0 = attach("Susp_" .. tag, chassis, up(c))
		local a1 = attach("Susp", strut, up(c))
		local susp
		if w.Steer then
			susp = Instance.new("CylindricalConstraint")
			susp.InclinationAngle = 0 -- rotation axis = the attachment X axis (vertical) -> wheels steer
			susp.AngularActuatorType = Enum.ActuatorType.Servo
			susp.ServoMaxTorque = 5e7
			susp.AngularSpeed = Config.SteerSpeed
			susp.TargetAngle = 0
			susp.AngularLimitsEnabled = true
			susp.LowerAngle = -42
			susp.UpperAngle = 42
		else
			susp = Instance.new("PrismaticConstraint")
		end
		susp.Name = "Susp"
		susp.Attachment0 = a0
		susp.Attachment1 = a1
		susp.LimitsEnabled = true
		susp.LowerLimit = -Config.SuspensionDown
		susp.UpperLimit = Config.SuspensionUp
		susp.Parent = strut

		local top = attach("SpringTop_" .. tag, chassis, CFrame.new(c + Vector3.new(0, Rig.SpringTop, 0)))
		local bottom = attach("SpringBottom", strut, CFrame.new(c))
		local spring = Instance.new("SpringConstraint")
		spring.Name = "Spring"
		spring.Attachment0 = top
		spring.Attachment1 = bottom
		spring.FreeLength = Rig.SpringTop + Config.SuspensionSag
		spring.Stiffness = 30000 -- re-tuned from the real mass by TX6_Server when spawned
		spring.Damping = 1500
		spring.Visible = false
		spring.Parent = strut

		local ax0 = attach("Axle", strut, fwdAxle(c))
		local ax1 = attach("Axle", wheel, fwdAxle(c))
		local motor = Instance.new("HingeConstraint")
		motor.Name = "Motor"
		motor.Attachment0 = ax0
		motor.Attachment1 = ax1
		motor.ActuatorType = Enum.ActuatorType.Motor
		motor.AngularVelocity = 0
		motor.MotorMaxTorque = 2e6
		motor.MotorMaxAcceleration = 200
		motor.Parent = strut
	end

	-- ------------------------------------------------------------------ visual meshes: materials + welds
	local groupNames = { "Body" }
	for name in Rig.Joints do
		table.insert(groupNames, name)
	end
	table.sort(groupNames, function(a, b)
		return #a > #b
	end)
	local visualFolders = {}
	local unknown, count = 0, 0
	for _, d in source:GetDescendants() do
		if d:IsA("BasePart") and string.sub(d.Name, 1, 4) == "RBX_" then
			local rest = string.sub(d.Name, 5)
			local group
			for _, g in groupNames do
				if string.sub(rest, 1, #g + 1) == g .. "_" then
					group = g
					break
				end
			end
			if not group then
				unknown += 1
				warn("[TX6] unknown mesh name", d.Name)
				group = "Body"
			end
			local matName = string.gsub(string.sub(rest, #group + 2), "_%d+$", "")
			local m = Rig.Materials[matName]
			if m then
				d.Material = Enum.Material[m.Material]
				d.Color = m.Color
				d.Transparency = m.Transparency
				d.Reflectance = m.Reflectance
			end
			d:SetAttribute("TX6Mat", matName)
			d:SetAttribute("TX6Group", group)
			d.Name = matName
			d.Anchored = true
			d.CanCollide = false
			d.CanTouch = false
			d.CanQuery = false
			d.Massless = true
			if d:IsA("MeshPart") then
				pcall(function()
					d.CollisionFidelity = Enum.CollisionFidelity.Box
				end)
			end
			if m and (m.Material == "Neon" or m.Material == "Glass") then
				d.CastShadow = false
			end
			local vf = visualFolders[group]
			if not vf then
				vf = Instance.new("Model")
				vf.Name = group
				vf.Parent = folders.Visual
				visualFolders[group] = vf
			end
			d.Parent = vf
			local joint = Rig.Joints[group]
			local anchorPart
			if group == "Body" then
				anchorPart = chassis
			elseif joint and joint.Physics == "Strut" then
				anchorPart = strutOf[string.sub(group, -2)]
			elseif joint and joint.Physics == "Wheel" then
				anchorPart = wheelOf[string.sub(group, -2)]
			else
				anchorPart = jointPart[group] or chassis
			end
			weld(anchorPart, d)
			count += 1
		end
	end

	-- ------------------------------------------------------------------ seats
	for seatName, s in Rig.Seats do
		local cls = seatName == "DriverSeat" and "VehicleSeat" or "Seat"
		local seat = Instance.new(cls)
		seat.Name = seatName
		seat.Size = Vector3.new(2, 0.8, 2)
		seat.CFrame = CFrame.new(s.Position - Vector3.new(0, 0.4, 0))
		seat.Anchored = true
		seat.CanCollide = false
		seat.CanTouch = false -- players get in through the prompts, never by bumping into a seat
		seat.CanQuery = false
		seat.Transparency = 1
		seat.Massless = true
		if cls == "VehicleSeat" then
			seat.HeadsUpDisplay = false
			seat.MaxSpeed = 0
			seat.Torque = 0
			seat.TurnSpeed = 0
		end
		seat:SetAttribute("Role", s.Role)
		seat.Parent = folders.Seats
		weld(seatName == "GunnerSeat" and jointPart.Turret_Rotor or chassis, seat)
	end

	-- ------------------------------------------------------------------ prompts
	local P = Rig.Points
	local function prompt(point: string, action: string, kind: string, target: string, key: Enum.KeyCode, pad: Enum.KeyCode)
		local a = chassis:FindFirstChild(point)
		if not a then
			a = attach(point, chassis, CFrame.new(P[point]))
		end
		local pp = Instance.new("ProximityPrompt")
		pp.Name = kind .. "_" .. target
		pp.ActionText = action
		pp.ObjectText = "TX-6 Bastion"
		pp.KeyboardKeyCode = key
		pp.GamepadKeyCode = pad
		pp.HoldDuration = 0
		pp.MaxActivationDistance = 9
		pp.RequiresLineOfSight = false
		pp:SetAttribute("Kind", kind)
		pp:SetAttribute("Target", target)
		pp.Parent = a
		return pp
	end
	local E, F, T = Enum.KeyCode.E, Enum.KeyCode.F, Enum.KeyCode.T
	local BX, BY, BB = Enum.KeyCode.ButtonX, Enum.KeyCode.ButtonY, Enum.KeyCode.ButtonB
	prompt("P_DriverDoor", "Drive", "Seat", "DriverSeat", E, BX)
	prompt("P_DriverDoor", "Open / close door", "Channel", "Door_FL", F, BY)
	prompt("P_PassengerDoor", "Ride", "Seat", "PassengerSeat", E, BX)
	prompt("P_PassengerDoor", "Open / close door", "Channel", "Door_FR", F, BY)
	prompt("P_RearLeftDoor", "Ride", "Seat", "RearLeftSeat", E, BX)
	prompt("P_RearLeftDoor", "Man the turret", "Seat", "GunnerSeat", T, BB)
	prompt("P_RearLeftDoor", "Open / close door", "Channel", "Door_RL", F, BY)
	prompt("P_RearRightDoor", "Ride", "Seat", "RearRightSeat", E, BX)
	prompt("P_RearRightDoor", "Man the turret", "Seat", "GunnerSeat", T, BB)
	prompt("P_RearRightDoor", "Open / close door", "Channel", "Door_RR", F, BY)
	prompt("P_Rear", "Rear door + spare carrier", "Channel", "Rear", F, BY)
	prompt("P_LockerL", "Equipment bay (drone)", "Channel", "Locker_L", F, BY)
	prompt("P_LockerR", "Equipment bay (supplies)", "Channel", "Locker_R", F, BY)
	prompt("P_Hood", "Open / close hood", "Channel", "Hood", F, BY)
	prompt("P_Fuel", "Fuel door", "Channel", "Fuel", F, BY)

	-- ------------------------------------------------------------------ lights (start switched off)
	local function lightPart(name: string, point: string, anchor: BasePart, cls: string, props)
		local lp = part(name, Vector3.new(0.3, 0.3, 0.3), CFrame.new(P[point]), folders.Lights)
		lp.Massless = true
		weld(anchor, lp)
		local l = Instance.new(cls)
		for k, v in props do
			l[k] = v
		end
		l.Enabled = false
		l.Parent = lp
		return lp
	end
	local warm = Color3.fromRGB(255, 244, 225)
	lightPart("HeadlightL", "HeadlightL", chassis, "SpotLight", { Face = Enum.NormalId.Front, Range = 70, Angle = 70, Brightness = 4, Color = warm, Shadows = true })
	lightPart("HeadlightR", "HeadlightR", chassis, "SpotLight", { Face = Enum.NormalId.Front, Range = 70, Angle = 70, Brightness = 4, Color = warm, Shadows = true })
	lightPart("LightBar", "LightBar", chassis, "SpotLight", { Face = Enum.NormalId.Front, Range = 90, Angle = 100, Brightness = 3, Color = Color3.fromRGB(235, 240, 255) })
	lightPart("Searchlight", "SearchlightLamp", jointPart.Searchlight or chassis, "SpotLight", { Face = Enum.NormalId.Front, Range = 140, Angle = 16, Brightness = 7, Color = warm })
	for i = 1, 4 do
		lightPart("Beacon" .. i, "Beacon" .. i, chassis, "PointLight", { Range = 14, Brightness = 5, Color = Color3.fromRGB(255, 140, 25) })
	end
	lightPart("TailL", "TailL", chassis, "PointLight", { Range = 7, Brightness = 2, Color = Color3.fromRGB(255, 30, 20) })
	lightPart("TailR", "TailR", chassis, "PointLight", { Range = 7, Brightness = 2, Color = Color3.fromRGB(255, 30, 20) })
	lightPart("Dome", "Dome", chassis, "PointLight", { Range = 6, Brightness = 1, Color = Color3.fromRGB(255, 40, 30) })

	-- ------------------------------------------------------------------ scripts + remote
	local remote = Instance.new("RemoteEvent")
	remote.Name = "TX6Remote"
	remote.Parent = car
	kit.Vehicle.TX6_Server:Clone().Parent = car
	kit.Vehicle.TX6_DriverClient:Clone().Parent = folders.Templates
	kit.Vehicle.TX6_GunnerClient:Clone().Parent = folders.Templates

	-- ------------------------------------------------------------------ finish: unanchor, tag, store
	for _, d in car:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = false
		end
	end
	car.WorldPivot = CFrame.identity -- pivot = ground under the vehicle centre
	CollectionService:AddTag(car, "TX6_Vehicle")
	local store = ServerStorage:FindFirstChild("AdminVehicles")
	if not store then
		store = Instance.new("Folder")
		store.Name = "AdminVehicles"
		store.Parent = ServerStorage
	end
	local prev = store:FindFirstChild("TX6_Bastion")
	if prev then
		prev:Destroy()
	end
	car.Parent = store
	source:Destroy()

	print(string.format("[TX6] Installed: %d meshes, %d joints, %d unknown names. Vehicle stored in "
		.. "ServerStorage.AdminVehicles.TX6_Bastion. Press Play, then F4 (admin) to spawn it.",
		count, #folders.Joints:GetChildren(), unknown))
	return car
end

return install
