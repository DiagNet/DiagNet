alias m := manage
alias s := serve
alias sh := shell

default:
    @just --list

[group("django")]
manage *args:
    uv run manage.py {{args}}

[group("django")]
serve:
    @just manage runserver

[group("django")]
shell:
    @just manage shell

[group("nix")]
update:
    nix flake update
