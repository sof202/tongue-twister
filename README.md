# Tongue Twister

This is a python program that will display tongue twisters on a GUI. The catch
is that the program will play your voice back at you with a user specified
delay (best results at 50-200ms delay). 

## Windows

I use WSL1 for programming currently, as such these files were generated on
WSL1, but are unfortunately for windows based systems. This is so that audio
drivers and other system level calls work (GUI elements).

## Install

Go through the painful experience of installing conda on a windows machine,
no I won't tell you how. Then create a new conda environment with:

```powershell
cd ...\tongue-twister\envs\
conda env create --file .\environment.yaml
```

## Running

Run the powershell script in the root of this repository:

```bash
# From WSL
powershell.exe .../run.ps1
```

```powershell
# From Powershell
& .../run.ps1
```
