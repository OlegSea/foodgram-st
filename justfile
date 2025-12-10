alias d := down
alias b := build
alias r := run

build:
    cd infra && docker compose up --build

run:
    cd infra && docker compose up

down:
    cd infra && docker compose down

prune:
    cd infra && docker volume prune
