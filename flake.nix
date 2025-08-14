{
  description = "Flake using uv2nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    systems.url = "github:nix-systems/default-linux";

    git-hooks-nix = {
      url = "github:cachix/git-hooks.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs = {
        pyproject-nix.follows = "pyproject-nix";
        nixpkgs.follows = "nixpkgs";
      };
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs = {
        pyproject-nix.follows = "pyproject-nix";
        uv2nix.follows = "uv2nix";
        nixpkgs.follows = "nixpkgs";
      };
    };
  };

  outputs =
    { nixpkgs, ... }@inputs:
    let
      inherit (nixpkgs) lib;

      forEachSystem = f: lib.genAttrs (import inputs.systems) (system: f pkgsFor.${system});
      pkgsFor = lib.genAttrs (import inputs.systems) (
        system:
        import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        }
      );

      wsgiApp = "diagnet.wsgi:application";
      settingsModules = {
        prod = "diagnet.settings";
      };

      workspace = inputs.uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

      overlay = workspace.mkPyprojectOverlay {
        sourcePreference = "wheel";
      };

      editableOverlay = workspace.mkEditablePyprojectOverlay {
        root = "$REPO_ROOT";
      };

      pythonSets = forEachSystem (
        pkgs:
        let
          python = pkgs.python313;

          # Base Python package set from pyproject.nix
          baseSet = pkgs.callPackage inputs.pyproject-nix.build.packages {
            inherit python;
          };

          # An overlay of build fixups & test additions
          pyprojectOverrides = _final: prev: {

            # diagnet is the name of our example package
            diagnet = prev.diagnet.overrideAttrs (old: {

              # Add tests to passthru.tests
              #
              # These attribute are used in Flake checks.
              inherit (old) passthru;
            });

          };
        in
        baseSet.overrideScope (
          lib.composeManyExtensions [
            inputs.pyproject-build-systems.overlays.default
            overlay
            pyprojectOverrides
          ]
        )
      );

      # Django static roots grouped per system
      staticRoots = forEachSystem (
        pkgs:
        let
          inherit (pkgs) stdenv;

          pythonSet = pythonSets.${pkgs.system};

          venv = pythonSet.mkVirtualEnv "diagnet-env" workspace.deps.default;
        in
        stdenv.mkDerivation {
          name = "diagnet-static";
          inherit (pythonSet.diagnet) src;

          dontConfigure = true;
          dontBuild = true;

          nativeBuildInputs = [
            venv
          ];

          installPhase = ''
            env DJANGO_STATIC_ROOT="$out" python manage.py collectstatic
          '';
        }
      );
    in
    {
      formatter = forEachSystem (pkgs: pkgs.nixfmt-tree);

      packages = forEachSystem (
        pkgs:
        let
          pythonSet = pythonSets.${pkgs.system};
        in
        lib.optionalAttrs pkgs.stdenv.isLinux {
          # Expose Docker container in packages
          docker =
            let
              venv = pythonSet.mkVirtualEnv "diagnet-env" workspace.deps.default;
            in
            pkgs.dockerTools.buildLayeredImage {
              name = "diagnet";
              contents = [ pkgs.cacert ];
              config = {
                Cmd = [
                  "${venv}/bin/gunicorn"
                  wsgiApp
                ];
                Env = [
                  "DJANGO_SETTINGS_MODULE=${settingsModules.prod}"
                  "DJANGO_STATIC_ROOT=${staticRoots.${pkgs.system}}"
                ];
              };
            };
        }
      );

      # Use an editable Python set for development.
      devShells = forEachSystem (
        pkgs:
        let
          python = pkgs.python313;

          editablePythonSet = pythonSets.${pkgs.system}.overrideScope (
            lib.composeManyExtensions [
              editableOverlay

              (final: prev: {
                diagnet = prev.diagnet.overrideAttrs (old: {
                  src = lib.fileset.toSource {
                    root = old.src;
                    fileset = lib.fileset.unions [
                      (old.src + "/pyproject.toml")
                      (old.src + "/README.md")
                      (old.src + "/diagnet/__init__.py")
                    ];
                  };
                  nativeBuildInputs =
                    old.nativeBuildInputs
                    ++ final.resolveBuildSystem {
                      editables = [ ];
                    };
                });
              })
            ]
          );

          venv = editablePythonSet.mkVirtualEnv "diagnet-dev-env" {
            diagnet = [ "dev" ];
          };
        in
        {
          default = pkgs.mkShell {
            packages = [
              venv
              pkgs.uv
            ];
            env = {
              UV_NO_SYNC = "1";
              UV_PYTHON = python.interpreter;
              UV_PYTHON_DOWNLOADS = "never";
            };
            shellHook = ''
              unset PYTHONPATH
              export REPO_ROOT=$(git rev-parse --show-toplevel)
            '';
          };
        }
      );
    };
}
