# VENV

__Use a virtual environment__ (if you are developing python)

## Getting Setup

First install virtualenv:
```bash
$ pip install virtualenv
```

Then set it up for your project, run the following at the top of the repository's 
directory tree.
```bash
$ python -m virtualenv venv -p python3.10
```
Make sure you run this command with your intended version of python.

##### Activate the Environment
Do this before working on the project each time. You can set some IDEs to do this for you.

To activate the environment on windows, run:
```powershell
$ venv\Scripts\activate.bat
```

To activate in PowerShell run:
```powershell
venv\Scripts\activate.ps1
```

In Linux bash run:
```sh
source venv/Scripts/activate
```

## Installing Packages

You can install the packages using the requirements file:
```sh
pip install -r requirements.txt
```

If you have added additional required packages, run `pip freeze > requirements.txt` to 
update the list. 

