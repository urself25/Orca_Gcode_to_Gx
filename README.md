# Orca_Gcode_to_Gx
Executable Python script converting Gcode to Flashforge Gx for Orcaslicer

## Description
Inspired by many users, I developed a python script converting Orcaslicer Gcode files to Flashforge Gx format.

- It converts the included PNG thumbnails into the appropriate bitmap format.
- Reports the Time to print, bed and nozzle temp, the speed and lenght of filament used.

## How to Install

Download the zip file and extract the included exe file anywhere you want.

In Orcaslicer, go to Process, under the Other Tab, scroll down to the _Post-Processing Script_ box.
In the box, insert "path/to/orca_gcode_to_gx.exe";

Just above, Output filename format, replace gcode for gx.

Save your profile.

Enjoy!

### Compatibility

This was tested on an Adventurer 4 only but it should work on other Flashforge printers. 
Please report any issues.
