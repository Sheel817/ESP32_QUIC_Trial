from pathlib import Path
import datetime, hashlib, json, os, subprocess, zipfile

root=Path.cwd()
backup_dir=root/'backups'
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
archive=backup_dir/f'ESP32_QUIC_Trial_quiet_checkpoint_{stamp}.zip'

def command(args,cwd=root):
    if args[0] == 'git' and str(cwd).replace(chr(92), '/') == 'C:/esp/v6.1/esp-idf':
        args = ['git', '-c', 'safe.directory=C:/esp/v6.1/esp-idf'] + args[1:]
    result=subprocess.run(args,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError(f'{args}: {result.stderr.decode(errors="replace")}')
    return result.stdout

metadata={}
metadata['git-status.txt']=command(['git','status','--short'])
metadata['git-head.txt']=command(['git','rev-parse','HEAD'])
metadata['project-local-changes.patch']=command(['git','diff','--binary','HEAD'])
metadata['submodule-versions.txt']=command(['git','submodule','status','--recursive'])
for label,relative in [('ngtcp2','components/ngtcp2/ngtcp2'),('coreMQTT','components/coreMQTT/coreMQTT')]:
    folder=root/relative
    metadata[f'{label}-head.txt']=command(['git','rev-parse','HEAD'],folder)
    metadata[f'{label}-local-changes.patch']=command(['git','diff','--binary','HEAD'],folder)
    metadata[f'{label}-status.txt']=command(['git','status','--short'],folder)
for label,python in [('server',root/'.quic-venv/Scripts/python.exe'),('esp-idf',Path('C:/Espressif/tools/python/v6.1/venv/Scripts/python.exe'))]:
    metadata[f'{label}-requirements-freeze.txt']=command([str(python),'-m','pip','freeze','--all'])
    metadata[f'{label}-python-version.txt']=command([str(python),'--version'])
metadata['esp-idf-git-head.txt']=command(['git','rev-parse','HEAD'],Path('C:/esp/v6.1/esp-idf'))
metadata['esp-idf-git-describe.txt']=command(['git','describe','--always','--dirty','--tags'],Path('C:/esp/v6.1/esp-idf'))
metadata['esp-idf-tools.json']=Path('C:/esp/v6.1/esp-idf/tools/tools.json').read_bytes()
metadata['RESTORE.md']=(backup_dir/'RESTORE_QUIET_CHECKPOINT.md').read_bytes()
firmware=root/'build/quic_demo.bin'
metadata['quiet-firmware.json']=json.dumps({
    'mode':'quiet',
    'quiet_switch':'main/measurement_logging.h: QUIET_MEASUREMENT=1',
    'firmware_path':'ESP32_QUIC_Trial/build/quic_demo.bin',
    'bytes':firmware.stat().st_size,
    'sha256':hashlib.sha256(firmware.read_bytes()).hexdigest(),
    'build_log':'ESP32_QUIC_Trial/build/quiet_measurement_build_retry.log',
    'comparison':'ESP32_QUIC_Trial/results/logging_comparison.csv',
},indent=2).encode()

manifest=[]
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
    for base,dirs,files in os.walk(root):
        dirs.sort()
        if Path(base)==root:
            dirs[:]=[d for d in dirs if d!='backups']
        for filename in sorted(files):
            path=Path(base)/filename
            relative=path.relative_to(root).as_posix()
            data=path.read_bytes()
            entry=f'ESP32_QUIC_Trial/{relative}'
            z.writestr(entry,data)
            manifest.append({'path':entry,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    for name,data in metadata.items():
        entry='BACKUP_METADATA/'+name
        z.writestr(entry,data)
        manifest.append({'path':entry,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    z.writestr('BACKUP_METADATA/manifest.json',json.dumps({'created_utc':stamp,'original_root':str(root),'files':manifest},indent=2))

with zipfile.ZipFile(archive) as z:
    for item in manifest:
        data=z.read(item['path'])
        if len(data)!=item['bytes'] or hashlib.sha256(data).hexdigest()!=item['sha256']:
            raise RuntimeError('Backup verification failed: '+item['path'])
archive_hash=hashlib.sha256(archive.read_bytes()).hexdigest()
checksum=archive.with_suffix('.zip.sha256')
checksum.write_text(f'{archive_hash}  {archive.name}\n')
print(json.dumps({'archive':str(archive),'sha256_file':str(checksum),'verified_files':len(manifest),'archive_bytes':archive.stat().st_size,'sha256':archive_hash},indent=2))

