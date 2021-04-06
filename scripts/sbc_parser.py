"""It should be possible to parse the XML files that define a blueprint and determine number
 and type of components required to build the blueprint.
It may also be possible to determine the dimensions and weight from the XML.
These numbers can be used in calculations and auto-populate parts of the content page.

The blueprint files in question are in
C:\\Users\\Username\\AppData\\Roaming\\SpaceEngineers\\Blueprints\\local\\blueprintname\\bp.sbc
The path to this directory should be listed in config.ini, and the name of the blueprint
 directory should be in the JSON for each item.

Important note:
all tags are converted to lowercase by BeautifulSoup!
"""


import pathlib
import configparser

import bs4


_config = configparser.ConfigParser()
_this_dir = pathlib.Path(__file__).resolve().parent
_config.read(str(_this_dir.parent / "source" / "config.ini"))


class Block:

    def __init__(self, soup):
        # don't save unless debugging, takes up too much memory
        # self.soup = soup
        # name of a block type is "subtypename"
        self.name = soup.find("subtypename").contents[0]
        # maybe use "entityid" to look up blocks
        # self.id   = int(soup.find("entityid").contents[0])
        # location of block relative to grid
        self.loc  = soup.find("min").attrs


class Grid:

    def __init__(self, soup):
        self.soup = soup
        # "gridsizeenum" is "Small" or "Large"
        self.size = soup.find("gridsizeenum")
        # block groups are enumerated by coordinates?
        # grid name is "displayname"
        self.name = soup.find("displayname").contents[0]
        # can determine the size of the grid using "localcoordsys" and finding min and max x,y,z
        self.localcoordsys = int(soup.find("localcoordsys").contents[0])

        # self.blocks = [Block(b) for b in soup.find("myobjectbuilder_cubeblock")]
        def get_block_type(block):
            return block.find("subtypename").contents[0]

        def get_block_loc(block):
            return {d: int(v) for d, v in block.find("min").attrs.items()}

        self.blocks = {}
        mins = {d: self.localcoordsys for d in ['x', 'y', 'z']}
        maxs = {d: self.localcoordsys for d in ['x', 'y', 'z']}

        # parse the blocks
        for b in soup.find_all("myobjectbuilder_cubeblock"):
            if isinstance(b, bs4.element.Tag):
                b_type = get_block_type(b)
                b_loc = get_block_loc(b)
                if b_type in self.blocks:
                    self.blocks[b_type] += 1
                else:
                    self.blocks[b_type] = 1
                # track size
                mins = {k[0]: min(k[1], v) for k, v in zip(mins.items(), b_loc.values())}
                maxs = {k[0]: max(k[1], v) for k, v in zip(maxs.items(), b_loc.values())}

        # absolute distance between 2 values
        self.dimensions = {mi[0]: abs(mi[1]-mx[1]) for mi, mx in zip(mins.items(), maxs.items())}

    def get_grid_size(self):
        if isinstance(self.size, bs4.element.Tag):
            return self.size.contents[0]
        else:
            return "Unknown"

    def get_grid_dimension(self):
        return "{}x{}x{}".format(*sorted(self.dimensions.values()))


class Blueprint:

    def __init__(self, name):
        """name - the name of the directory that contains the blueprint"""
        self.name = name
        # load the .sbc file
        sbc_file = pathlib.Path(_config['General']['BlueprintPath']) / name / "bp.sbc"
        with open(sbc_file, 'r') as fp:
            self.soup = bs4.BeautifulSoup(fp, 'lxml')

        self.grids = [Grid(g) for g in self.soup.find_all("cubegrid")]


def unit_test():
    bp = Blueprint("TRN Ion Missile Mk5 SG [V]")


if __name__ == '__main__':
    unit_test()
