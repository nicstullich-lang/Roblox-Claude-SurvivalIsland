"""Type-check + lint the Roblox kit with luau-lsp (Roblox API definitions) using a sourcemap of the runtime layout."""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
LSP = os.environ.get('LUAU_LSP', '/tmp/luau-lsp/build/luau-lsp')
DEFS = os.environ.get('LUAU_DEFS', '/tmp/luau-lsp/scripts/globalTypes.d.luau')


def node(name, cls, path=None, children=None):
    n = {'name': name, 'className': cls}
    if path:
        n['filePaths'] = ['src/' + path]
    if children:
        n['children'] = children
    return n


shared = [node('Config', 'ModuleScript', 'TX6/Config.luau'), node('RigData', 'ModuleScript', 'TX6/RigData.luau'),
          node('Shared', 'ModuleScript', 'TX6/Shared.luau')]
vehicle_children = [
    node('TX6_Server', 'Script', 'Vehicle/TX6_Server.server.luau'),
    node('Chassis', 'Part'), node('TX6Remote', 'RemoteEvent'),
    node('Templates', 'Folder', None, [node('TX6_DriverClient', 'LocalScript', 'Vehicle/TX6_DriverClient.client.luau'),
                                       node('TX6_GunnerClient', 'LocalScript', 'Vehicle/TX6_GunnerClient.client.luau')]),
]
sm = node('Game', 'DataModel', None, [
    node('ReplicatedStorage', 'ReplicatedStorage', None, [node('TX6', 'Folder', None, shared)]),
    node('ServerStorage', 'ServerStorage', None, [node('TX6_Kit', 'Folder', None, [
        node('Install', 'ModuleScript', 'Install.luau'),
        node('Shared', 'Folder', None, [dict(n, filePaths=n['filePaths']) for n in shared])])]),
    node('ServerScriptService', 'ServerScriptService', None, [node('TX6_Spawner', 'Script', 'Server/TX6_Spawner.server.luau')]),
    node('StarterPlayer', 'StarterPlayer', None, [node('StarterPlayerScripts', 'StarterPlayerScripts', None, [
        node('TX6_Visuals', 'LocalScript', 'Client/TX6_Visuals.client.luau'),
        node('TX6_SpawnClient', 'LocalScript', 'Client/TX6_SpawnClient.client.luau')])]),
    node('Workspace', 'Workspace', None, [node('TX6_Bastion', 'Model', None, vehicle_children)]),
])
json.dump(sm, open(os.path.join(HERE, 'sourcemap.json'), 'w'), indent=1)
files = []
for root, _, fs in os.walk(os.path.join(HERE, 'src')):
    files += [os.path.relpath(os.path.join(root, f), HERE) for f in fs if f.endswith('.luau')]
cmd = [LSP, 'analyze', '--platform=roblox', '--sourcemap=sourcemap.json', '--definitions=@roblox=' + DEFS] + sorted(files)
r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
out = (r.stdout + r.stderr).strip()
print(out if out else 'no problems found')
print('files checked:', len(files), 'exit', r.returncode)
sys.exit(r.returncode)
