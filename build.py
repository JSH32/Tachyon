from genericpath import isdir
from functools import cache
import os
import pathlib
import subprocess
import shutil
import json
import urllib.request
import zipfile
import toml

# Versions to build, these must be folders in the root path
versions = [
    '1.18.2',
    '1.19',
    '1.19.2',
    '1.19.4'
]

# MultiMC path
mmc_path = os.path.join(os.getcwd(), 'MultiMC')

# Build path
build_path = os.path.join(os.getcwd(), 'build')

# Recreate the build path
shutil.rmtree(build_path, ignore_errors=True)
os.makedirs(build_path)

def packwiz_export(version: str, export_type: str, ext: str = 'zip') -> None:
    dir_path = os.path.join(os.getcwd(), version)
    p = subprocess.Popen(['../packwiz', export_type, 'export'], cwd=dir_path)
    p.wait()
    # there should only be one archive
    archive = [f for f in os.listdir(dir_path) if f.endswith(f'.{ext}')][0]
    os.rename(
        os.path.join(dir_path, archive),
        os.path.join(build_path, f"{os.path.splitext(archive)[0]}-{export_type}.{ext}")
    )

# Download the latest packwiz bootstrapper from github
@cache
def packwiz_bootstrap() -> bytes:
    req = urllib.request.urlopen('https://api.github.com/repos/packwiz/packwiz-installer-bootstrap/releases/latest')
    bootstrap_url = json.load(req)['assets'][0]['browser_download_url']
    return urllib.request.urlopen(bootstrap_url).read()

print(f'=== Building all modpacks ({len(versions)}) ===')

# Build every version
for version in versions:
    print(f'Building curseforge ({version})')
    packwiz_export(version, 'curseforge')

    print(f'Building modrinth ({version})')
    packwiz_export(version, 'modrinth', 'mrpack')

    print(f'Building MultiMC ({version})')

    with open(f'./{version}/pack.toml', "r") as f:
        pack_config = toml.loads(f.read())

    quilt = 'quilt' in pack_config['versions']
    loader_name = 'Quilt Loader' if quilt else 'Fabric Loader'

    # Will be available in each suffixed '.template' file in MultiMC directory
    template_vars = { 
        'version': version,
        'loader_version': pack_config['versions']['quilt'] if quilt else pack_config['versions']['fabric'],
        'loader_uid': 'org.quiltmc.quilt-loader' if quilt else 'net.fabricmc.fabric-loader',
        'loader_name': loader_name
    }

    # Generate MultiMC auto updating packs
    with zipfile.ZipFile(os.path.join(build_path, f'Tachyon-MultiMC-{version}.zip'), "w") as zipf:
        zipf.writestr('.minecraft/packwiz-installer-bootstrap.jar', packwiz_bootstrap()) # Put bootstrapper
        for sys_path in list(pathlib.Path(mmc_path).glob('**/*')):
            if isdir(sys_path): 
                continue

            sys_path = str(sys_path)

            path = sys_path.removeprefix(mmc_path).strip('/').strip('\\')
            if path.endswith('.template'):
                with open(sys_path) as f:
                    template_str = f.read()
                    for key, value in template_vars.items():
                        template_str = template_str.replace(f"${key}$", value) # Replace all variables in template files

                    zipf.writestr(path.removesuffix('.template'), template_str)
                    print(f"Generated template ({path}) for {version}")
            else:
                zipf.write(sys_path, path)
                print(f"Copied file ({path}) for {version}")