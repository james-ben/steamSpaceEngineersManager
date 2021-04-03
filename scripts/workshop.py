import json
import pathlib

_this_dir = pathlib.Path(__file__).resolve().parent
_links_path = _this_dir.parent / "cfg" / "links.json"


class Page:

    # class/static values
    title_str = """[h1]{t}[/h1]\n"""
    section_header_str = """[h2]{name}[/h2]\n"""
    attr_str = """[h2]Attribution[/h2]\n\n[list]\n{items}[/list]\n"""
    single_content_str = "{name}: {content}\n"
    content_url = "https://steamcommunity.com/sharedfiles/filedetails/?id={id}"
    edit_url = "https://steamcommunity.com/sharedfiles/itemedittext/?id={id}"
    build_str = """\nThis page was auto generated with [url=https://github.com/james-ben/steamSpaceEngineersManager/tree/main]steamSpaceEngineersManager[/url]\n"""

    def __init__(self, path):
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

    def format_page(self):
        line_list = [self.formatted_title()]

        for section, content in self.sections.items():
            if section == 'header':
                # special
                line_list.extend(content)
                line_list.append('')
            elif section == 'attribution':
                line_list.append(self.formatted_attribution(content))
            elif isinstance(content, list):
                # each section will have a name
                line_list.append(self.section_header_str.format(name=section))
                # then add all of the content lines
                line_list.extend(content)
                line_list.append('\n')
            else:
                # some are just single strings: concat name and content together
                line_list.append(self.single_content_str.format(
                    name=section.capitalize(),
                    content=content
                ))

        # last thing, attribution to script
        line_list.append(self.build_str)
        return line_list
