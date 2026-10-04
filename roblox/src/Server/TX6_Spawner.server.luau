--!nonstrict
--[[
	TX-6 "Bastion" - admin spawner (ServerScriptService).

	Admins (same rule as AdminService: Studio, IsAdmin attribute, game owner or group rank 255) can:
	  F4 / chat "/tx6"            -> spawn a TX-6 26 studs in front of them
	  Shift+F4 / "/tx6 remove"    -> remove their TX-6
	The server checks admin rights on every request.
]]

local Players = game:GetService("Players")
local ServerStorage = game:GetService("ServerStorage")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local PhysicsService = game:GetService("PhysicsService")

local folder = ReplicatedStorage:WaitForChild("TX6")
local Shared = require(folder:WaitForChild("Shared"))
local Config = Shared.Config

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

local request = folder:FindFirstChild("TX6_SpawnRequest")
if not request then
	request = Instance.new("RemoteEvent")
	request.Name = "TX6_SpawnRequest"
	request.Parent = folder
end

local owned: { [Player]: Model } = {}
local lastRequest: { [Player]: number } = {}

local function template(): Model?
	local store = ServerStorage:FindFirstChild("AdminVehicles")
	local t = store and store:FindFirstChild("TX6_Bastion")
	if t and t:IsA("Model") then
		return t
	end
	warn("[TX6] ServerStorage.AdminVehicles.TX6_Bastion is missing - run the installer again")
	return nil
end

local function despawn(player: Player)
	local car = owned[player]
	if car then
		owned[player] = nil
		car:Destroy()
	end
end

local function spawnFor(player: Player)
	if not Config.IsAdmin(player) then
		return
	end
	local t = template()
	local char = player.Character
	local root = char and char:FindFirstChild("HumanoidRootPart")
	if not t or not root or not root:IsA("BasePart") then
		return
	end
	if Config.OneVehiclePerAdmin then
		despawn(player)
	end
	local look = root.CFrame.LookVector
	local flat = Vector3.new(look.X, 0, look.Z)
	if flat.Magnitude < 0.1 then
		flat = Vector3.new(0, 0, -1)
	end
	flat = flat.Unit
	local spot = root.Position + flat * 26
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { char }
	local hit = workspace:Raycast(spot + Vector3.new(0, 40, 0), Vector3.new(0, -250, 0), params)
	local ground = hit and hit.Position or Vector3.new(spot.X, root.Position.Y - 3, spot.Z)
	local base = ground + Vector3.new(0, 1.0, 0)
	local car = t:Clone()
	car.Name = "TX6_Bastion_" .. player.Name
	car:SetAttribute("Owner", player.UserId)
	car:PivotTo(CFrame.lookAt(base, base + flat)) -- nose points the way you are looking
	car.Parent = workspace
	owned[player] = car
	car.Destroying:Connect(function()
		if owned[player] == car then
			owned[player] = nil
		end
	end)
end

local function handle(player: Player, action)
	local now = os.clock()
	if lastRequest[player] and now - lastRequest[player] < 1.5 then
		return
	end
	lastRequest[player] = now
	if action == "Spawn" then
		spawnFor(player)
	elseif action == "Despawn" and Config.IsAdmin(player) then
		despawn(player)
	end
end

request.OnServerEvent:Connect(handle)

local function hookChat(player: Player)
	player.Chatted:Connect(function(msg)
		local m = string.lower(msg)
		if m == Config.ChatCommand then
			handle(player, "Spawn")
		elseif m == Config.ChatCommand .. " remove" then
			handle(player, "Despawn")
		end
	end)
end
for _, p in Players:GetPlayers() do
	hookChat(p)
end
Players.PlayerAdded:Connect(hookChat)
Players.PlayerRemoving:Connect(function(player)
	despawn(player)
	lastRequest[player] = nil
end)
