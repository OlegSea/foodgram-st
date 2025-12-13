build:
    cd infra && docker compose -f docker-compose.local.yml up --build

run:
    cd infra && docker compose up

down:
    cd infra && docker compose down && docker compose -f docker-compose.local.yml down

prune:
    docker volume prune
