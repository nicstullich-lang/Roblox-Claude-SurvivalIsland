--!nonstrict
--[[
	TX-6 "Bastion" - gunner controls (given to the player in the turret's sling seat).

	Mouse / right stick aims (the turret follows the crosshair at a realistic traverse speed),
	Left mouse / R2 = rotary cannon, R = open / close missile bays, hold the crosshair on a target to lock,
	F / right mouse / L2 = fire missile, M = sensor mast (radar appears when it is up).
	The server re-checks everything; this script only aims, asks and draws the HUD.
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
local Config = Shared.Config

local player = Players.LocalPlayer
local camera = workspace.CurrentCamera
local chassis = vehicle:WaitForChild("Chassis") :: BasePart
local seat = vehicle:WaitForChild("Seats"):WaitForChild("GunnerSeat") :: Seat
local seatsFolder = vehicle:WaitForChild("Seats")
local remote = vehicle:WaitForChild("TX6Remote") :: RemoteEvent
local character = player.Character
local humanoid = character and character:FindFirstChildOfClass("Humanoid")

-- ====================================================================== HUD
local function frame(parent: Instance, size: UDim2, pos: UDim2, color: Color3, transparency: number?)
	local f = Instance.new("Frame")
	f.Size = size
	f.Position = pos
	f.BackgroundColor3 = color
	f.BackgroundTransparency = transparency or 0
	f.BorderSizePixel = 0
	f.Parent = parent
	return f
end
local function text(parent: Instance, s: string, size: UDim2, pos: UDim2, ts: number, color: Color3?)
	local l = Instance.new("TextLabel")
	l.BackgroundTransparency = 1
	l.Size = size
	l.Position = pos
	l.Font = Enum.Font.GothamBold
	l.TextSize = ts
	l.TextColor3 = color or Color3.fromRGB(230, 235, 220)
	l.Text = s
	l.Parent = parent
	return l
end

local green = Color3.fromRGB(155, 229, 100)
local cross = frame(gui, UDim2.fromOffset(44, 44), UDim2.new(0.5, -22, 0.5, -22), Color3.new(0, 0, 0), 1)
for _, spec in { { 20, 2, 0, 21 }, { 20, 2, 24, 21 }, { 2, 20, 21, 0 }, { 2, 20, 21, 24 } } do
	frame(cross, UDim2.fromOffset(spec[1], spec[2]), UDim2.fromOffset(spec[3], spec[4]), green)
end
frame(cross, UDim2.fromOffset(4, 4), UDim2.fromOffset(20, 20), green)

local panel = frame(gui, UDim2.fromOffset(360, 84), UDim2.new(0.5, -180, 1, -102), Color3.fromRGB(18, 20, 16), 0.25)
Instance.new("UICorner").Parent = panel
text(panel, "CANNON HEAT", UDim2.fromOffset(110, 18), UDim2.fromOffset(10, 6), 12).TextXAlignment = Enum.TextXAlignment.Left
local heatBack = frame(panel, UDim2.fromOffset(220, 10), UDim2.fromOffset(126, 10), Color3.fromRGB(50, 55, 45))
local heatBar = frame(heatBack, UDim2.fromScale(0, 1), UDim2.fromScale(0, 0), green)
local missileText = text(panel, "", UDim2.new(1, -20, 0, 20), UDim2.fromOffset(10, 28), 13)
missileText.TextXAlignment = Enum.TextXAlignment.Left
missileText.RichText = true
local hint = text(panel, string.format("LMB fire   %s bays   hold on target to lock   %s / RMB missile   %s mast   Space exit",
	Config.MissileKeyDeploy.Name, Config.MissileKeyFire.Name, Config.MastKey.Name), UDim2.new(1, -20, 0, 18),
	UDim2.fromOffset(10, 58), 11, Color3.fromRGB(150, 160, 130))
hint.TextXAlignment = Enum.TextXAlignment.Left

local lockBox = frame(gui, UDim2.fromOffset(64, 64), UDim2.fromOffset(0, 0), Color3.new(0, 0, 0), 1)
lockBox.AnchorPoint = Vector2.new(0.5, 0.5)
lockBox.Visible = false
local lockStroke = Instance.new("UIStroke")
lockStroke.Thickness = 2
lockStroke.Parent = lockBox
local lockText = text(lockBox, "", UDim2.new(1, 40, 0, 16), UDim2.new(0, -20, 1, 4), 12)

local radar = frame(gui, UDim2.fromOffset(180, 180), UDim2.new(1, -200, 1, -220), Color3.fromRGB(10, 20, 12), 0.3)
local radarCorner = Instance.new("UICorner")
radarCorner.CornerRadius = UDim.new(0.5, 0)
radarCorner.Parent = radar
local radarStroke = Instance.new("UIStroke")
radarStroke.Color = green
radarStroke.Transparency = 0.4
radarStroke.Parent = radar
frame(radar, UDim2.fromOffset(6, 6), UDim2.fromOffset(87, 87), green)
text(radar, "RADAR 600", UDim2.fromOffset(180, 14), UDim2.fromOffset(0, 4), 10, green)
radar.Visible = false
local blips = {}


-- ====================================================================== targets (every Humanoid in the world)
local humanoids: { [Humanoid]: boolean } = {}
for _, d in workspace:GetDescendants() do
	if d:IsA("Humanoid") then
		humanoids[d] = true
	end
end
local addConn = workspace.DescendantAdded:Connect(function(d)
	if d:IsA("Humanoid") then
		humanoids[d] = true
	end
end)
local remConn = workspace.DescendantRemoving:Connect(function(d)
	if d:IsA("Humanoid") then
		humanoids[d] = nil
	end
end)

local function isCrew(model: Instance): boolean
	for _, s in seatsFolder:GetChildren() do
		if (s:IsA("Seat") or s:IsA("VehicleSeat")) and s.Occupant and s.Occupant.Parent == model then
			return true
		end
	end
	return false
end

local function validTarget(h: Humanoid): boolean
	local model = h.Parent
	if not model or h.Health <= 0 or model == player.Character or model:IsDescendantOf(vehicle) or isCrew(model) then
		return false
	end
	if not Config.DamagePlayers and Players:GetPlayerFromCharacter(model) then
		return false
	end
	return true
end

-- ====================================================================== input
local bound = {}
local firing = false
local lockTarget: Model? = nil
local function setFiring(on: boolean)
	if firing ~= on then
		firing = on
		remote:FireServer("Fire", on)
	end
end
local function launch()
	if lockTarget then
		remote:FireServer("Launch", lockTarget)
	end
end
ContextActionService:BindActionAtPriority("TX6_Fire", function(_, state)
	setFiring(state == Enum.UserInputState.Begin or state == Enum.UserInputState.Change)
	return Enum.ContextActionResult.Sink
end, true, 3000, Enum.UserInputType.MouseButton1, Enum.KeyCode.ButtonR2)
ContextActionService:SetTitle("TX6_Fire", "FIRE")
ContextActionService:BindActionAtPriority("TX6_Launch", function(_, state)
	if state == Enum.UserInputState.Begin then
		launch()
	end
	return Enum.ContextActionResult.Sink
end, true, 3000, Config.MissileKeyFire, Enum.UserInputType.MouseButton2, Enum.KeyCode.ButtonL2)
ContextActionService:SetTitle("TX6_Launch", "MISSILE")
ContextActionService:BindAction("TX6_Bays", function(_, state)
	if state == Enum.UserInputState.Begin then
		remote:FireServer("MissileDeploy")
	end
	return Enum.ContextActionResult.Sink
end, true, Config.MissileKeyDeploy, Enum.KeyCode.ButtonY)
ContextActionService:SetTitle("TX6_Bays", "BAYS")
ContextActionService:BindAction("TX6_GunnerMast", function(_, state)
	if state == Enum.UserInputState.Begin then
		remote:FireServer("Mast")
	end
	return Enum.ContextActionResult.Sink
end, false, Config.MastKey, Enum.KeyCode.DPadRight)
bound = { "TX6_Fire", "TX6_Launch", "TX6_Bays", "TX6_GunnerMast" }

-- ====================================================================== aim + lock loop
local aimYaw = vehicle:GetAttribute("TurretYaw") or 0
local aimPitch = vehicle:GetAttribute("TurretPitch") or 0
local sentYaw, sentPitch, sendClock = 999, 999, 0
local candidate: Model? = nil
local lockTimer = 0
local missilesProgress = 0
local mastProgress = 0
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
	addConn:Disconnect()
	remConn:Disconnect()
	for _, n in bound do
		ContextActionService:UnbindAction(n)
	end
	if firing then
		remote:FireServer("Fire", false)
	end
	vehicle:SetAttribute("ClientYaw", nil)
	vehicle:SetAttribute("ClientPitch", nil)
	UserInputService.MouseBehavior = Enum.MouseBehavior.Default
	UserInputService.MouseIconEnabled = true
end
script.Destroying:Connect(cleanup)

local function angleTo(a: number, b: number, maxStep: number): number
	local d = (b - a + math.pi) % (2 * math.pi) - math.pi
	return a + math.clamp(d, -maxStep, maxStep)
end

conn = RunService.RenderStepped:Connect(function(dt)
	if not vehicle.Parent or not humanoid or seat.Occupant ~= humanoid then
		cleanup()
		return
	end
	if not UserInputService.TouchEnabled then
		UserInputService.MouseBehavior = Enum.MouseBehavior.LockCenter
		UserInputService.MouseIconEnabled = false
	end

	-- 1) aim point = what the crosshair (screen centre) is looking at
	local camCF = camera.CFrame
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { vehicle, player.Character }
	local hit = workspace:Raycast(camCF.Position, camCF.LookVector * 1500, params)
	local aimPoint = hit and hit.Position or (camCF.Position + camCF.LookVector * 1500)
	local vcf = Shared.VehicleCF(chassis)
	local wantYaw, wantPitch = Shared.AimAngles(vcf, aimPoint)
	aimYaw = angleTo(aimYaw, wantYaw, math.rad(140) * dt)          -- turret traverse 140 deg/s
	aimPitch = angleTo(aimPitch, wantPitch, math.rad(90) * dt)     -- elevation 90 deg/s
	vehicle:SetAttribute("ClientYaw", aimYaw)                       -- local only: smooth turret on this screen
	vehicle:SetAttribute("ClientPitch", aimPitch)
	sendClock += dt
	if sendClock > 1 / 15 and (math.abs(aimYaw - sentYaw) > 0.002 or math.abs(aimPitch - sentPitch) > 0.002) then
		sendClock = 0
		sentYaw, sentPitch = aimYaw, aimPitch
		remote:FireServer("Aim", aimYaw, aimPitch)
	end

	-- 2) lock-on: keep the crosshair on a target for MissileLockTime seconds
	missilesProgress = Shared.Advance("Missiles", missilesProgress, vehicle:GetAttribute("T_Missiles") or 0, dt)
	mastProgress = Shared.Advance("Mast", mastProgress, vehicle:GetAttribute("T_Mast") or 0, dt)
	local range = Config.MissileRange * (mastProgress >= 0.99 and 2 or 1)
	local look = camCF.LookVector
	local function coneAngle(model: Model): number?
		local pos = Shared.TargetPosition(model)
		if not pos or (pos - chassis.Position).Magnitude > range then
			return nil
		end
		return math.deg(math.acos(math.clamp((pos - camCF.Position).Unit:Dot(look), -1, 1)))
	end
	if lockTarget then
		local h = lockTarget:FindFirstChildOfClass("Humanoid")
		local a = coneAngle(lockTarget)
		if not h or not validTarget(h) or not a or a > Config.MissileKeepLockConeDeg then
			lockTarget = nil
		end
	end
	if not lockTarget then
		local best, bestA = nil, nil
		for h in humanoids do
			if h.Parent and validTarget(h) then
				local a = coneAngle(h.Parent)
				if a and a < Config.MissileLockConeDeg and (not bestA or a < bestA) then
					best, bestA = h.Parent, a
				end
			end
		end
		if best and best == candidate then
			lockTimer += dt
			if lockTimer >= Config.MissileLockTime then
				local pos = Shared.TargetPosition(best)
				local los = pos and workspace:Raycast(camCF.Position, pos - camCF.Position, params)
				if pos and (not los or los.Instance:IsDescendantOf(best)) then
					lockTarget = best
				end
			end
		else
			candidate = best
			lockTimer = 0
		end
	end

	-- 3) HUD
	local heat = vehicle:GetAttribute("Heat") or 0
	heatBar.Size = UDim2.fromScale(heat, 1)
	heatBar.BackgroundColor3 = vehicle:GetAttribute("Overheated") and Color3.fromRGB(240, 60, 40)
		or Color3.fromRGB(155 + 100 * heat, 229 - 120 * heat, 100 - 60 * heat)
	local bays = vehicle:GetAttribute("T_Missiles") == 1
	local state = bays and (missilesProgress >= 0.999 and '<font color="#9BE564">READY</font>' or "OPENING...")
		or (missilesProgress > 0.001 and "CLOSING..." or '<font color="#8A8F7E">BAYS CLOSED</font>')
	missileText.Text = string.format("MISSILES  L %d  |  R %d     %s     range %d",
		vehicle:GetAttribute("MissilesL") or 0, vehicle:GetAttribute("MissilesR") or 0, state, range)
	local shown = lockTarget or candidate
	local showPos = shown and Shared.TargetPosition(shown)
	if showPos then
		local sp, onScreen = camera:WorldToViewportPoint(showPos)
		lockBox.Visible = onScreen
		lockBox.Position = UDim2.fromOffset(sp.X, sp.Y)
		if lockTarget then
			lockStroke.Color = Color3.fromRGB(255, 60, 40)
			lockText.Text = "LOCKED"
			lockBox.Size = UDim2.fromOffset(48, 48)
		else
			local k = math.clamp(lockTimer / Config.MissileLockTime, 0, 1)
			lockStroke.Color = Color3.fromRGB(255, 210, 80)
			lockText.Text = "LOCKING"
			lockBox.Size = UDim2.fromOffset(90 - 42 * k, 90 - 42 * k)
		end
	else
		lockBox.Visible = false
	end

	-- 4) radar while the mast is up
	radar.Visible = mastProgress >= 0.99
	if radar.Visible then
		local i = 0
		for h in humanoids do
			if h.Parent and h.Health > 0 and h.Parent ~= player.Character then
				local pos = Shared.TargetPosition(h.Parent)
				if pos then
					local rel = vcf:PointToObjectSpace(pos)
					local d = Vector2.new(rel.X, rel.Z)
					if d.Magnitude < 600 then
						i += 1
						local b = blips[i]
						if not b then
							b = frame(radar, UDim2.fromOffset(5, 5), UDim2.fromOffset(0, 0), Color3.fromRGB(255, 90, 60))
							b.AnchorPoint = Vector2.new(0.5, 0.5)
							blips[i] = b
						end
						b.Visible = true
						b.Position = UDim2.fromOffset(90 + d.X / 600 * 86, 90 + d.Y / 600 * 86)
						b.BackgroundColor3 = Players:GetPlayerFromCharacter(h.Parent) and Color3.fromRGB(90, 170, 255)
							or Color3.fromRGB(255, 90, 60)
					end
				end
			end
		end
		for j = i + 1, #blips do
			blips[j].Visible = false
		end
	end
end)
