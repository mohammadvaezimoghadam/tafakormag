#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Make sure we are in the script directory
cd "$(dirname "$0")"

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Ensure directories for artifacts exist on the host
mkdir -p tests/results tests/artifacts

echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}    Setting Up Isolated Monorepo Test Suite       ${NC}"
echo -e "${GREEN}==================================================${NC}"

# Define the clean up trap to run on EXIT (success, failure, or interrupt)
cleanup() {
    echo -e "\n${YELLOW}==================================================${NC}"
    echo -e "${YELLOW}    Tearing Down Testing Environment...           ${NC}"
    echo -e "${YELLOW}==================================================${NC}"
    # Forceful cleanup, removing containers, networks, and anonymous volumes (-v)
    docker compose -f docker-compose.test.yml down -v
}
trap cleanup EXIT

# 1. Build test-runner, backend, and vue-frontend
echo -e "${GREEN}[1/4] Building test services...${NC}"
docker compose -f docker-compose.test.yml build

# 2. Spin up postgres, backend, and frontend in background
echo -e "\n${GREEN}[2/4] Launching supporting containers in background...${NC}"
docker compose -f docker-compose.test.yml up -d postgres-test backend vue-frontend

# 3. Wait for all services to pass their health checks
echo -e "\n${GREEN}[3/4] Waiting for services to become healthy...${NC}"
MAX_RETRIES=30
for ((i=1; i<=MAX_RETRIES; i++)); do
    DB_STATUS=$(docker inspect --format='{{.State.Health.Status}}' tafakor_postgres_test 2>/dev/null || echo "starting")
    BACKEND_STATUS=$(docker inspect --format='{{.State.Health.Status}}' tafakor_backend_test 2>/dev/null || echo "starting")
    FRONTEND_STATUS=$(docker inspect --format='{{.State.Health.Status}}' tafakor_vue_frontend_test 2>/dev/null || echo "starting")

    if [ "$DB_STATUS" = "healthy" ] && [ "$BACKEND_STATUS" = "healthy" ] && [ "$FRONTEND_STATUS" = "healthy" ]; then
        echo -e "${GREEN}All services are healthy and running!${NC}"
        break
    fi

    if [ "$i" -eq "$MAX_RETRIES" ]; then
        echo -e "${RED}Error: Services failed to reach healthy state. Exiting.${NC}"
        echo -e "Status: Database=$DB_STATUS, Backend=$BACKEND_STATUS, Frontend=$FRONTEND_STATUS"
        exit 1
    fi

    echo -e "Waiting... DB is [${YELLOW}$DB_STATUS${NC}], Backend is [${YELLOW}$BACKEND_STATUS${NC}], Frontend is [${YELLOW}$FRONTEND_STATUS${NC}] (Attempt $i/$MAX_RETRIES)"
    sleep 2
done

# Disable exit-on-error so we can capture the test runner's exit code
set +e

# 4. Run Pytest suite inside the test-runner
echo -e "\n${GREEN}[4/4] Executing test runner...${NC}"
docker compose -f docker-compose.test.yml run --rm test-runner pytest -v --junitxml=/app/tests/results/junit.xml

# Capture test execution exit code
TESTS_EXIT_CODE=$?

if [ $TESTS_EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✔ Tests passed successfully!${NC}"
else
    echo -e "\n${RED}✘ Tests failed with exit code $TESTS_EXIT_CODE. Check tests/results/junit.xml and tests/artifacts/ for failure screenshots.${NC}"
fi

# Exit with the test execution exit code (this will trigger the trap clean up)
exit $TESTS_EXIT_CODE
