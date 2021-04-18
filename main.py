# To interact with the Steam Web API
# https://partner.steamgames.com/doc/webapi_overview

# It looks like Steam doesn't have an API for changing workshop content,
#  at least not using the Web API, and I don't want to write a client for this,
#  this is just supposed to be a script that can run.
# Instead, I will create a `make`-like system that will build the text body
#  for each workshop item, and inform me of ones that need to be updated.
# It will also keep track of the photo timestamps if any of those need to be
#  updated as well.

# Create temporary file using tempfile,
#  compare with existing build file of same name with filecmp,
#  copy over to new place if needed using shutil
#  remove temp file using https://stackoverflow.com/a/9155528/12940429

import os
import json
import shutil
import filecmp
import pathlib
import tempfile
import subprocess as sp

from scripts import sbc_parser
from scripts.workshop import Page


# globals
_this_dir = pathlib.Path(__file__).resolve().parent


def build_page_source(src_path, build_dir, blocks_dict, comps_dict):
    """Returns Page object if rewrote the file, None otherwise."""

    # create a new one
    new_page = Page(src_path, blocks_dict, comps_dict)
    new_page_lines = new_page.format_page(blocks_dict)
    tmp_file = tempfile.NamedTemporaryFile(mode='w+t', delete=False)
    for line in new_page_lines:
        tmp_file.write(line + '\n')
    tmp_file.close()

    # compare with the old one
    old_build_name = src_path.name.split(".")[0] + ".txt"
    old_build_path = build_dir / old_build_name
    new_build_name = tmp_file.name

    if old_build_path.exists() and filecmp.cmp(old_build_path, new_build_name, shallow=False):
        # they are the same, just cleanup and exit
        os.remove(new_build_name)
        return None
    else:
        # they are different, overwrite the old with new temp file
        shutil.copy(new_build_name, old_build_path)
        os.remove(new_build_name)
        # open in notepad
        # startfile has no way of knowing when it returns
        # os.startfile(old_build_path)
        if new_page.edit_workshop_page():
            proc = sp.Popen(['notepad.exe', str(old_build_path)])
            proc.wait()
        return new_page


def prepare_images(page):
    page.format_images()


def prepare_thumbnails(page):
    page.format_thumbnail()


def main():
    # make sure build directory exists
    build_dir = _this_dir / "build"
    if not build_dir.exists():
        build_dir.mkdir()

    # get list of inputs from source dir
    source_dir = _this_dir / "source" / "pages"
    src_list = source_dir.glob("*.json")

    # load the information about blocks and components
    blocks_file = build_dir / "game_blocks.json"
    comps_file = build_dir / "components.json"
    # make sure exists
    if (not blocks_file.exists()) or (not comps_file.exists()):
        sbc_parser.create_json_dicts()
    with open(blocks_file, 'r') as jf:
        blocks_dict = json.load(jf)
    with open(comps_file, 'r') as jf:
        comps_dict = json.load(jf)

    # now go generate all of the output files
    for src in src_list:
        page = build_page_source(src, build_dir, blocks_dict, comps_dict)
        if page is not None:
            print("Rebuilt {}".format(src))
            prepare_thumbnails(page)
            prepare_images(page)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
