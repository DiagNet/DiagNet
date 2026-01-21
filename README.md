# DiagNet 🌐

Welcome to DiagNet! This is your new go-to platform for making network management a breeze. We designed it to take the headache out of testing, validating, and monitoring your infrastructure.

Instead of spending hours on boring manual checks, DiagNet lets you automate the whole process. Now you can define, run, and visualize your network tests in a way that actually makes sense!

This was built with love as a diploma project at HTL Wien 3 Rennweg, in partnership with our friends at CANCOM Austria AG.

> [!WARNING]
> This project is still a work in progress. **Passwords are currently stored in plaintext.**

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
- **Networking Magic:** [Netmiko](https://github.com/ktbyers/netmiko), [PyATS](https://developer.cisco.com/pyats/)
- **The Toolbox:** [`nix`](https://nixos.org/), [`uv`](https://github.com/astral-sh/uv), [`just`](https://github.com/casey/just)

## 📦 Getting Started

### Prerequisites

First things first, make sure you have these tools installed:

- `just`
- `uv`
- `nix` (Optional, if you like keeping your environment tidy.)

### Let's Run It!

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
