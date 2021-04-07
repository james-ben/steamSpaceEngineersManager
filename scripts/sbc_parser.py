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


import json
import pathlib
import configparser

import bs4


_config = configparser.ConfigParser()
_this_dir = pathlib.Path(__file__).resolve().parent
_config.read(str(_this_dir.parent / "source" / "config.ini"))


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


def get_block_dict(soup):
    block_dict = {}

    # get the name first
    block_id = soup.find("id")
    try:
        block_name = block_id.find("subtypeid").contents[0]
    except IndexError:
        # just use the typeid, because that means there's only one kind
        block_name = block_id.find('typeid').contents[0]
    # type of block (thruster, battery, etc)
    block_dict['type'] = block_id.find('typeid').contents[0]

    # list of things we care about
    # looks like force is in Newtons and power is in MegaWatts in the game files
    attrs = ['size', 'pcu', 'forcemagnitude', 'maxpowerconsumption', 'maxpoweroutput']
    for a in attrs:
        tag = soup.find(a)
        if tag is not None:
            if tag.contents:
                block_dict[a] = tag.contents[0]
            else:
                block_dict[a] = tag.attrs

    # get components list
    block_components = soup.find("components")
    comp_dict = {}
    for c in block_components.find_all("component"):
        c_list = c.attrs
        if c_list['subtype'] in comp_dict:
            comp_dict[c_list['subtype']] += int(c_list['count'])
        else:
            comp_dict[c_list['subtype']] = int(c_list['count'])
    block_dict['components'] = comp_dict

    return block_name, block_dict


def parse_game_blocks(blocks_dir=None):
    """blocks_dir - file path of game files directory with block information.

    probably
    "C:\\Program Files (x86)\\Steam\\steamapps\\common\\SpaceEngineers\\Content\\Data\\CubeBlocks"
    returns a dictionary that can be sent to JSON.
    """

    game_blocks = {}
    if blocks_dir is None:
        blocks_dir = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\SpaceEngineers\\Content\\Data\\CubeBlocks"

    blocks_files = pathlib.Path(blocks_dir).glob("CubeBlocks_*.sbc")
    for block_file in blocks_files:
        with open(block_file, 'r') as fp:
            soup = bs4.BeautifulSoup(fp, 'lxml')

        for b in soup.find_all("definition"):
            try:
                name, block_dict = get_block_dict(b)
                game_blocks[name] = block_dict
            except IndexError:
                print("Error with file {}".format(block_file))
                raise

    return game_blocks


def get_comp_dict(soup):
    comp_dict = {}

    # get the name first
    block_id = soup.find("id")
    comp_name = block_id.find("subtypeid").contents[0]

    attrs = ['mass', 'volume', 'health']
    for a in attrs:
        tag = soup.find(a)
        if tag is not None:
            if tag.contents:
                comp_dict[a] = tag.contents[0]
            else:
                comp_dict[a] = tag.attrs

    return comp_name, comp_dict


def parse_components(components_file=None):
    """components_files - file path of game file with components information.

    probably
    "C:\\Program Files (x86)\\Steam\\steamapps\\common\\SpaceEngineers\\Content\\Data\\Components.sbc"
    returns a dictionary that can be sent to JSON.
    """

    components = {}
    if components_file is None:
        components_file = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\SpaceEngineers\\Content\\Data\\Components.sbc"

    with open(components_file, 'r') as fp:
        soup = bs4.BeautifulSoup(fp, 'lxml')

    for c in soup.find_all("component"):
        name, comp_dict = get_comp_dict(c)
        components[name] = comp_dict

    return components


def create_json_dicts():
    build_dir = _this_dir.parent / "build"

    # game_blocks = parse_game_blocks()
    # game_blocks_file = build_dir / "game_blocks.json"
    # with open(game_blocks_file, 'w') as jf:
    #     json.dump(game_blocks, jf, indent=2)

    components = parse_components()
    components_file = build_dir / "components.json"
    with open(components_file, 'w') as jf:
        json.dump(components, jf, indent=2)


if __name__ == '__main__':
    create_json_dicts()
