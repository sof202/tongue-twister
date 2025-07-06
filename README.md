# Tongue Twister

This is a python program that will display tongue twisters on a GUI. The catch
is that the program will play your voice back at you with a user specified
delay (best results at 50-200ms delay). 

## Windows

I use WSL1 for programming currently, as such these files were generated on
WSL1, but are unfortunately for windows based systems. This is so that audio
drivers and other system level calls work (GUI elements).

## Install

Install conda on your windows machine and run the following in powershell:

```powershell
cd ...\tongue-twister
conda env create --file envs\environment.yaml
pip install -e .
```

## Running

You need to input the correct input/output audio devices for this to work,
for my laptop, most of the audio devices don't actually do anything, so I can't
really come up with a nice way to automate grabbing these. Instead you are
encouraged to run the program with the `--detect` flag. This will output
all available input/output audio devices for the system. You can run this via
the provided powershell script (or just calling `cli.py` manually if in
powershell already):

```bash
# From WSL
powershell.exe "& .../run.ps1"  --detect
```

```powershell
# From Powershell
& .../run.ps1 --detect
```

### Running for real

Once you have the input and output audio devices at the ready, you can provide
these to the powershell script via `-i` and `-o` (input and output
respectively):

```bash
# From WSL
powershell.exe "& .../run.ps1"  -i 1 -o 2
```

```powershell
# From Powershell
& .../run.ps1 -i 1 -o 2
```
