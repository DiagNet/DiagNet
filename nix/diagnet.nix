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

      overlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };

      editableOverlay = workspace.mkEditablePyprojectOverlay { root = "$REPO_ROOT"; };

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
          baseSet = pkgs.callPackage inputs.pyproject-nix.build.packages { inherit python; };
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

          nativeBuildInputs = [ venv ];

          installPhase = ''
            mkdir -p $out
            # Provide dummy keys to satisfy settings.py checks without enabling debug mode
            export DIAGNET_SECRET_KEY="django-insecure-fallback-key-for-dev-only"
            export DIAGNET_DEVICE_ENCRYPTION_KEY="8OGs8CTrNq8TltpMA3H-zybxADNlMt8FvdhEDo0QW98="
            env DIAGNET_STATIC_ROOT="$out" python manage.py collectstatic --noinput --clear
          '';
        };

    in
    {
      packages = lib.optionalAttrs pkgs.stdenv.isLinux {
        # Expose container in packages
        container =
          let
            venv = pythonSet.mkVirtualEnv "diagnet-env" deps;
            entrypoint = pkgs.writeShellScriptBin "entrypoint" ''
              set -euo pipefail
              # Default to /data if not set
              export DIAGNET_DATA_PATH="''${DIAGNET_DATA_PATH:-/data}"
              mkdir -p "$DIAGNET_DATA_PATH"

              # Ensure the database directory exists (if using a custom DB path)
              if [ -n "''${DIAGNET_DB_PATH:-}" ]; then
                mkdir -p "$(dirname "$DIAGNET_DB_PATH")"
              fi

              # Generate secrets
              SECRETS_FILE="$DIAGNET_DATA_PATH/secrets.env"

              if [ -f "$SECRETS_FILE" ]; then
                echo "Loading secrets from $SECRETS_FILE"
                set -a
                source "$SECRETS_FILE"
                set +a
              fi

              # Generate missing secrets in a subshell with strict umask
              (
                umask 077
                if [ -z "''${DIAGNET_SECRET_KEY:-}" ]; then
                  echo "Generating new DIAGNET_SECRET_KEY..."
                  NEW_SECRET=$(${venv}/bin/python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
                  echo "DIAGNET_SECRET_KEY='$NEW_SECRET'" >> "$SECRETS_FILE"
                  export DIAGNET_SECRET_KEY="$NEW_SECRET"
                fi

                if [ -z "''${DIAGNET_DEVICE_ENCRYPTION_KEY:-}" ]; then
                  echo "Generating new DIAGNET_DEVICE_ENCRYPTION_KEY..."
                  NEW_KEY=$(${venv}/bin/python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')
                  echo "DIAGNET_DEVICE_ENCRYPTION_KEY='$NEW_KEY'" >> "$SECRETS_FILE"
                  export DIAGNET_DEVICE_ENCRYPTION_KEY="$NEW_KEY"
                fi
              )

              # Re-source in case we generated new ones (to export them to current shell)
              if [ -f "$SECRETS_FILE" ]; then
                 set -a
                 source "$SECRETS_FILE"
                 set +a
              fi

              # Run migrations (exit if they fail)
              if ! ${venv}/bin/python /manage.py migrate --noinput; then
                echo "Database migrations failed; aborting startup." >&2
                exit 1
              fi

              # Start the application
              exec ${venv}/bin/daphne -b 0.0.0.0 ${wsgiApp}
            '';
          in
          pkgs.dockerTools.buildLayeredImage {
            name = "diagnet";
            tag = "latest";
            contents = [
              pkgs.dockerTools.fakeNss

              pkgs.cacert
              pkgs.coreutils
              pkgs.bashInteractive
              entrypoint
              ../.
            ];
            config = {
              Cmd = [ "${entrypoint}/bin/entrypoint" ];
              WorkingDir = "/";
              Env = [
                "DIAGNET_SETTINGS_MODULE=${settingsModules.prod}"
                # staticRoot is per-system already
                "DIAGNET_STATIC_ROOT=${staticRoot}"

                "DIAGNET_ALLOWED_HOSTS=localhost,127.0.0.1"
                "DIAGNET_DATA_PATH=/data"
                "DIAGNET_DEBUG=False"
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

          venv = pythonSet'.mkVirtualEnv "diagnet-dev-env" (workspace.deps.all // { diagnet = [ "dev" ]; });
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
              VIRTUAL_ENV = "${venv}";
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
