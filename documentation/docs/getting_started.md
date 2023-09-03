# Getting Started with Kademlia DHT Project

Welcome to the Getting Started guide for the Kademlia Distributed Hash Table (DHT) project! If you're new to the project, this is the best place to start. Here, we'll walk you through the installation process, initial setup, and basic usage.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Project](#running-the-project)
- [Additional Commands](#additional-commands)

## Prerequisites

Before diving into the setup, ensure you have the following software installed on your computer:

- Python 3.11
- Poetry

## Installation

### Clone the Repository

First, clone the project repository to your local machine.

```bash
git clone https://gitlab.lrz.de/netintum/teaching/p2psec_projects_2023/DHT-8.git
```

### Navigate to the Project Directory

Once cloned, navigate into the project's root directory.

```bash
cd DHT-8
```

### Install Dependencies

Next, install the necessary Python packages.

```bash
poetry install
```

To activate the project's virtual environment, run:

```bash
poetry shell
```

Note: Remember to activate the project's virtual environment using `poetry shell` in every new shell window you open.

## Running the Project

To launch the Kademlia bootstrap node on localhost, run the following command:

```bash
python3 main.py -a 127.0.0.1 -p 6501
```

To launch the Kademlia node and connect to a bootstrap node, run the following command:

```bash
python3 main.py -a 127.0.0.1 -p 6502 --bootstrap
```

This should initialize your node and you'll see output indicating it's running and connected to the network.

## Additional Commands

Here are some more commands you might find useful:

### Running Tests

To execute all the unit tests, be in the ```DHT-8/``` directory and run:

```bash
pytest test/
```

### Running Specific Tests

To run individual test files, use a command similar to the one below. For instance, this example assumes that a node is listening on port 6501. The following command sends a GET request to the API address (port 7501) of the node running on that port:


```bash
python3 dht_client_test.py -a 127.0.0.1 -p 7501 -c -g
```

The command below will send a PUT request to the same node:

```bash
python3 dht_client_test.py -a 127.0.0.1 -p 7501 -c -s
```

## Next Steps

To learn more about what you can do, head over to the [Features](features.md) section.