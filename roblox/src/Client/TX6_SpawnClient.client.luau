--!nonstrict
--[[
	TX-6 "Bastion" - admin spawn key (StarterPlayerScripts).
	F4 = spawn a TX-6 in front of you, Shift+F4 = remove it. The server decides if you are allowed.
]]

local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local folder = ReplicatedStorage:WaitForChild("TX6")
local Config = require(folder:WaitForChild("Config"))
local request = folder:WaitForChild("TX6_SpawnRequest", 30)
local player = Players.LocalPlayer

if not request then
	warn("[TX6] spawn remote not found - is TX6_Spawner in ServerScriptService?")
	return
end

UserInputService.InputBegan:Connect(function(input, processed)
	if processed or input.KeyCode ~= Config.SpawnKey then
		return
	end
	local shift = UserInputService:IsKeyDown(Enum.KeyCode.LeftShift) or UserInputService:IsKeyDown(Enum.KeyCode.RightShift)
	request:FireServer(shift and "Despawn" or "Spawn")
end)

-- small hint for admins
task.spawn(function()
	local ok, admin = pcall(Config.IsAdmin, player)
	if not ok or not admin then
		return
	end
	local gui = Instance.new("ScreenGui")
	gui.Name = "TX6_AdminHint"
	gui.ResetOnSpawn = false
	local l = Instance.new("TextLabel")
	l.BackgroundColor3 = Color3.fromRGB(18, 20, 16)
	l.BackgroundTransparency = 0.3
	l.Size = UDim2.fromOffset(420, 28)
	l.Position = UDim2.new(0, 16, 1, -150)
	l.Font = Enum.Font.GothamBold
	l.TextSize = 13
	l.TextColor3 = Color3.fromRGB(200, 215, 170)
	l.Text = string.format("ADMIN  TX-6 Bastion: %s spawn  -  Shift+%s remove  -  chat %s",
		Config.SpawnKey.Name, Config.SpawnKey.Name, Config.ChatCommand)
	l.Parent = gui
	Instance.new("UICorner").Parent = l
	gui.Parent = player:WaitForChild("PlayerGui")
	task.wait(12)
	gui:Destroy()
end)
