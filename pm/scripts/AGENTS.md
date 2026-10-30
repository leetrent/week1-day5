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
- Start scripts require a root `.env` file and pass it to Docker using
  `--env-file` so backend environment variables (including OpenRouter config)
  are available in the container.
- Start scripts mount the named volume `pm-data` at `/app/backend/data`, so the
  SQLite database survives container restarts and image rebuilds.
- Stop scripts stop and remove `pm-mvp-app` if it exists. They do not remove
  the `pm-data` volume. To reset all data, run `docker volume rm pm-data`
  while the container is stopped.