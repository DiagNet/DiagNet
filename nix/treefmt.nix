{ inputs, ... }:
{
  imports = [
    inputs.treefmt-nix.flakeModule
  ];

  perSystem = {
    treefmt = {
      settings = {
        excludes = [ "**/migrations/*.py" ];
      };

      programs = {
        # nix
        nixfmt.enable = true;
        deadnix.enable = true;
        statix.enable = true;

        # python
        ruff-check.enable = true;
        ruff-format.enable = true;
        djlint.enable = true;

        # web
        prettier = {
          enable = true;
          excludes = [ "**/*.html" ];
        };
      };
    };
  };
}
