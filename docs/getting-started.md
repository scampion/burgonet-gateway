# Getting Started with Burgonet Gateway

This guide will walk you through the process of setting up and using the Burgonet Gateway.

## Prerequisites

Before you begin, ensure you have the following:

* A compatible operating system (Linux, macOS, or Windows)
* A text editor or IDE
* [Download the latest release](https://github.com/burgonet-eu/gateway/releases) of the Burgonet Gateway binary.

## Installation

1. **Download:** Download the appropriate binary for your operating system from the releases page.
2. **Configuration:** Create a configuration file (`conf.yml`) based on the example provided in the [Configuration](configuration.md) section.
3. **Run:** Execute the binary using the following command, replacing `<path/to/conf.yml>` with the actual path to your configuration file:

   ```bash
   ./burgonet-gw -c <path/to/conf.yml>
   ```

## Accessing the Web UI

Once the gateway is running, you can access the administration web UI at:

```
http://127.0.0.1:6189/
```

You can also access the chat interface at:

```
http://127.0.0.1:6190/
```

## Next Steps

Explore the other sections of this documentation to learn more about configuring and using the Burgonet Gateway's features.


