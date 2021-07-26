# neuro3d
Blender framework for visualization of neurons and simulation data.

# Installation

Make sure that `python` and `blender` are valid commands. Most likely you have to make them available on your PATH.

## Linux

```
curl -Ls https://github.com/Helveg/neuro3d/releases/latest/download/install | python
```

## Windows

Execute the following snippet from the command line or PowerShell:

```
powershell.exe -command PowerShell -ExecutionPolicy Bypass -noprofile -command Invoke-WebRequest -Uri https://github.com/Helveg/neuro3d/releases/latest/download/install -OutFile _tmp_n3d_install.py; Invoke-Expression "python _tmp_n3d_install.py"; Remove-Item -Path "_tmp_n3d_install.py"
```
