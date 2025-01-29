# Getting Started 

This guide will walk you through the process of setting up and using the Burgonet Gateway.


## Installation

1. **Download:** Download the appropriate binary for your operating system from the [releases page](https://github.com/burgonet-eu/gateway/releases).
2. **Configuration:** Download the default configuration file [conf.yml](https://raw.githubusercontent.com/burgonet-eu/gateway/refs/heads/main/conf.yml)
3. **Run:** Execute the binary using the following command, replacing `<path/to/conf.yml>` with the actual path to your configuration file:


```bash
./burgonet-gw -c <path/to/conf.yml>
```


## Accessing the Web UI

Once the gateway is running, you can access the administration web UI at:
[http://127.0.0.1:6189/](http://127.0.0.1:6189/)

![Screenshot](images/screenshot.png)


When you have created your token, you can test it via the convenience chat web app embedded, open the following URL in your browser:


[http://127.0.0.1:6190/](http://127.0.0.1:6190/)
configure the the server url (default port is 6191) and your token: 

![Chat Web UI](images/chat-interface.png)

