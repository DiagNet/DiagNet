# DiagNet 🌐

Welcome to DiagNet! This is your new go-to platform for making network management a breeze. We designed it to take the headache out of testing, validating, and monitoring your infrastructure.

Instead of spending hours on boring manual checks, DiagNet lets you automate the whole process. Now you can define, run, and visualize your network tests in a way that actually makes sense!

This was built with love as a diploma project at HTL Wien 3 Rennweg, in partnership with our friends at CANCOM Austria AG.

## 🚀 What It Does

- **Your Control Center:** A slick web dashboard where you can handle all your devices and tests in one place.
- **Organize Your Gear:** Keep track of your inventory and store your credentials safely.
- **Testing on Autopilot:**
  - Use our ready-made templates (like Ping or Routing Table checks) to get started fast.
  - Write your own custom tests using our simple, standardized structure.
  - Group tests together and run them in batches.
- **See the Big Picture:** Compare your current test results with past data. It’s a great way to spot network drift or catch failures before they become a problem!

## 🛠️ Under the Hood

- **The Brains:** [Python](https://www.python.org/), [Django](https://www.djangoproject.com/)
- **Networking Magic:** [PyATS](https://developer.cisco.com/pyats/)
- **The Toolbox:** [`nix`](https://nixos.org/), [`uv`](https://github.com/astral-sh/uv), [`just`](https://github.com/casey/just)

## 📦 Getting Started

DiagNet is distributed as an OCI-compliant container image (Docker/Podman).
Using the container is the **only officially supported way** to run DiagNet in
production, as it guarantees a deterministic environment with all necessary
networking and Python dependencies pre-installed via Nix.

For detailed configuration options, see the [Configuration Guide](docs/configuration.md).

### Prerequisites

First things first, make sure you have one of these installed on your system:

- [Docker](https://docs.docker.com/get-docker/) (with Docker Compose)
- [Podman](https://podman.io/docs/installation) (with podman-compose)

### Let's Run It!

The easiest and most maintainable way to run DiagNet is using Docker Compose. You will pull and run the latest version of DiagNet directly from the GitHub Container Registry (GHCR).

Create a file named `docker-compose.yml` in your preferred directory and add the following configuration:

```yaml
services:
  diagnet:
    container_name: diagnet
    image: ghcr.io/diagnet/diagnet:latest # always uses the latest version
    restart: unless-stopped
    ports:
      - 8000:8000 # host:container
    volumes:
      - ./data:/data:Z # stores database and secrets
    environment:
      # secrets are auto-generated on first run and stored in /data/secrets.env
      - DIAGNET_DATA_PATH=/data
      - DIAGNET_ALLOWED_HOSTS=localhost,127.0.0.1
```

Once you have saved the file, you can start DiagNet:

```bash
docker compose up
```

## 💻 Local Development

If you are looking to contribute to DiagNet, tinker with the code, or run it locally without Docker, here is how you set up the development environment.

### Prerequisites

Make sure you have these tools installed:

- `just`
- `uv`
- `nix` (Optional, if you like keeping your environment tidy.)

### Development Commands

We use a `justfile` to make the common tasks super easy.

1. **Fire up the server:**

   ```bash
   just serve
   ```

   This gets everything installed and running for you.

2. **Update the database:**

   ```bash
   just migrate
   ```

   This handles the heavy lifting of migrations.

3. **Jump into a shell:**

   ```bash
   just shell
   ```

   This opens up a Django shell context for you.

4. **See what else you can do:**

   ```bash
   just --list
   ```

## 👥 Who We Are

- **Karun** - Project Lead (Backend, DevOps)
- **Luka** - Deputy Project Lead (Test Logic/Abstraction, Routing Tests)
- **Benedikt** - Team Member (Config Retrieval, Firewall/Service Config)
- **Danijel** - Team Member (Switching Config/Tests, Visualization, Hardening)

## 📄 The Legal Stuff

This project is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.html).
