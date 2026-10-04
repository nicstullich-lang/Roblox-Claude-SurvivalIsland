--!nonstrict
--[[
	TX-6 "Bastion" - driver controls (given to the player in the driver's seat, removed when they leave).

	The server hands physics ownership to the driver, so this script sets the wheel motors and steering directly
	for lag-free driving. Works with keyboard, gamepad and touch (VehicleSeat throttle/steer values).
]]

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local ContextActionService = game:GetService("ContextActionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local gui = script.Parent
local vehicleRef = gui:WaitForChild("Vehicle") :: ObjectValue
local vehicle = vehicleRef.Value
local waited = 0
while not vehicle and waited < 10 do
	waited += task.wait(0.1)
	vehicle = vehicleRef.Value
end
if not vehicle then
	return
end
local Shared = require(ReplicatedStorage:WaitForChild("TX6"):WaitForChild("Shared"))
local Config, Rig = Shared.Config, Shared.Rig

local player = Players.LocalPlayer
local chassis = vehicle:WaitForChild("Chassis") :: BasePart
local seat = vehicle:WaitForChild("Seats"):WaitForChild("DriverSeat") :: VehicleSeat
local remote = vehicle:WaitForChild("TX6Remote") :: RemoteEvent
local wheelsFolder = vehicle:WaitForChild("Wheels")

local motors: { [string]: HingeConstraint } = {}
local steering: { [string]: CylindricalConstraint } = {}
local wheelParts: { BasePart } = {}
for _, tag in { "FL", "FR", "RL", "RR" } do
	local strut = wheelsFolder:WaitForChild("Strut_" .. tag)
	motors[tag] = strut:WaitForChild("Motor") :: HingeConstraint
	local susp = strut:WaitForChild("Susp")
	if susp:IsA("CylindricalConstraint") then
		steering[tag] = susp
	end
	table.insert(wheelParts, wheelsFolder:WaitForChild("Wheel_" .. tag) :: BasePart)
end

local character = player.Character
local humanoid = character and character:FindFirstChildOfClass("Humanoid")

-- ====================================================================== HUD
local function label(parent: Instance, text: string, size: UDim2, pos: UDim2, textSize: number, color: Color3?)
	local l = Instance.new("TextLabel")
	l.BackgroundTransparency = 1
	l.Size = size
	l.Position = pos
	l.Font = Enum.Font.GothamBold
	l.TextSize = textSize
	l.TextColor3 = color or Color3.fromRGB(230, 235, 220)
	l.Text = text
	l.Parent = parent
	return l
end

local panel = Instance.new("Frame")
panel.Name = "DriverPanel"
panel.AnchorPoint = Vector2.new(0.5, 1)
panel.Position = UDim2.new(0.5, 0, 1, -18)
panel.Size = UDim2.fromOffset(420, 92)
panel.BackgroundColor3 = Color3.fromRGB(18, 20, 16)
panel.BackgroundTransparency = 0.25
panel.Parent = gui
Instance.new("UICorner").Parent = panel
local stroke = Instance.new("UIStroke")
stroke.Color = Color3.fromRGB(120, 130, 90)
stroke.Transparency = 0.4
stroke.Parent = panel

local speedLabel = label(panel, "0", UDim2.fromOffset(110, 52), UDim2.fromOffset(12, 6), 46)
local unitLabel = label(panel, "km/h", UDim2.fromOffset(60, 20), UDim2.fromOffset(120, 34), 14, Color3.fromRGB(160, 170, 140))
local gearLabel = label(panel, "N", UDim2.fromOffset(40, 40), UDim2.fromOffset(180, 10), 32, Color3.fromRGB(255, 200, 80))
local statusLabel = label(panel, "", UDim2.fromOffset(200, 40), UDim2.fromOffset(214, 10), 13)
statusLabel.TextXAlignment = Enum.TextXAlignment.Left
statusLabel.TextWrapped = true
statusLabel.RichText = true
local hint = label(panel, string.format("W/S drive  A/D steer  %s handbrake  %s lights  %s beacons  %s armour  %s mast  %s flip  Space exit",
	Config.HandbrakeKey.Name, Config.LightsKey.Name, Config.BeaconsKey.Name, Config.ArmorKey.Name, Config.MastKey.Name,
	Config.FlipKey.Name), UDim2.new(1, -20, 0, 18), UDim2.fromOffset(10, 66), 11, Color3.fromRGB(150, 160, 130))
hint.TextXAlignment = Enum.TextXAlignment.Left
unitLabel.TextXAlignment = Enum.TextXAlignment.Left

-- ====================================================================== input
local handbrake = false
local bound = {}
local function bindPress(name: string, action: string, ...)
	ContextActionService:BindAction(name, function(_, state)
		if state == Enum.UserInputState.Begin then
			remote:FireServer(action)
		end
		return Enum.ContextActionResult.Sink
	end, false, ...)
	table.insert(bound, name)
end
bindPress("TX6_Lights", "Lights", Config.LightsKey, Enum.KeyCode.DPadUp)
bindPress("TX6_Beacons", "Beacons", Config.BeaconsKey, Enum.KeyCode.DPadDown)
bindPress("TX6_Armor", "Armor", Config.ArmorKey, Enum.KeyCode.DPadLeft)
bindPress("TX6_Mast", "Mast", Config.MastKey, Enum.KeyCode.DPadRight)
bindPress("TX6_Horn", "Horn", Config.HornKey, Enum.KeyCode.ButtonL3)
bindPress("TX6_Flip", "Flip", Config.FlipKey, Enum.KeyCode.ButtonY)
ContextActionService:BindAction("TX6_Handbrake", function(_, state)
	handbrake = state == Enum.UserInputState.Begin or state == Enum.UserInputState.Change
	return Enum.ContextActionResult.Sink
end, true, Config.HandbrakeKey, Enum.KeyCode.ButtonB)
ContextActionService:SetTitle("TX6_Handbrake", "BRAKE")
table.insert(bound, "TX6_Handbrake")

-- pull the camera out a bit: the TX-6 is big
local savedMinZoom = player.CameraMinZoomDistance
player.CameraMinZoomDistance = math.max(savedMinZoom, 18)

-- ====================================================================== drive loop
local lastBrake = false
local hudClock = 0
local conn: RBXScriptConnection? = nil
local cleaned = false

local function cleanup()
	if cleaned then
		return
	end
	cleaned = true
	if conn then
		conn:Disconnect()
	end
	for _, name in bound do
		ContextActionService:UnbindAction(name)
	end
	player.CameraMinZoomDistance = savedMinZoom
end
script.Destroying:Connect(cleanup)

conn = RunService.Heartbeat:Connect(function(dt)
	if not vehicle.Parent or not humanoid or seat.Occupant ~= humanoid then
		cleanup()
		return
	end
	local throttle = seat.ThrottleFloat
	local steerIn = seat.SteerFloat
	local cf = chassis.CFrame
	local speed = chassis.AssemblyLinearVelocity:Dot(cf.LookVector) -- studs/s, + = forward
	local mass = chassis.AssemblyMass
	for _, w in wheelParts do
		mass += w.AssemblyMass
	end
	local r = Rig.WheelRadius

	local targetW, accel, braking = 0, Config.CoastDecel, false
	if handbrake then
		targetW, accel, braking = 0, Config.BrakeDecel, true
	elseif throttle > 0.05 then
		if speed < -1.5 then
			targetW, accel, braking = 0, Config.BrakeDecel, true
		else
			targetW, accel = throttle * Config.MaxSpeed / r, Config.Acceleration
		end
	elseif throttle < -0.05 then
		if speed > 1.5 then
			targetW, accel, braking = 0, Config.BrakeDecel, true
		else
			targetW, accel = throttle * Config.ReverseSpeed / r, Config.Acceleration * 0.7
		end
	end
	-- torque each wheel needs for that acceleration (+40% for hills / grip losses)
	local torque = mass * accel * r / 4 * 1.4
	for _, m in motors do
		m.AngularVelocity = targetW
		m.MotorMaxTorque = torque
		m.MotorMaxAcceleration = math.max(accel / r * 2, 5)
	end

	-- speed-sensitive steering with Ackermann geometry (inner wheel turns more)
	local frac = math.clamp(math.abs(speed) / Config.MaxSpeed, 0, 1)
	local maxDeg = Config.SteerMaxDeg + (Config.SteerMaxDegAtSpeed - Config.SteerMaxDeg) * frac
	local angle = -steerIn * maxDeg -- positive = turn left
	local inner, outer = angle * 1.12, angle * 0.88
	if steering.FL then
		steering.FL.TargetAngle = angle > 0 and inner or outer
	end
	if steering.FR then
		steering.FR.TargetAngle = angle > 0 and outer or inner
	end

	if braking ~= lastBrake then
		lastBrake = braking
		remote:FireServer("Brake", braking)
	end

	hudClock += dt
	if hudClock > 0.1 then
		hudClock = 0
		speedLabel.Text = tostring(math.floor(math.abs(speed) * 0.28 * 3.6 + 0.5))
		gearLabel.Text = (speed < -1 or throttle < -0.05) and "R" or ((throttle > 0.05 or speed > 1) and "D" or "N")
		local function chip(on: boolean, text: string)
			return string.format('<font color="%s">%s</font>', on and "#9BE564" or "#5E6652", text)
		end
		statusLabel.Text = table.concat({
			chip(vehicle:GetAttribute("LightsOn") == true, "LIGHTS"),
			chip(vehicle:GetAttribute("BeaconsOn") == true, "BEACONS"),
			chip(vehicle:GetAttribute("T_Armor") == 1, "ARMOUR"),
			chip(vehicle:GetAttribute("T_Mast") == 1, "MAST"),
			chip(handbrake, "HANDBRAKE"),
		}, "  ")
	end
end)

-- touch players get a horn / lights button through ContextActionService automatically when createTouchButton is true
if UserInputService.TouchEnabled then
	ContextActionService:BindAction("TX6_TouchLights", function(_, state)
		if state == Enum.UserInputState.Begin then
			remote:FireServer("Lights")
		end
		return Enum.ContextActionResult.Sink
	end, true)
	ContextActionService:SetTitle("TX6_TouchLights", "LIGHTS")
	table.insert(bound, "TX6_TouchLights")
end
