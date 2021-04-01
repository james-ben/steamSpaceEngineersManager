import json
import pathlib

_this_dir = pathlib.Path(__file__).resolve().parent
_links_path = _this_dir / "cfg" / "links.json"


class Page:

    # class/static values
    title_str = """[h1]{t}[/h1]\n\n"""
    setup_str = """[h2]Setup[/h2]\n\n"""
    attr_str = """[list]\n{items}[/list]\n"""

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

        self.title = data['title']
        self.header = data['header']
        self.setup = data['setup']
        self.attribution = data['attribution']

    def formatted_title(self):
        return self.title_str.format(t=self.title)

    def formatted_header(self):
        return '\n'.join(self.header) + '\n\n'

    def formatted_setup(self):
        return self.setup_str + '\n'.join(self.setup) + '\n\n'

    def formatted_attribution(self):
        link_str = ""
        for item in self.attribution:
            if item in self.links:
                link_str += "[*] {}\n".format(self.links[item])
            else:
                link_str += "[*] {}\n".format(item)

        if link_str:
            return self.attr_str.format(items=link_str)
        else:
            return ""

    def format_page(self):
        return self.formatted_title() + \
                self.formatted_header() + \
                self.formatted_setup() + \
                self.formatted_attribution()
