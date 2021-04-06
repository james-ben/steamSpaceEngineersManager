# steamSpaceEngineersManager
Auto generate body of Steam workshop content pages


## Description

I created this project to help me keep my Steam workshop content up to date.
Any time a file is out of date, it will be rebuilt automatically.

The implementation is decent, but there is certainly room for improvement.  Feel free to suggest revisions.

This is built for Windows.  If you can get Space Engineers to work on Linux, then you should have no problem porting this to work with Linux.  It would really only be a few file operations functions.


## Under Construction

TODO:

* Open up browser to workshop page each time a file is regenerated
* Copy the new text to the clipboard
* Give the user the path to the pictures that go with the file if those are out of date
* Automatically put the logo on the thumb nail
* links to the components of the blueprint (subgrids or assemblies) or grids it's used in
* the list of components required to build the ordnance
* the features of the ships
  * dimensions
  * acceleration


## Details

### cfg

* links.json - contains attributions to other items on the workshop
