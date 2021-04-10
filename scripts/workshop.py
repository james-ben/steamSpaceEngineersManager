import json
import pathlib
import webbrowser

from scripts.sbc_parser import Blueprint

_this_dir = pathlib.Path(__file__).resolve().parent
_links_path = _this_dir.parent / "cfg" / "links.json"


class Page:

    # class/static values
    title_str = """[h1]{t}[/h1]\n"""
    section_header_str = """[h2]{name}[/h2]"""
    attr_str = """[h2]Attribution[/h2]\n[list]\n{items}[/list]\n"""
    single_content_str = "{name}: {content}\n"
    content_url = "https://steamcommunity.com/sharedfiles/filedetails/?id={id}"
    edit_url = "https://steamcommunity.com/sharedfiles/itemedittext/?id={id}"
    images_url = "https://steamcommunity.com/sharedfiles/managepreviews/?id={id}"
    build_str = """\nThis page was auto generated with [url=https://github.com/james-ben/steamSpaceEngineersManager/tree/main]steamSpaceEngineersManager[/url]\n"""

    def __init__(self, path, blocks_dict=None, comps_dict=None):
        """blocks_dict and comps_dict only used in construction, not stored"""

        load_path = pathlib.Path(path)
        if not load_path.exists():
            raise ValueError("Error, path {} does not exist!".format(load_path))

        with open(path, 'r') as fp:
            data = json.load(fp)

        # load the links for attribution
        with open(_links_path, 'r') as fp:
            self.links = json.load(fp)

        # decode the entries in the json
        if not isinstance(data, dict):
            raise ValueError("data in {} is not a dictionary!".format(load_path))

        # get known common fields
        self.type = data['type']
        self.name = data['name']
        self.id = data['id']
        self.title = data['title']

        # then the rest are optional
        self.sections = data['sections']

        # auto generate some things by parsing the blueprint file
        self.bp = Blueprint(self.name, blocks_dict, comps_dict)
        # components list
        # if (len(self.bp.grids) == 1) and (self.bp.grids[0].get_grid_size() == "Small"):
        if len(self.bp.grids) == 1:
            # could be None if dictionaries didn't exist
            self.grid_comps = self.bp.grids[0].get_grid_components()
        else:
            self.grid_comps = None

    def edit_workshop_page(self):
        webbrowser.open(self.edit_url.format(id=self.id))

    def formatted_title(self):
        return self.title_str.format(t=self.title)

    def formatted_attribution(self, attr_list):
        link_str = ""
        for item in attr_list:
            if item in self.links:
                link_str += "[*] {}\n".format(self.links[item])
            else:
                link_str += "[*] {}\n".format(item)

        if link_str:
            return self.attr_str.format(items=link_str)
        else:
            return ""

    def format_generic_list(self, name, elements):
        line_list = [self.section_header_str.format(name=name),
                     '[list]']
        line_list.extend(['[*] {}'.format(x) for x in elements])
        line_list.append('[/list]')
        line_list.append('')
        return line_list

    def format_normal_section(self, section, content):
        # each section will have a name
        line_list = [self.section_header_str.format(name=section.capitalize()) + '\n']
        # then add all of the content lines
        line_list.extend(content)
        line_list.append('')
        return line_list

    def format_bullet_section(self, section, content):
        return self.format_generic_list(section.split("_")[0].capitalize(), content)

    def format_components_list(self):
        if self.grid_comps is None:
            return []
        else:
            return self.format_generic_list('Components', ['{}: {}'.format(k, v)
                                                           for k, v in self.grid_comps.items()])

    def format_missile_features(self, block_dict):
        if self.bp.grids[0].get_grid_size() == 'Small':
            wh_name = 'SmallWarhead'
        else:
            wh_name = 'LargeWarhead'
        missile_specs = [
            'Blocks: {}'.format(self.bp.get_total_blocks()),
            'PCU: {}'.format(self.bp.get_total_pcu()),
            'Warheads: {}'.format(self.bp.grids[0].blocks[wh_name]),
            'Mass: {} Kg'.format(self.bp.grids[0].get_grid_mass()),
            'Acceleration: {:.3f} (m/s)^2'.format(self.bp.get_acceleration(block_dict, gravity=0))
        ]
        return self.format_generic_list('Missile Features', missile_specs)

    def format_page(self, block_dict):
        line_list = [self.formatted_title()]

        for section, content in self.sections.items():
            # specials
            if section == 'header':
                line_list.extend(content)
                line_list.append('')
            elif section == 'grid_dimension':
                line_list.extend([self.bp.get_largest_grid_dimensions(), ''])
            elif section == "components":
                line_list.extend(self.format_components_list())
            elif section == "missile_specs":
                line_list.extend(self.format_missile_features(block_dict))
            elif section == 'attribution':
                line_list.append(self.formatted_attribution(content))
            # generics
            elif isinstance(content, list):
                if section.endswith("_list"):
                    line_list.extend(self.format_bullet_section(section, content))
                else:
                    line_list.extend(self.format_normal_section(section, content))
            else:
                # some are just single strings: concat name and content together
                line_list.append(self.single_content_str.format(
                    name=section.capitalize(),
                    content=content
                ))

        # last thing, attribution to script
        line_list.append(self.build_str)
        return line_list
