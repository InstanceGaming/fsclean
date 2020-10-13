import os
import pathlib
from common import ChangeLog

CAPITALIZED = 'capitalized'
TITLECASE = 'titlecase'
LOWERCASE = 'lowercase'
UPPERCASE = 'uppercase'

STRIPPING_CHARS = " _-"


def check_filename(l, filename: str, style=None, space_char=None):
    """
    Parse a given filename for these consistency errors:
    - Extraneous spaces
    - Uppercase extension names
    - Stripping beginning and end of STRIPPING_CHARS
    - Spaces directly before or after a "."
    - Optionally enforce naming conventions
    :param l: logger instance
    :param filename: input filename
    :param style: enforce a particular naming style (CAPITALIZED, TITLECASE, LOWERCASE, UPPERCASE)
    :param space_char: replace spaces in a file name with this character
    :return: a corrected filename
    """
    pl_obj = pathlib.Path(filename)
    name = pl_obj.stem
    ext = pl_obj.suffix

    if name != '':
        name_stripped = name.strip(STRIPPING_CHARS)

        if name_stripped != name:
            l.debug('{}: needed stripping'.format(filename))

        name_spaces = ' '.join(name_stripped.split())

        if name_spaces != name_stripped:
            l.debug('{}: had extraneous spaces'.format(filename))

        name = name_spaces

        if style is not None:
            if style == CAPITALIZED:
                name_style = name.capitalize()
            elif style == TITLECASE:
                name_style = name.title()
            elif style == LOWERCASE:
                name_style = name.lower()
            elif style == UPPERCASE:
                name_style = name.upper()
            else:
                name_style = name

            if name_style != name:
                l.debug('{}: naming style enforced'.format(filename))

            name = name_style

        if space_char is not None:
            name_replaced = name.replace(' ', space_char)

            if name_replaced != name:
                l.debug('{}: spaces replaced with "{}"'.format(filename, space_char))

            name = name_replaced

    ext_spaces = ext.replace(' ', '')

    if ext_spaces != ext:
        l.debug('{}: extension spaces removed'.format(filename))

    ext_lowering = ext_spaces.lower()

    if ext_lowering != ext_spaces:
        l.debug('{}: extension converted to lowercase'.format(filename))

    return name + ext_lowering


def check_files(l, files: list, style=None, space_char=None):
    """
    Generate a dictionary of files to be renamed and the new name
    :param l: logger instance
    :param files: a list of file paths to check
    :param style: enforce a particular naming style (CAPITALIZED, TITLECASE, LOWERCASE, UPPERCASE)
    :param space_char: replace spaces in a file name with this character
    :return: A dictionary in form of {<path>: <new name>}
    """
    renamed = {}

    for file in files:
        new_name = check_filename(l, file, style=style, space_char=space_char)

        if new_name != file:
            renamed.update({file: new_name})
            l.debug('{}: to be renamed to "{}"'.format(file, new_name))
        else:
            l.debug('{}: no change'.format(file))

    return renamed


def rename_files(l, cl: ChangeLog, directory: str, files: list, dry_run: bool,
                 style=None, space_char=None):
    """
    Check file names for inconsistency and rename
    :param l: logger instance
    :param cl: ChangeLog instance
    :param directory: directory the files are contained in
    :param files: a list of file names
    :param dry_run: True will not apply changes, only log them
    :param style: enforce a particular naming style (CAPITALIZED, TITLECASE, LOWERCASE, UPPERCASE)
    :param space_char: replace spaces in a file name with this character
    """

    changes = check_files(l, files, style=style, space_char=space_char)

    # iterate and apply changes
    for of, nf in changes.items():
        path = os.path.join(directory, of)
        dest = os.path.join(directory, nf)
        l.info('{}: rename "{}"'.format(path, nf))

        if not dry_run:
            try:
                os.rename(path, dest)
                cl.addChange(__name__, 'rename', True, src=path, dest=dest)
            except OSError as e:
                l.error('failed to rename {}: {}'.format(path, str(e)))
        else:
            cl.addChange(__name__, 'rename', False, src=path, dest=dest)


def rename_dir(l, cl: ChangeLog, directory: str, dry_run: bool, recursive: bool,
               style=None, space_char=None):
    """
    Check files in a directory for naming inconsistency and rename
    :param l: logger instance
    :param cl: ChangeLog instance
    :param directory: directory that the files are contained in
    :param dry_run: True will not apply changes, only log them
    :param recursive: True to recursively enter sub-directories
    :param style: enforce a particular naming style (CAPITALIZED, TITLECASE, LOWERCASE, UPPERCASE)
    :param space_char: replace spaces in a file name with this character
    """

    if os.path.exists(directory):
        if os.path.isdir(directory):
            try:
                for cd, dirs, files in os.walk(directory):
                    l.info('working in {} ({} files, {} sub directories)'.format(cd, len(files), len(dirs)))

                    rename_files(l, cl, cd, files, dry_run, style=style, space_char=space_char)

                    if recursive:
                        # check each sub-directory
                        for sub in dirs:
                            rename_dir(l, cl, sub, dry_run, recursive)
            except OSError as e:
                l.error('failed to enumerate {}: {}'.format(directory, str(e)))
        else:
            l.error('"{}" is not a directory'.format(directory))
    else:
        l.error('"{}" does not exist'.format(directory))
