# Scripts notes

This folder contains Docker start/stop scripts for each target OS.

## Current scripts

- `start-mac.sh`
- `stop-mac.sh`
- `start-linux.sh`
- `stop-linux.sh`
- `start-windows.ps1`
- `stop-windows.ps1`

## Behavior

- Start scripts build the Docker image (`pm-mvp`) and run container
  (`pm-mvp-app`) on port `8000`.
- Stop scripts stop and remove `pm-mvp-app` if it exists.