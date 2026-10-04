--!nonstrict
--[[
	TX-6 "Bastion" - shared maths used by the server AND the clients so they always agree.

	Vehicle space: origin on the ground under the vehicle centre, nose = -Z, up = +Y, vehicle RIGHT = +X (studs).
	Every moving group has an invisible joint part ("J_<name>") at its hinge; a Motor6D connects it to its parent.
	Clients animate by setting Motor6D.Transform; the server only does the maths (aim, muzzle, pods, missiles).
]]

local Shared = {}

local Config = require(script.Parent:WaitForChild("Config"))
local Rig = require(script.Parent:WaitForChild("RigData"))
Shared.Config = Config
Shared.Rig = Rig

-- how fast each animated "channel" travels from 0 (stowed / closed) to 1 (deployed / open), per second
Shared.ChannelSpeed = {
	Armor = 0.7, Missiles = 0.45, Mast = 0.38,
	Door_FL = 1.6, Door_FR = 1.6, Door_RL = 1.6, Door_RR = 1.6,
	Rear = 0.75, Locker_L = 0.8, Locker_R = 0.9, Hood = 0.8, Fuel = 1.5, Utility = 1.5,
}
Shared.Channels = {}
for name in Shared.ChannelSpeed do
	table.insert(Shared.Channels, name)
end
table.sort(Shared.Channels)

function Shared.Smooth(t: number): number
	t = math.clamp(t, 0, 1)
	return t * t * (3 - 2 * t)
end

-- move a channel value toward its target at the channel's speed
function Shared.Advance(channel: string, value: number, target: number, dt: number): number
	local step = (Shared.ChannelSpeed[channel] or 1) * dt
	if value < target then
		return math.min(target, value + step)
	end
	return math.max(target, value - step)
end

local function axisAngles(axis: string, radians: number): CFrame
	if axis == "X" then
		return CFrame.Angles(radians, 0, 0)
	elseif axis == "Y" then
		return CFrame.Angles(0, radians, 0)
	end
	return CFrame.Angles(0, 0, radians)
end

local function axisVector(axis: string): Vector3
	if axis == "X" then
		return Vector3.xAxis
	elseif axis == "Y" then
		return Vector3.yAxis
	end
	return Vector3.zAxis
end

-- local transform of one joint. progress = {channel = 0..1}; live = {Yaw, Pitch, Spin, HeadSpin} in radians
function Shared.JointTransform(name: string, progress, live): CFrame
	live = live or {}
	if name == "Turret_Rotor" then
		return CFrame.Angles(0, live.Yaw or 0, 0)
	elseif name == "Turret_Cradle" then
		return CFrame.Angles(live.Pitch or 0, 0, 0)
	elseif name == "Turret_Barrels" then
		return CFrame.Angles(0, 0, live.Spin or 0)
	elseif name == "Sensor_Head" then
		return CFrame.Angles(0, 0, live.HeadSpin or 0)
	end
	local joint = Rig.Joints[name]
	local drive = joint and joint.Drive
	if not drive then
		return CFrame.identity
	end
	local p = progress[drive.Channel] or 0
	local k = Shared.Smooth((p - drive.T0) / (drive.T1 - drive.T0))
	if drive.Kind == "rot" then
		return axisAngles(drive.Axis, math.rad(drive.Amount * k))
	end
	return CFrame.new(axisVector(drive.Axis) * (drive.Amount * k))
end

-- world frame of a joint (origin at its hinge, axes = vehicle axes at rest)
function Shared.JointWorld(vehicleCF: CFrame, name: string, progress, live): CFrame
	local joint = Rig.Joints[name]
	local parent = joint.Parent
	local parentCF, parentPivot
	if Rig.Joints[parent] then
		parentCF = Shared.JointWorld(vehicleCF, parent, progress, live)
		parentPivot = Rig.Joints[parent].Pivot
	else
		parentCF = vehicleCF
		parentPivot = Vector3.zero
	end
	return parentCF * CFrame.new(joint.Pivot - parentPivot) * Shared.JointTransform(name, progress, live)
end

-- the vehicle-space reference frame from the physics chassis part
function Shared.VehicleCF(chassis: BasePart): CFrame
	return chassis.CFrame * CFrame.new(-Rig.ChassisCenter)
