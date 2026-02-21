alias m := manage
alias s := serve
alias sh := shell

default:
    @just --list

[group("django")]
manage *args:
    #!/usr/bin/env bash
    export DIAGNET_DEBUG="True"
    if [ -n "$IN_NIX_SHELL" ]; then
        python manage.py {{args}}
    else
        uv run manage.py {{args}}
    fi

[group("django")]
serve:
    @just manage runserver

[group("django")]
test:
    @just manage test

[group("django")]
shell:
    @just manage shell

[group("django")]
migrate:
    @just manage makemigrations
    @just manage migrate

[group("nix")]
update:
    nix flake update
