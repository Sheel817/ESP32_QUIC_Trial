# Restore the working quiet checkpoint

The ZIP contains `ESP32_QUIC_Trial/` (the full local project) and
`BACKUP_METADATA/` (restore instructions, dependency versions, Git revisions,
local patches, Python requirements, and a per-file SHA-256 manifest).

Included: quiet firmware and ELF, bootloader, partition table, flash arguments,
server and CSV logging, configuration, populated managed dependencies and Git
submodules with local changes, Git metadata, server virtual environment,
certificates, measurement comparison, and existing logs. Only `backups/` itself
is excluded to avoid recursively archiving earlier backups.

1. Verify the ZIP with `Get-FileHash -Algorithm SHA256 <checkpoint.zip>` and
   compare it with the adjacent `.zip.sha256` file. Extract to a new folder.
2. Restore the extracted `ESP32_QUIC_Trial` to the original location,
   `C:\Users\newsh\Desktop\ESP32_QUIC_Trial`, after moving the current project
   aside if needed. Build products and virtual-environment launchers contain
   absolute paths. For another location, recreate the server environment and
   use a fresh build directory instead of reusing cached build files.
3. Use ESP-IDF v6.1 at the revision in
   `BACKUP_METADATA/esp-idf-git-head.txt` with the recorded tools. The external
   ESP-IDF installation and toolchain are not bundled. Tool versions are in
   `BACKUP_METADATA/esp-idf-tools.json` and `build/CMakeCache.txt`.
4. In an ESP-IDF terminal at the project root, run:

   ```powershell
   idf.py -B build-restored -p COM6 build flash monitor
   ```

   `QUIET_MEASUREMENT` is already 1 in `main/measurement_logging.h`. Release
   COM6 from any other serial monitor before flashing. For the already-built
   snapshot, the original `build/` includes `quic_demo.bin`, bootloader,
   partition table, and `flash_args`; these can also be flashed with esptool.
5. Restore/recreate `.quic-venv` using the Python version in
   `BACKUP_METADATA/server-python-version.txt` and install the packages in
   `BACKUP_METADATA/server-requirements-freeze.txt`. Run:

   ```powershell
   .\.quic-venv\Scripts\python.exe .\quic_server.py
   ```

   The laptop must provide `192.168.137.1`; the server uses UDP 14567 and ALPN
   `mqtt`. DHT11 remains on GPIO4, 3V3, and GND. Each server run prints a new
   CSV path in `logs/`.
6. `dependencies.lock` and populated dependency sources preserve the versions.
   The `.patch` files in the project and metadata describe changes already
   applied in the snapshot: do not apply them again or reset the submodules.

The quiet build passed linking and partition checks. Its comparison results
are in `results/logging_comparison.csv` and the accompanying methodology note.
Older hardware verification logs may describe earlier firmware runs; the user-
supplied comparison is documented separately and is not a new hardware test.

The checkpoint includes local Wi-Fi configuration and the server private key.
