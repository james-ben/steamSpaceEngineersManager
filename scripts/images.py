# Run GIMP in batch mode:
# https://www.gimp.org/tutorials/Basic_Batch/

"""Manage the thumbnails and other images to be used for workshop content.

Each local workshop directory will have a sub-directory named "img".
This will contain the screenshots to be used as thumbnail and other
 attached images on the workshop page.
The raw image to be used as the thumbnail should be named 'thumb.png'.
This will be converted to the proper size, have a logo added, and overwrite
 existing 'thumb.png' file in the top BP directory.
Any images that should have a logo (and optionally text) added to them
 should end in '-append-logo'.
"""

# Notes:
# JSON file will have details about where the logo should go
# Final image size for thumb.png will be [1280x720] as this should be
#  small enough to fit within the 1MB size limit of the workshop for thumbnails
# Similarly, file size for '-append-logo' files is [1600x900]


import shlex
import pathlib
import configparser
import subprocess as sp

# globals
_this_dir = pathlib.Path(__file__).resolve().parent
_config = configparser.ConfigParser()
_config.read(str(_this_dir.parent / "source" / "config.ini"))
_magick_path = _config['Images']['ImageMagickPath']


class ImageSet:

    default_thumb_type = 'logo-simple'
    default_position = 'lower-right'
    # composite_cmd = 'magick.exe composite \'{mask}[{size}]\' \'{img}[{size}]\' png:{dst}'

    @staticmethod
    def make_composite_cmd(mask_path, mask_size, img_path, img_size, dst_path):
        return [
            'powershell.exe',
            _magick_path,
            'composite',
            shlex.quote('{mask}[{size}]'.format(mask=mask_path, size=mask_size)),
            shlex.quote('{img}[{size}]'.format(img=img_path, size=img_size)),
            shlex.quote('{dst}'.format(dst=dst_path))
        ]

    def get_thumb_info(self, cfg):
        if 'thumb' in cfg:
            thumb_cfg = cfg['thumb']
            for k in thumb_cfg.keys():
                if k.startswith('logo-'):
                    return k, thumb_cfg[k]
        # default
        return self.default_thumb_type, self.default_position

    def __init__(self, dir_path, logo_path, cfg=None):
        """dir_path: path to the BP directory (not 'img').

        logo_path: set in config.ini, should point to dir with png masks.
        """

        self.dir_path = dir_path
        self.thumb_size = '1280x720'
        self.dst_size = '1600x900'
        self.img_path = dir_path / 'img'
        self.logo_path = logo_path
        self.cfg = cfg if cfg is not None else {}
        self.imgs = list(self.img_path.glob('*.png')) if self.img_path.is_dir() else None

    def add_logo(self, img_path, logo_type, logo_pos):
        mask_path = self.logo_path / '{type}-full-{pos}.png'.format(type=logo_type, pos=logo_pos)
        # TODO: have this override original name, saving backup
        img_dst = img_path.parent / '{}_new.png'.format(img_path.stem)

        cmd = self.make_composite_cmd(mask_path, self.dst_size, img_path,
                                      self.dst_size, img_dst)
        proc = sp.Popen(cmd)
        proc.wait()

    def generate_thumbnail(self):
        thumb_src = self.img_path / 'thumb.png'
        if not thumb_src.is_file():
            return None
        thumb_type, thumb_pos = self.get_thumb_info(self.cfg)
        thumb_dst = self.dir_path / 'thumb.png'
        mask_path = self.logo_path / '{type}-thumb-{pos}.png'.format(type=thumb_type, pos=thumb_pos)

        cmd = self.make_composite_cmd(mask_path, self.thumb_size, thumb_src,
                                      self.thumb_size, thumb_dst)
        proc = sp.Popen(cmd)
        proc.wait()

        return None

    def format_images(self):
        # do any of the images match in the cfg dict?
        for k, v in self.cfg.items():
            if k == 'thumb':
                continue
            img_path = self.img_path / '{}.png'.format(k)
            if img_path in self.imgs:
                # apply the formatting
                if 'logo' in v:
                    self.add_logo(img_path, 'logo-complex', v['logo'])
                # elif 'logo-simple' in v:
                #     self.add_logo(img_path, 'logo-simple', v['logo-simple'])
                # TODO: add simple masks for full size
                elif 'text' in v:
                    pass
                # TODO: adding text is more difficult

        return None
