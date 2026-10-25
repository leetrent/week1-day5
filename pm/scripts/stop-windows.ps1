$ErrorActionPreference = "Stop"

$containerName = "pm-mvp-app"

$existing = docker ps -a --format '{{.Names}}' | Select-String -Pattern "^$containerName$"
if ($LASTEXITCODE -ne 0) {
  throw "Failed to query Docker containers."
}
if ($existing) {
  docker stop $containerName | Out-Null
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to stop container '$containerName'."
  }
  docker rm $containerName | Out-Null
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to remove container '$containerName'."
  }
  Write-Host "Stopped and removed $containerName"
} else {
  Write-Host "Container $containerName was not found"
}
