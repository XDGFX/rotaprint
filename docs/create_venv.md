# Create a venv for Python to allow installation of dependencies without affecting the host os!
Both pip and npm are used for Python and JavaScript dependencies respectively.
- Part A will install and setup the Python virtual-environment and dependencies. 
- Part B will install and setup the node virtual-environment and install npm dependencies.

> Instructions are for UNIX based operating systems, as this was used for development

# Part A
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
    source .venv/bin/activate.fish  # Uses fish shell, use Bash or whatever you prefer instead if you want!
```

4. Install required packages
```shell
    pip3 install -r requirements.txt
```

# Part B
1. Tell nodeenv to create a new environment using the existing python venv
```shell
    nodeenv -p
```

2. Validate installation was successful. Output should be a version number e.g. `6.14.4`
```shell
    npm install -g npm
    npm -v
```

3. Install required npm dependencies
```shell
    npm install
```