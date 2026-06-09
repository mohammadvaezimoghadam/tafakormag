# run-tests.ps1
# Native PowerShell script to run the isolated monorepo test suite on Windows.
# Prevents WSL/bash proxy conflicts by executing Docker commands directly in PowerShell.

# Ensure directories for artifacts exist
New-Item -ItemType Directory -Force -Path "tests/results", "tests/artifacts" | Out-Null

Write-Host "==================================================" -ForegroundColor Green
Write-Host "    Setting Up Isolated Monorepo Test Suite       " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Cleanup function definition
function Cleanup-Environment {
    Write-Host "`n==================================================" -ForegroundColor Yellow
    Write-Host "    Tearing Down Testing Environment...           " -ForegroundColor Yellow
    Write-Host "==================================================" -ForegroundColor Yellow
    docker compose -f docker-compose.test.yml down -v
}

try {
    # 1. Build test-runner, backend, and vue-frontend
    Write-Host "[1/4] Building test services..." -ForegroundColor Green
    docker compose -f docker-compose.test.yml build
    if ($LASTEXITCODE -ne 0) {
        throw "Docker build failed"
    }

    # 2. Spin up postgres, backend, and frontend in background
    Write-Host "`n[2/4] Launching supporting containers in background..." -ForegroundColor Green
    docker compose -f docker-compose.test.yml up -d postgres-test backend vue-frontend
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to launch Docker containers"
    }

    # 3. Wait for all services to pass their health checks
    Write-Host "`n[3/4] Waiting for services to become healthy..." -ForegroundColor Green
    $maxRetries = 30
    $healthy = $false
    for ($i = 1; $i -le $maxRetries; $i++) {
        $dbStatus = (docker inspect --format='{{.State.Health.Status}}' tafakor_postgres_test 2>$null)
        $backendStatus = (docker inspect --format='{{.State.Health.Status}}' tafakor_backend_test 2>$null)
        $frontendStatus = (docker inspect --format='{{.State.Health.Status}}' tafakor_vue_frontend_test 2>$null)

        if ($dbStatus -eq "healthy" -and $backendStatus -eq "healthy" -and $frontendStatus -eq "healthy") {
            Write-Host "All services are healthy and running!" -ForegroundColor Green
            $healthy = $true
            break
        }

        Write-Host "Waiting... DB is [$dbStatus], Backend is [$backendStatus], Frontend is [$frontendStatus] (Attempt $i/$maxRetries)"
        Start-Sleep -Seconds 2
    }

    if (-not $healthy) {
        throw "Services failed to reach healthy state"
    }

    # 4. Run Pytest suite inside the test-runner
    Write-Host "`n[4/4] Executing test runner..." -ForegroundColor Green
    docker compose -f docker-compose.test.yml run --rm test-runner pytest -v --junitxml=/app/tests/results/junit.xml
    $testsExitCode = $LASTEXITCODE

    if ($testsExitCode -eq 0) {
        Write-Host ""
        Write-Host "SUCCESS: Tests passed successfully!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "FAILURE: Tests failed with exit code $testsExitCode. Check tests/results/junit.xml and tests/artifacts/ for failure screenshots." -ForegroundColor Red
    }

    exit $testsExitCode
}
catch {
    Write-Host ""
    Write-Host "An error occurred: $($_)" -ForegroundColor Red
    exit 1
}
finally {
    Cleanup-Environment
}
