SDMTools
====

An integrated toolset for Houdini, and hopefully other 3D packages in the future!

- http://www.sashaouellet.com

Download the **latest version** here (pick the top most one):
https://github.com/sashaouellet/SDMTools/releases


### About

SDMTools is a collection of shelf tools, HDAs, and menu scripts in its Houdini form. I aim to expand this library to other packages in the future.
The toolset is aimed to integrate seamlessly into the existing Houdini tools while providing quality-of-life changes.
My development is driven by the requests of my peers, alongside any features I found useful during my coursework.

My goal is to provide:
- **Ease-of-use**: Self-installation and updates from within Houdini itself. Well designed menus/UIs for user-friendliness
- **Integration**: Small QoL tools/scripts that leverage already existing functionality and fit seamlessly into the UI
- **Strong Python API**: Houdini-specific and general Python API that is well documented

SDMTools is **open source**, licensed under the [MIT license](https://github.com/sashaouellet/SDMTools/blob/master/LICENSE). This tool set is developed by only myself, currently a Visual Effects major at SCAD.


### Tools

- Menu scripts for toolset specific functions (preferences, updates, etc.)
- QoL convenience scripts
- Shelf tools
- Easy-to-use default node color/shape tool
- Workflow-enhancing HDAs


### Automatic Installation (for first time download)

- Download the latest release (see link above)
- Extract and move it anywhere. If working on a network (such as a school) I'd recommend keeping it on a network drive
- Run `python install.py <houdiniVersion>` from the command line after `cd`ing into SDMTools/houdini
- Any release after you install this first time can be automatically downloaded and installed from inside Houdini!

If for some reason the script incorrectly indentifies the location of your houdini.env file, you can run `python install.py <houdiniVersion> --env /path/to/houdini.env` to point it to the right place.

### Manual Installation

The installation process involves two steps: **downloading** and
**setting up the environment**.

#### 1. Download

Download latest release from [here](https://github.com/sashaouellet/SDMTools/releases) (use the top most release on the page). Unzip and place the SDMTools directory anywhere on your computer (or network drive if more convenient).

#### 2. Adding it to the Houdini environment

For Houdini to access all the SDMTools components, you must modify the following environment variables:

- `HOUDINI_PATH`: shelves, startup scripts, HDAs, menu scripts
- `PYTHONPATH`: Supporting Python API required for the toolset to function

See the following example for how your houdini.env should look:

```
HOUDINI_PATH = "/path/to/SDMTools/houdini;&"
PYTHONPATH = "/path/to/SDMTools/python"
```

The "&" at the end of HOUDINI_PATH is very important. Your HOUDINI_PATH variable may already exist (perhaps for an Arnold installation, or something of the sort). In this case, all you have to do is add "/path/to/SDMTools/houdini" to what is already there, separated by a ";" and before the final "&". For example:

```
HOUDINI_PATH = "/some/other/installation/path;/path/to/SDMTools/houdini;&"
```

Please note that the automatic installation described in the first section properly appends to these environment variables for you.

### Documentation

I do my best to document all the tools I develop, and work to make sure that the shelf tools have up-to-date help cards. The Python API that I continue to grow is thoroughly documented as well.

Other information is covered in the [wiki](https://github.com/sashaouellet/SDMTools/wiki), which I will keep updating.

I greatly appreciate bug reports and feature requests, all it takes is a Github account!
[Check out the issue tracker here](https://github.com/sashaouellet/SDMTools/issues?state=open).

#### Thanks for your interest!
##### Sasha Ouellet
