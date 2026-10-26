$ErrorActionPreference = "Stop"

$imageName = "pm-mvp"
$containerName = "pm-mvp-app"
$port = "8000"
$envFile = Join-Path (Get-Location) ".env"

if (-not (Test-Path $envFile)) {
  throw "Missing .env file in project root. Add OPENROUTER_API_KEY before starting."
}

docker build -t $imageName .
if ($LASTEXITCODE -ne 0) {
  throw "Docker build failed."
}

$existing = docker ps -a --format '{{.Names}}' | Select-String -Pattern "^$containerName$"
if ($LASTEXITCODE -ne 0) {
  throw "Failed to query Docker containers."
}
if ($existing) {
  docker rm -f $containerName | Out-Null
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to remove existing container '$containerName'."
  }
}

docker run -d --name $containerName --env-file $envFile -p "$port`:8000" $imageName | Out-Null
if ($LASTEXITCODE -ne 0) {
  throw "Docker run failed."
}

Write-Host "PM MVP is running at http://localhost:$port"
