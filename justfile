alias m := manage
alias cs := collectstatic
alias s := serve
alias t := test
alias sh := shell
alias lc := load-container

default:
    @just --list

[group("django")]
manage *args:
    #!/usr/bin/env bash
    export DIAGNET_DEBUG="${DIAGNET_DEBUG:-True}"
    export DIAGNET_DATA_PATH="${DIAGNET_DATA_PATH:-./data}"
    mkdir -p $DIAGNET_DATA_PATH
    if [ -n "$IN_NIX_SHELL" ]; then
        python manage.py {{args}}
    else
        uv run manage.py {{args}}
    fi

[group("django")]
migrate:
    @just manage makemigrations
    @just manage migrate

[group("django")]
collectstatic *args:
    @just manage collectstatic {{args}}

[group("django")]
serve *args:
    @just manage runserver {{args}}

[group("django")]
test *args:
    @just manage test {{args}}

[group("django")]
shell *args:
    @just manage shell {{args}}

[group("container")]
load-container:
    nix build .#container
    podman load < result

[group("nix")]
update:
    nix flake update
