import os
import filecmp
import logging
from common import ChangeLog
from collections import defaultdict


LOG = logging.getLogger('fsclean.duplicates')


def shortest_filenames(files: list):
    """
    Determine the shortest filenames out of a list of possible names.
    :param files: a list of file names
    :return: the shortest filenames and all the rest minus the shortest
    """

    possible = defaultdict(list)

    for file in files:
        possible[len(file)].append(file)

    min_length = min(possible.keys())
    shortest = possible[min_length]
    others = []

    for k, v in possible.items():
        if k != min_length:
            others.extend(v)

    return shortest, others


def get_most_recent_file(files):
    mod_map = defaultdict(str)

    for file in files:
        mod_time = os.path.getmtime(file)
        # does not handle if two files have the exact same mod time
        mod_map[mod_time] = file

    return mod_map[max(mod_map.keys())]


def list_except_one(l: list, o: object):
    index = l.index(o)
    return l[:index] + l[index + 1:]


def find_duplicates(directory: str,
                    recursive: bool):
    """
    Locate duplicate files starting at `directory`.

    :param directory: the folder to search
    :param recursive: True to recursively consider sub-directories
    :return: a map of file paths to other duplicates
    """
    file_map = defaultdict(list)

    try:
        for cd, dirs, files in os.walk(directory, followlinks=False):
            files = [os.path.join(cd, f) for f in files]
            for file in files:
                size = os.stat(file).st_size

                if size > 0:
                    pool = list_except_one(files, file)
                    for other_file in pool:
                        if other_file in file_map.keys():
                            continue

                        other_size = os.stat(other_file).st_size

                        if other_size == size:
                            LOG.debug(f'content comparison on "{file}" <-> '
                                      f'"{other_file}"')
                            # cmp() includes comparison caching
                            if filecmp.cmp(file, other_file):
                                file_map[file].append(other_file)

            if not recursive:
                break
    except OSError as e:
        LOG.error(
            'failed to search "{}": {}'.format(directory, str(e)))

    return file_map


def remove_duplicates(cl: ChangeLog,
                      directory: str,
                      dry_run: bool,
                      recursive: bool):
    """
    Find and remove file duplicates
    :param cl: ChangeLog instance
    :param directory: directory to search
    :param dry_run: True will not apply changes, only log them
    :param recursive: True to recursively consider sub-directories
    """
    bytes_freed = 0

    # Generate a dictionary of duplicate files
    file_map = find_duplicates(directory,
                               recursive)

    # Remove all files but the one with the shortest file name
    for path, duplicates in file_map.items():
        # Determine the shortest file name
        shortest, others = shortest_filenames((duplicates + [path]))
        chosen_name = shortest[0] if len(shortest) == 1 else \
            get_most_recent_file(shortest)

        LOG.info('"{}": {} duplicates found'.format(chosen_name,
                                                    len(others)))

        # Remove duplicate files
        for duplicate in others:
            LOG.info('"{}": remove duplicate "{}"'.format(chosen_name,
                                                          duplicate))

            if not dry_run:
                try:
                    bytes_freed += os.stat(duplicate).st_size
                    if os.path.exists(duplicate):
                        os.remove(duplicate)
                        cl.addChange(__name__,
                                     True,
                                     path=duplicate,
                                     original=chosen_name)
                    else:
                        LOG.error(f'"{chosen_name}": duplicate does not exist')
                        cl.addChange(__name__,
                                     False,
                                     path=duplicate,
                                     original=chosen_name,
                                     message='duplicate does not exist')
                except OSError as e:
                    LOG.error(f'"{chosen_name}": failed to remove '
                              f'"{duplicate}": {str(e)}')
                    cl.addChange(__name__,
                                 False,
                                 path=duplicate,
                                 original=chosen_name,
                                 message=str(e),
                                 errno=e.errno)
            else:
                cl.addChange(__name__,
                             False,
                             path=duplicate,
                             original=chosen_name)
    return bytes_freed
