# To interact with the Steam Web API
# https://partner.steamgames.com/doc/webapi_overview

# It looks like Steam doesn't have an API for changing workshop content,
#  at least not using the Web API, and I don't want to write a client for this,
#  this is just supposed to be a script that can run.
# Instead, I will create a `make`-like system that will build the text body
#  for each workshop item, and inform me of ones that need to be updated.
# It will also keep track of the photo timestamps if any of those need to be
#  updated as well.

import pathlib

from workshop import Page


# globals
_this_dir = pathlib.Path(__file__).resolve().parent


def build_page_source(src, build_dir):
    # create a new one
    new_page = Page(src)
    new_page_str = new_page.format_page()

    # load the old one
    old_build_name = src.name.split(".")[0] + ".txt"
    old_build_path = build_dir / old_build_name

    write_new = True
    if old_build_path.exists():
        with open(old_build_path, 'r') as old_fp:
            old_page = old_fp.readlines()
        old_page_str = ''.join(old_page)
        if old_page_str == new_page_str:
            write_new = False

    # write out new version
    if write_new:
        with open(old_build_path, 'w') as new_fp:
            new_fp.write(new_page_str)

    return write_new


def main():
    # make sure build directory exists
    build_dir = _this_dir / "build"
    if not build_dir.exists():
        build_dir.mkdir()

    # get list of inputs from source dir
    source_dir = _this_dir / "page_source"
    src_list = source_dir.glob("*.json")

    for src in src_list:
        if build_page_source(src, build_dir):
            print("Rebuilt {}".format(src))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
