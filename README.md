
[KubaNotes](https://github.com/Mateusz-Grzelinski/kuba-notes) is small addon that adds note taking abilities to Blender

![addon image](images\addon.png)

## Features 

- open link: type any text and open in preferred application: www link will open web, path will open file explorer

## Installation

1. Download this addon as `.zip` (or clone git repo to `%APPDATA%\Blender Foundation\Blender\3.0\scripts\addons`)
2. Go to <kbd><kbd>Edit</kbd>|<kbd>Preferences</kbd></kbd>. On the <kbd>Add-ons</kbd> tab, choose <kbd>Install</kbd> and select the downloaded `.zip` file.
3. Tick the box beside the add-on name.

## Roadmap

Tested on Blender 3.0, but older versions should work fine.

Please use [Issues](https://github.com/Mateusz-Grzelinski/kuba-notes/issues) for new requests.

- [ ] add description field
  - [ ] show on hoover description by default (if missing show partial link)
- [ ] show "Go to" button on object hover
  - [x] basic implmentation
- [ ] ctrl click to add new text object 
  - [ ] if object is selected make an arrow that points to text
- [ ] Add arrows quickly 
  - [x] proof of concept done - operator `object.addarrow`
  - [ ] import node tree only once per blend file (or just use link?)
  - [ ] make use of selected and active items: add arrows from each selected to active object 
  - [ ] quickly add routing points from object mode
  - [ ] manage style (settings) of multiple arrows at once
  - [ ] style presets
  - [ ] automatically scale arrow (driver?) but allow for adding more offset manually
  - [ ] point to a group of objects 
  - [ ] point to image as plane with correct scale (image is an empty object)
  - [ ] lock arrow to a side of object (similar to draw.io). Propertly track object boundaries.
- [x] Open file explorer (quickly as button)