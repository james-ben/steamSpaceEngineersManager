# Run GIMP in batch mode:
# https://www.gimp.org/tutorials/Basic_Batch/

"""Manage the thumbnails and other images to be used for workshop content.

Each local workshop directory will have a sub-directory named "img".
This will contain the screenshots to be used as thumbnail and other
 attached images on the workshop page.
The raw image to be used as the thumbnail should be named 'thumb.png'.
If thumb.png does not exist, then the JSON will indicate which image is
 supposed to be used as the thumbnail, by tagging it with "thumb" attribute.
This will be converted to the proper size, have a logo added, and overwrite
 existing 'thumb.png' file in the top BP directory.
Any images that should have a logo and/or text added to them will have the
 necessary options defined in the JSON.
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

    @staticmethod
    def make_text_cmd(text, img_path, img_size, dst_path):
        return [
            'powershell.exe',
            _magick_path,
            'convert',
            '-background',
            shlex.quote('#00000080'),       # alpha channel, mostly transparent
            '-fill',
            'white',
            '-size',
            '700x60',
            '-pointsize',
            '48',
            '-geometry',
            '+900+50',
            'caption:"{txt}"'.format(txt=text),
            shlex.quote('{img}[{size}]'.format(img=img_path, size=img_size)),
            '+swap',
            '-composite',
            shlex.quote(str(dst_path))
        ]

    @staticmethod
    def make_resize_cmd(img_path, img_size):
        return [
            'powershell.exe',
            _magick_path,
            'convert',
            shlex.quote(str(img_path)),
            '-resize',
            img_size,
            shlex.quote(str(img_path))
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
        return proc.returncode

    def add_text(self, img_path, text_cfg):
        # self.make_text_cmd(grid_name, ...)
        img_dst = img_path.parent / '{}_new.png'.format(img_path.stem)
        # might have already been created, keep adding to new image
        if img_dst.is_file():
            img_path = img_dst
        cmd = self.make_text_cmd(text_cfg['content'], img_path, self.dst_size, img_dst)

        proc = sp.Popen(cmd)
        proc.wait()
        return proc.returncode

    def resize_image(self, img_path):
        cmd = self.make_resize_cmd(img_path, self.dst_size)
        proc = sp.Popen(cmd)
        proc.wait()
        return proc.returncode

    def generate_thumbnail(self):
        thumb_src = self.img_path / 'thumb.png'
        if thumb_src.is_file():
            # found one, get info
            thumb_type, thumb_pos = self.get_thumb_info(self.cfg)
        else:
            # nothing named thumb, maybe reuse other image
            thumb_src = None
            thumb_pos = self.default_position
            # find one that has the attribute
            for k, v in self.cfg.items():
                if 'thumb' in v:
                    thumb_src = self.img_path / '{}.png'.format(k)
                    thumb_pos = v['thumb']
            if thumb_src is None:
                # couldn't find one at all
                return None
            thumb_type = self.default_thumb_type

        thumb_dst = self.dir_path / 'thumb.png'
        mask_path = self.logo_path / '{type}-thumb-{pos}.png'.format(type=thumb_type, pos=thumb_pos)

        cmd = self.make_composite_cmd(mask_path, self.thumb_size, thumb_src,
                                      self.thumb_size, thumb_dst)
        proc = sp.Popen(cmd)
        proc.wait()
        return proc.returncode

    def format_images(self):
        if self.imgs is None:
            return None
        # look at all of the files and make sure they're the right size
        for img in self.imgs:
            # is there a config for it?
            img_basename = img.stem
            if img_basename == 'thumb':
                continue
            if img_basename in self.cfg:
                img_cfg = self.cfg[img_basename]
                # apply the formatting
                if 'logo' in img_cfg:
                    self.add_logo(img, 'logo-complex', img_cfg['logo'])
                if 'text' in img_cfg:
                    self.add_text(img, img_cfg['text'])
            else:
                # if not, just make sure it's the right size (less than 2MB)
                if img.stat().st_size > 2000000:
                    self.resize_image(img)

        return None

# TODO: move the images to a separate dir, instead of inside the BP dir,
#  so they don't get deleted when updating the BP
