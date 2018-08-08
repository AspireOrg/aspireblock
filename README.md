aspireblock
==============

`aspireblock` provides additional services to Aspirewallet beyond those offered in the API provided by `aspire-server`. It features a full-fledged JSON RPC-based API, which services Aspirewallet as well as any 3rd party services which wish to use it. `aspireblock` has an extensible architecture, and developers may write custom plugins for it, which are loaded dynamically and allow them to extend `aspireblock` with new parsing functionality, write gateways to other currencies or services, and much more.

With its set of core-plugins, `aspireblock` provides a more high-level data processing, and an API that layers on top of `aspire-server`’s API. `aspireblock` generates and allows querying of data such as market and price information, trade operations, asset history, and more. It is used extensively by Aspirewallet itself, and is appropriate for use by applications that require additional API-based functionality beyond the scope of what `aspire-server` itself provides.

# Installation

For a simple Docker-based install of the Aspire software stack, see [this guide](http://counterparty.io/docs/federated_node/).

# Manual installation

(Linux only.) First, install `mongodb` and `redis`, and have an instance of `aspiregasd` and [`aspire-server`](https://github.com/AspireOrg/aspire-lib) running.

Then, download and install `aspireblock`:

```
$ git clone https://github.com/AspireOrg/aspireblock.git
$ cd aspireblock
$ sudo pip3 install -r requirements.txt
$ sudo python3 setup.py install
```

Then, launch the daemon via the following command, with the passwords set as appropriate:

```
$ aspireblock --backend-password=rpc --aspire-password=rpc server
```

Further command line options are available via:

* `$ aspireblock --help`
