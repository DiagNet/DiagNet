alias s := serve
alias sh := shell

default:
    @just --list

serve:
    uv run manage.py runserver

shell:
    uv run manage.py shell
