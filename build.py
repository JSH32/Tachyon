import os
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

mmc_path = os.path.join(os.getcwd(), 'MultiMC')
build_path = os.path.join(os.getcwd(), 'build')
shutil.rmtree(build_path, ignore_errors=True)
os.makedirs(build_path)

def packwiz_export(version, export_type, ext = 'zip'):
    dir_path = cwd=os.path.join(os.getcwd(), version)
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
    mmc_version = os.path.join(mmc_path, version)
    zip_location = os.path.join(build_path, f'Tachyon-MultiMC-{version}')
    shutil.make_archive(zip_location, 'zip', mmc_version)
    with zipfile.ZipFile(zip_location + '.zip', 'a') as zipf:
        zipf.writestr(".minecraft/packwiz-installer-bootstrap.jar", packwiz_bootstrap())
