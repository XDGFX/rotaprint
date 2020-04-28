# Use grbl-sim to simulate a real Arduino connection, virtually!

1. The file `grbl-1.1h/grbl_sim` allows for running source grbl firmware in Linux (tested with WSL Ubuntu).

2. `grbl-1.1h/simport.sh` will start the server and connect it to a fake serial port, `grbl-1.1h/ttyGRBL`. It will make necessary permissions changes to allow the port to be accessed.

3. It will output step(s.out) and block(s.out) to their respective files, at a delta t of `0.01s` (can be altered in `simport.sh` script)

4. Connect to this port as normal. If `screen` is used on the port, nothing else can connect at the same time! Exit `screen` with `crtl-A` > `k` > `y`.