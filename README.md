** <u>NOTE</u>: This repository contains an incomplete implementation of a CPU and a compiler and it's up to the students of [FOI](http://foi.unizg.hr) to do their magic and get this beast up and running. **


# SIS-A

*Secure Integrated System v. A*

The incomplete CPU that was discovered on one of the computers in the faculty's basement.

## Getting the source code

This will download and install the discovered Python library 

		$ git clone http://github.com/foi-oss/sis-a
		$ cd sis-a
		$ python setup.py build
		$ sudo python setup.py develop


### Running the CPU

Using advanced reverse engineering techniques we have discovered how to run the CPU:

		$ sis-a -m os.mem

Where `memory.sisa` is the raw image of the memory containing the operating system and userspace programs. (We haven't recovered any.)


### Compiling programs for SIS-A

A specialised compiler for the CPU has also been recovered, although, it's implementation is incomplete, as of now it can compile only some instructions.

		$ sis-ac -s fielen.sisas -o fielen.mem

It's up to you implement the missing functions and send a pull request once you're done.

## Documentation

The documentation files have not been recovered yet. We suspect they were on the wiped out USB stick that the agent has left behind. Send a pull request as soon as you manage to recover the files.