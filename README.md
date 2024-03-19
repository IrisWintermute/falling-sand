# falling-sand [IN DEVELOPMENT]
Grid of cellular automata that updates in real time and draws to terminal.
This project requires a command line interface and Python runtime environment to run.
Ideal CLI is the VSCode integrated terminal. Windows Powershell also works, but may perform poorly at higher framerates.
To install, download fallingsand.py and run from terminal. 
The script does not currently have a programming API so changing the initial configuration requires manipulating the variables defined at the start of main().

When run, the script will clear the terminal, update itself and print its updated condition to the terminal before. 
It will do this each frame until the program is killed.

Each frame, the script executes a series of update functions on each node that comprises the overall grid.
Each function updates the attributes of the passed node according to the node's initial attributes and the attributes of adjacent nodes.

The script defines a number of node 'types', where the type acts as a key to define the node's other attributes, such as density and transition temperatures.
