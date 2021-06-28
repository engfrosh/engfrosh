# Contributing

### Branches
Work off of the relevant development branch and commit to that.

You are encouraged to create your own branches, please name them as `[your name]/[branch name]`.

## Python Style

Try and keep line length to a maximum of 90 characters and don't go over 120. 
Add rulers at these distances if you find it helps, VSCode settings to add:
```json
"editor.rulers": [90,120],
```

For setting a formatter, use _autopep8_. You will have to install it, although VSCode 
should prompt you with how to do this. You should also adjust your formatter arguments 
with the following settings (formatted for VSCode settings):
```json
"python.formatting.autopep8Args": [
        "--max-line-length",
        "120",
        "--experimental",
        "--ignore",
        "E402"
    ],
```
Make sure to run the formatter before you commit.

### Linting
When working in python, run linting on your code before you commit (or at least before you 
want to pull it into the development branch).

I recommend using _flake8_, as this is what I use, and will tend to be what I'm checking 
your code with. Instructions for using _flake8_ with VSCode can be found 
[here](https://code.visualstudio.com/docs/python/linting) and you can find out how to use
it with other IDEs with a quick search. 

These are the additional arguments to pass to _flake8_ to make it a little nicer (formatted)
for VSCode settings file.
```json
"python.linting.flake8Args": ["--max-line-length=120",],
```
I use autosave and have linting done on save, which is very handy as it will point out
your errors right away, but do what works best for you. 

Try and fix any errors or warnings before you commit, and if you leave an error, add a 
comment on why it is ignored. 

## Getting Started

If you are working with Django you will need to get that installed.

If you are working with Python you will need a version installed (3.9) and then use the
virtual environment to install the packages. 

