# Create a venv for Python to allow installation of dependencies without affecting the host os!
> Instructions are for UNIX based operating systems, as this was used for development

1. Check `pip` and `venv` are installed
```shell
    sudo apt-get update
    sudo apt-get -y install python3-pip
    sudo apt-get install python3-venv
```

2. Create virtual environment in `rota-print` install folder
```shell
    python3 -m venv .venv
```

3. Activate virtual environment
```shell
    source .venv/bin/activate.fish  # Uses fish shell
```

4. Install required packages
```shell
    pip3 install -r requirements.txt
```
