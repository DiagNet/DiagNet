# Frequently Asked Questions (FAQ)

## SSH Configuration

### How can I use custom or "insecure" SSH settings for older devices?

If you need to connect to older network devices that require legacy cryptographic algorithms (e.g., `diffie-hellman-group1-sha1` or `ssh-rsa`), you can provide a custom SSH configuration file to the DiagNet container.

1. Create a file named `ssh_config` on your host system with the necessary settings:

   ```ssh
   Host *
       # Example: Enable legacy algorithms
       KexAlgorithms +diffie-hellman-group1-sha1
       HostKeyAlgorithms +ssh-rsa
       PubkeyAcceptedAlgorithms +ssh-rsa
       # Disable strict host key checking if needed
       StrictHostKeyChecking no
       UserKnownHostsFile /dev/null
   ```

2. Mount this file into the container in your `docker-compose.yml`:

   ```yaml
   services:
     diagnet:
       # ...
       volumes:
         - ./data:/data:Z
         - ./ssh_config:/etc/ssh/ssh_config
   ```

## Networking

### How can I allow DiagNet to access services on the host's localhost?

By default, containers are isolated from the host's network. If you want DiagNet to be able to reach services running directly on your host's `localhost` (127.0.0.1), the easiest way is to use "host networking".

Update your `docker-compose.yml` to include `network_mode: host`:

```yaml
services:
  diagnet:
    # ...
    network_mode: host
    # Note: When using host mode, port mapping (ports:) is ignored
    # as the container binds directly to the host's ports.
```

When using `network_mode: host`, `localhost` or `127.0.0.1` inside DiagNet will refer directly to the host machine.
