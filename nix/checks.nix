{
  inputs,
  pkgs,
  ...
}: {
  pre-commit-check = inputs.git-hooks-nix.lib.${pkgs.system}.run {
    src = ../.;
    hooks = {
      # nix
      alejandra.enable = true;
      deadnix.enable = true;
      nil.enable = true;
      statix.enable = true;

      # markdown
      markdownlint = {
        enable = true;
        settings.configuration = {
          line-length.tables = false;
          no-inline-html = false;
        };
      };

      # python
      check-python.enable = true;
      ruff.enable = true;
      ruff-format.enable = true;
    };
  };
}
