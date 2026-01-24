{ lib, inputs, ... }:
{
  perSystem =
    {
      config,
      pkgs,
      system,
      ...
    }:
    let
      wsgiApp = "diagnet.asgi:application";
      settingsModules = {
        prod = "diagnet.settings";
      };

      workspace = inputs.uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ../.; };

      overlay = workspace.mkPyprojectOverlay {
        sourcePreference = "wheel";
      };

      editableOverlay = workspace.mkEditablePyprojectOverlay {
        root = "$REPO_ROOT";
      };

      python = pkgs.python313;

      # choose workspace deps: if workspace.deps.default is a per-system attrset, pick the current system,
      # otherwise use it directly.
      deps =
        let
          wd = workspace.deps.default;
        in
        if lib.hasAttr system wd then wd.${system} else wd;

      # Python sets grouped per system
      pythonSet =
        let
          # Base Python package set from pyproject.nix
          baseSet = pkgs.callPackage inputs.pyproject-nix.build.packages {
            inherit python;
          };
        in
        baseSet.overrideScope (
          lib.composeManyExtensions [
            inputs.pyproject-build-systems.overlays.default
            overlay

            (final: prev: {
              # Fix 1: backports-ssl
              backports-ssl = prev.backports-ssl.overrideAttrs (old: {
                nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ final.setuptools ];
                # Remove conflicting namespace file
                postInstall = (old.postInstall or "") + ''
                  rm -f $out/lib/python*/site-packages/backports/__init__.py
                  rm -f $out/lib/python*/site-packages/backports/__init__.pyc
                '';
              });

              # Fix 2: backports-ssl-match-hostname
              backports-ssl-match-hostname = prev.backports-ssl-match-hostname.overrideAttrs (old: {
                nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ final.setuptools ];
                # Remove conflicting namespace file
                postInstall = (old.postInstall or "") + ''
                  rm -f $out/lib/python*/site-packages/backports/__init__.py
                  rm -f $out/lib/python*/site-packages/backports/__init__.pyc
                '';
              });

              # Fix 3: f5-icontrol-rest
              f5-icontrol-rest = prev.f5-icontrol-rest.overrideAttrs (old: {
                nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ final.setuptools ];
              });

              # Fix 4: future
              future = prev.future.overrideAttrs (old: {
                nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ final.setuptools ];
              });

              # Fix 5: ncclient
              ncclient = prev.ncclient.overrideAttrs (old: {
                nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ final.setuptools ];
              });

              # Fix 6: pyftpdlib
              pyftpdlib = prev.pyftpdlib.overrideAttrs (old: {
                nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ final.setuptools ];
              });

              # Fix 7: tftpy
              tftpy = prev.tftpy.overrideAttrs (old: {
                nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ final.setuptools ];
              });

              # Fix 8: py-ubjson
              py-ubjson = prev.py-ubjson.overrideAttrs (old: {
                nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ final.setuptools ];
              });
            })
          ]
        );

      # Django static root (single derivation for this system)
      staticRoot =
        let
          inherit (pkgs) stdenv;

          venv = pythonSet.mkVirtualEnv "diagnet-env" deps;
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
            # 1. Nix requires us to create the output directory explicitly
            mkdir -p $out

            # 2. Set necessary Django variables for the build
            # We use a dummy SECRET_KEY because settings.py often crashes without one,
            # even though we are just collecting static files.
            export DJANGO_SECRET_KEY="build-only-dummy-key"
            export DJANGO_SETTINGS_MODULE="diagnet.settings"

            # 3. Run collectstatic
            # --noinput: Don't ask for confirmation
            # --clear: Clean up old files (good practice)
            env DJANGO_STATIC_ROOT="$out" python manage.py collectstatic --noinput --clear
          '';
        };

    in
    {
      # TODO fix container
      packages = lib.optionalAttrs pkgs.stdenv.isLinux {
        # Expose Docker container in packages
        docker =
          let
            venv = pythonSet.mkVirtualEnv "diagnet-env" deps;
          in
          pkgs.dockerTools.buildLayeredImage {
            name = "diagnet";
            contents = [
              pkgs.dockerTools.fakeNss

              pkgs.cacert
              pkgs.coreutils
              pkgs.bashInteractive
              ../.
            ];
            config = {
              Cmd = [
                "${venv}/bin/daphne"
                "-b"
                "0.0.0.0"
                wsgiApp
              ];
              Env = [
                "DJANGO_SETTINGS_MODULE=${settingsModules.prod}"
                # staticRoot is per-system already
                "DJANGO_STATIC_ROOT=${staticRoot}"

                "DJANGO_SECRET_KEY=production-unsafe-key-change-me"
                "DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0"
              ];
              ExposedPorts = {
                "8000/tcp" = { };
              };
            };
          };
      };

      devShells =
        let
          pythonSet' = pythonSet.overrideScope editableOverlay;

          venv = pythonSet'.mkVirtualEnv "diagnet-dev-env" (
            workspace.deps.all
            // {
              diagnet = [ "dev" ];
            }
          );
        in
        {
          default = pkgs.mkShell {
            packages =
              builtins.attrValues {
                inherit (pkgs)
                  git
                  just
                  neovim
                  uv
                  ;
              }
              ++ [ venv ];
            env = {
              UV_NO_SYNC = "1";
              UV_PYTHON = python.interpreter;
              UV_PYTHON_DOWNLOADS = "never";
            };
            shellHook = ''
              ${config.pre-commit.settings.shellHook}
              unset PYTHONPATH
              export REPO_ROOT=$(git rev-parse --show-toplevel)
            '';
          };
        };
    };
}