end

-- muzzle of the rotary cannon: position at the barrel tips, LookVector = firing direction
function Shared.Muzzle(vehicleCF: CFrame, yaw: number, pitch: number): CFrame
	local cradle = Shared.JointWorld(vehicleCF, "Turret_Cradle", {}, { Yaw = yaw, Pitch = pitch })
	local pos = cradle:PointToWorldSpace(Rig.Points.Muzzle - Rig.Joints.Turret_Cradle.Pivot)
	return CFrame.lookAt(pos, pos + cradle.LookVector)
end

-- yaw / pitch (radians, vehicle space) that point the cannon at a world position
function Shared.AimAngles(vehicleCF: CFrame, worldPoint: Vector3): (number, number)
	local yaw, pitch = 0, 0
	for _ = 1, 3 do
		local cradle = Shared.JointWorld(vehicleCF, "Turret_Cradle", {}, { Yaw = yaw, Pitch = 0 })
		local rel = vehicleCF:VectorToObjectSpace(worldPoint - cradle.Position)
		yaw = math.atan2(-rel.X, -rel.Z)
		pitch = math.atan2(rel.Y, math.sqrt(rel.X * rel.X + rel.Z * rel.Z))
	end
	pitch = math.clamp(pitch, math.rad(Config.TurretPitchMin), math.rad(Config.TurretPitchMax))
	return yaw, pitch
end

-- launch tube exit of a missile pod ("L" or "R") when the bays are fully deployed
function Shared.PodLaunch(vehicleCF: CFrame, side: string): CFrame
	local name = "Missile_Pod_" .. side
	local pod = Shared.JointWorld(vehicleCF, name, { Missiles = 1 }, {})
	local pos = pod:PointToWorldSpace(Rig.Points["PodTube_" .. side] - Rig.Joints[name].Pivot)
	return CFrame.lookAt(pos, pos + pod.LookVector)
end

-- one homing-missile step (identical on server and clients). m = {Pos, Vel, Speed, Age}
function Shared.MissileStep(m, targetPos: Vector3?, dt: number): Vector3
	m.Age += dt
	m.Speed = math.min(Config.MissileSpeedMax, m.Speed + Config.MissileAccel * dt)
	local dir = m.Vel.Magnitude > 1e-3 and m.Vel.Unit or Vector3.zAxis
	if targetPos and m.Age > 0.25 then
		local to = targetPos - m.Pos
		if to.Magnitude > 1e-3 then
			local want = to.Unit
			local angle = math.acos(math.clamp(dir:Dot(want), -1, 1))
			if angle > 1e-4 then
				local axis = dir:Cross(want)
				if axis.Magnitude < 1e-6 then
					axis = dir:Cross(Vector3.yAxis)
					if axis.Magnitude < 1e-6 then
						axis = Vector3.xAxis
					end
				end
				local turn = math.min(angle, math.rad(Config.MissileTurnRateDeg) * dt)
				dir = CFrame.fromAxisAngle(axis.Unit, turn):VectorToWorldSpace(dir)
			end
		end
	end
	m.Vel = dir * m.Speed
	return m.Pos + m.Vel * dt
end

-- where a living target should be aimed at (nil if gone / dead)
function Shared.TargetPosition(model: Instance?): Vector3?
	if not model or not model.Parent then
		return nil
	end
	local hum = model:FindFirstChildOfClass("Humanoid")
	if hum and hum.Health <= 0 then
		return nil
	end
	local root = model:FindFirstChild("HumanoidRootPart") or model:FindFirstChild("Torso")
		or model:FindFirstChild("UpperTorso") or (model:IsA("Model") and model.PrimaryPart)
	if root and root:IsA("BasePart") then
		return root.Position
	end
	return nil
end

-- the Humanoid that owns a hit part (nil if none)
function Shared.HumanoidFromPart(part: Instance?): Humanoid?
	local node = part
	while node and node ~= workspace do
		local hum = node:FindFirstChildOfClass("Humanoid")
		if hum then
			return hum
		end
		node = node.Parent
	end
	return nil
end

return Shared
