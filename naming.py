import os
import logging
import pathlib
import re

from common import ChangeLog


CAPITALIZED = 'capitalized'
TITLECASE = 'titlecase'
LOWERCASE = 'lowercase'
UPPERCASE = 'uppercase'

ADJACENT_PERIOD_PATTERN = re.compile(r'([^A-Z\d)\]])?\.([^A-Z\d(\[])?',
                                     flags=re.IGNORECASE)

STYLE_NAMES = [
    CAPITALIZED,
    TITLECASE,
    LOWERCASE,
    UPPERCASE
]

STRIPPING_CHARS = " _-"
LOG = logging.getLogger('fsclean.naming')


def check_filename(filename: str, style=None, space_char=None):
    """
    Parse a given filename for these consistency errors:
    - Extraneous spaces
    - Uppercase extension names
    - Stripping beginning and end of STRIPPING_CHARS
    - Anything but alphanumerics before or after "."
    - Optionally enforce naming conventions
    :param filename: input filename
    :param style: enforce a particular naming style
    (CAPITALIZED, TITLECASE, LOWERCASE, UPPERCASE)
    :param space_char: replace spaces in a file name with this character
    :return: a corrected filename
    """
    pl_obj = pathlib.Path(filename)
    name = pl_obj.stem
    ext = pl_obj.suffix

    if name != '':
        name_stripped = name.strip(STRIPPING_CHARS)

        if name_stripped != name:
            LOG.debug('"{}": needed stripping'.format(filename))

        name_spaces = ' '.join(name_stripped.split())

        if name_spaces != name_stripped:
            LOG.debug('"{}": had extraneous spaces'.format(filename))

        name = name_spaces

        if style is not None:
            if style == CAPITALIZED:
                name_styled = name.capitalize()
            elif style == TITLECASE:
                name_styled = name.title()
            elif style == LOWERCASE:
                name_styled = name.lower()
            elif style == UPPERCASE:
                name_styled = name.upper()
            else:
                name_styled = name

            if name_styled != name:
                LOG.debug('"{}": naming style enforced'.format(filename))

            name = name_styled

        if space_char is not None:
            name_replaced = name.replace(' ', space_char)

            if name_replaced != name:
                LOG.debug('"{}": spaces replaced with "{}"'.format(filename,
                                                                   space_char))

            name = name_replaced

    ext_spaces = ext.replace(' ', '')

    if ext_spaces != ext:
        LOG.debug('"{}": extension spaces removed'.format(filename))

    ext_lowering = ext_spaces.lower()

    if ext_lowering != ext_spaces:
        LOG.debug('"{}": extension converted to lowercase'.format(filename))

    first_stage = name + ext_lowering
    adjacent_other = ADJACENT_PERIOD_PATTERN.sub('.', first_stage)

    if adjacent_other != first_stage:
        pattern_text = ADJACENT_PERIOD_PATTERN.pattern
        LOG.debug(f'"{filename}": removed chars adjacent to period matching '
                  f'"{pattern_text}"')

    second_stage = adjacent_other
    return second_stage


def check_files(files: list, style=None, space_char=None):
    """
    Generate a dictionary of files to be renamed and the new name
    :param files: a list of file paths to check
    :param style: enforce a particular naming style
    (CAPITALIZED, TITLECASE, LOWERCASE, UPPERCASE)
    :param space_char: replace spaces in a file name with this character
    :return: A dictionary in form of {<path>: <new name>}
    """
    renamed = {}

    for file in files:
        new_name = check_filename(file, style=style, space_char=space_char)

        if new_name != file:
            renamed.update({file: new_name})
            LOG.debug('"{}": to be renamed "{}"'.format(file, new_name))
        else:
            LOG.debug('"{}": no change'.format(file))

    return renamed


def rename_files(cl: ChangeLog, directory: str, files: list, dry_run: bool,
                 style=None, space_char=None):
    """
    Check file names for inconsistency and rename
    :param cl: ChangeLog instance
    :param directory: directory the files are contained in
    :param files: a list of file names
    :param dry_run: True will not apply changes, only log them
    :param style: enforce a particular naming style
    (CAPITALIZED, TITLECASE, LOWERCASE, UPPERCASE)
    :param space_char: replace spaces in a file name with this character
    """

    changes = check_files(files, style=style, space_char=space_char)

    # iterate and apply changes
    for of, nf in changes.items():
        path = os.path.join(directory, of)
        dest = os.path.join(directory, nf)
        LOG.info('"{}": rename "{}"'.format(path, nf))

        if not dry_run:
            try:
                if not os.path.exists(dest):
                    os.rename(path, dest)
                    cl.addChange(__name__, True, src=path, dest=dest)
                else:
                    LOG.warning('"{}": destination already exists'.format(path))
                    cl.addChange(__name__,
                                 False,
                                 src=path,
                                 dest=dest,
                                 message='destination already exists')
            except OSError as e:
                LOG.error('failed to rename "{}": {}'.format(path, str(e)))
                cl.addChange(__name__,
                             False,
                             src=path,
                             dest=dest,
                             message=str(e),
                             errno=e.errno)
        else:
            cl.addChange(__name__, False, src=path, dest=dest)


def rename_dir(cl: ChangeLog, directory: str, dry_run: bool, recursive: bool,
               style=None, space_char=None):
    """
    Check files in a directory for naming inconsistency and rename
    :param cl: ChangeLog instance
    :param directory: directory that the files are contained in
    :param dry_run: True will not apply changes, only log them
    :param recursive: True to recursively enter sub-directories
    :param style: enforce a particular naming style
    (CAPITALIZED, TITLECASE, LOWERCASE, UPPERCASE)
    :param space_char: replace spaces in a file name with this character
    """

    try:
        for cd, dirs, files in os.walk(directory, followlinks=False):
            LOG.info(f'working in "{cd}" ({len(files)} files, '
                     f'{len(dirs)} sub directories)')

            rename_files(cl,
                         cd,
                         files,
                         dry_run,
                         style=style,
                         space_char=space_char)

            if recursive:
                # check each sub-directory
                for sub in dirs:
                    rename_dir(cl, sub, dry_run, recursive)
    except OSError as e:
        LOG.error('failed to enumerate "{}": {}'.format(directory,
                                                        str(e)))
