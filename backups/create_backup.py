from pathlib import Path
import datetime, hashlib, json, os, subprocess, zipfile

root=Path.cwd()
backup_dir=root/'backups'
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
archive=backup_dir/f'ESP32_QUIC_Trial_working_{stamp}.zip'

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
metadata['RESTORE.md']=b'''# Restore this working ESP32-C6 project

This is a complete project snapshot, including uncommitted files, Git/submodule
metadata, managed dependency source, configuration, server, certificates, Python
virtual environment, build products, and successful hardware-verification logs.
No project folders were omitted except backups/ itself.

1. Verify the ZIP against the adjacent .sha256 file, then extract it to a NEW
   directory. Do not overwrite a newer project. The project is under
   ESP32_QUIC_Trial/. BACKUP_METADATA/ contains versions, patches and SHA-256s.
2. For the closest reproduction, restore to the original absolute path:
   C:\\Users\\newsh\\Desktop\\ESP32_QUIC_Trial
   after moving any existing project aside. Otherwise regenerate build/ and the
   server virtual environment: generated build files and venv launchers contain
   absolute paths. Preserve the original build folder separately before
   regenerating it if you want to retain firmware and verification evidence.
3. Use ESP-IDF v6.1 at the commit in esp-idf-git-head.txt. The external ESP-IDF
   installation/toolchains are NOT included. Their versions are recorded in
   esp-idf-tools.json and the archived build/CMakeCache.txt. dependencies.lock
   and main/idf_component.yml are included; managed dependency source and both
   Git submodules are already populated, including their local modifications.
   Do not reset/update dependencies over the snapshot. Local patch files are
   documentation of changes ALREADY applied; do not apply them a second time.
4. With ESP-IDF configured, run idf.py build. If using a different path, use a
   fresh build directory, e.g. idf.py -B build-restored build.
5. If recreating the server environment, use its recorded Python version,
   create .quic-venv, and install BACKUP_METADATA/server-requirements-freeze.txt.
   Run .quic-venv\\Scripts\\python.exe quic_server.py. The existing server
   certificate/key are included. The configured endpoint is
   192.168.137.1:14567, ALPN mqtt; laptop networking must supply that address.
6. DHT11: DATA GPIO4, power 3V3, GND. Release COM6 from other monitors, then
   run idf.py -p COM6 flash monitor.

The archived build/quic_runtime_COM6.log and quic_runtime_summary.json record
8 successful sensor publications and matching returned messages, with zero
ESP32 errors in the final 50-second verification capture.

This archive includes local Wi-Fi configuration and the server private key.
'''

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

