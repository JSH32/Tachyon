from genericpath import isdir
import os
import pathlib
import subprocess
import shutil
import json
import urllib.request
import zipfile
from functools import cache

versions = [
    '1.18.2'
]

print(f'=== Building all modpacks ({len(versions)}) ===')

mmc_path = os.path.join(os.getcwd(), 'MultiMC') # MultiMC path
build_path = os.path.join(os.getcwd(), 'build') # Build path
shutil.rmtree(build_path, ignore_errors=True)
os.makedirs(build_path)

def packwiz_export(version: str, export_type: str, ext: str = 'zip') -> None:
    dir_path = os.path.join(os.getcwd(), version)
    p = subprocess.Popen(['packwiz', export_type, 'export'], cwd=dir_path)
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

for version in versions:
    print(f'Building curseforge ({version})')
    packwiz_export(version, "curseforge")

    print(f'Building modrinth ({version})')
    packwiz_export(version, 'modrinth', 'mrpack')

    print(f'Building MultiMC ({version})')

    # Will be available in each suffixed '.template' file in MultiMC directory
    template_vars = { 'version': version }

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