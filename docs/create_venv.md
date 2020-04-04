# Create a venv for Python to allow installation of dependencies without affecting the host os!
Both pip and npm are used for Python and JavaScript dependencies respectively.
- Part A will install and setup the Python virtual-environment and dependencies. 
- Part B will install and setup the node virtual-environment and install npm dependencies.

> Instructions are for UNIX based operating systems, as this was used for development

# Part A
1. Check `pip` and `venv` are installed
```bash
sudo apt-get update
sudo apt-get -y install python3-pip python3-venv
```

2. Create and activate virtual environment in `rota-print` install folder
```bash
# Uses fish shell, use Bash or whatever you prefer instead if you want!
python3 -m venv .venv; source .venv/bin/activate.fish
```

3. Install required packages
```bash
pip3 install -r requirements.txt
```

# Part B
1. Tell nodeenv to create a new environment using the existing python venv, and check install was successful. Output should be a version number e.g. `6.14.4`.
```bash
nodeenv -p; npm install -g npm; npm -v
```

2. Install required npm dependencies
```bash
npm install
```