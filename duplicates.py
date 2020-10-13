import os
import pathlib
import hashlib
from common import ChangeLog


def hash_file(l, path):
    """
    Compute the hash of a files contents
    Will return a size of -1 in error
    :param l: logger instance
    :param path: a path to a file
    :return: the hash in hexadecimal and the size of the file
    """

    hf = hashlib.sha512()
    size = -1

    if os.path.exists(path):
        try:
            with open(path, 'rb') as fs:
                while True:
                    # read in the recommended amount of bytes
                    # for the given hashing algorithm
                    chunk = fs.read(hf.block_size)

                    # if there are no bytes read,
                    # break, as the file is empty
                    if not chunk:
                        break

                    hf.update(chunk)
                size = fs.tell()
        except IOError as e:
            l.error('failed to read {}: {}'.format(path, str(e)))
    else:
        l.warn('{}: does not exist, skipping'.format(path))

    return hf.hexdigest(), size


def shortest_filename(files: list):
    """
    Determine the shortest file name out of a list of possible names
    :param files: a list of file names
    :return: the shortest filename and all the rest
    """

    possible = {}

    for file in files:
        filename = pathlib.Path(file).stem  # Without extension
        size = len(filename)
        if possible.get(size):
            possible[size].append(file)
        else:
            possible.update({size: [file]})

    shortest = None
    others = []

    for size, possible_files in possible.items():
        sorted_files = sorted(possible_files, key=str.lower)
        if size == min(possible.keys()):
            shortest = sorted_files[0]
        else:
            others.extend(sorted_files)

    return shortest, others


def find_duplicates(l, directory: str, recursive: bool, preprocessed=None):
    """
    Compare and locate duplicate files in a directory
    :param l: logger instance
    :param directory: the directory to search
    :param recursive: True to recursively consider sub-directories
    :param preprocessed: used for recursion; a dictionary of existing hashes
    :return: a dictionary of hashes and file names in form of {<hash>: [<filename>]}
    """

    processed = preprocessed or {}

    if os.path.exists(directory):
        if os.path.isdir(directory):
            try:
                for cd, dirs, files in os.walk(directory):
                    l.info('working in {} ({} files, {} sub directories)'.format(cd, len(files), len(dirs)))

                    for file in files:
                        path = os.path.join(cd, file)
                        hash, size = hash_file(l, path)

                        if size >= 0:
                            l.debug('{}: {}B, hash is {}'.format(path, size, hash[0:16]))

                            if hash in processed.keys():
                                existing_hash = processed[hash]
                                l.debug('{}: duplicate {}'.format(path, len(existing_hash)))
                                existing_hash.append(path)
                            else:
                                processed.update({hash: [path]})
                                l.debug('{}: unique'.format(path))
                        else:
                            l.debug('{}: skipped'.format(path))

                    if recursive:
                        for sub in dirs:
                            processed = find_duplicates(l, sub, recursive, preprocessed=processed)
            except OSError as e:
                l.error('failed to enumerate {}: {}'.format(directory, str(e)))
        else:
            l.error('"{}" is not a directory'.format(directory))
    else:
        l.error('"{}" does not exist'.format(directory))

    return processed


def remove_duplicates(l, cl: ChangeLog, directory: str, dry_run: bool, recursive: bool):
    """
    Find and remove file duplicates
    :param l: logger instance
    :param cl: ChangeLog instance
    :param directory: directory to search
    :param dry_run: True will not apply changes, only log them
    :param recursive: True to recursively consider sub-directories
    """

    if os.path.exists(directory):
        if os.path.isdir(directory):
            # Generate a dictionary of hashes of files
            processed = find_duplicates(l, directory, recursive)

            # Find hashes with more than one file name
            # then remove all but the one with the shortest file name
            for hash, files in processed.items():
                file_count = len(files)
                l.debug('{}: {} files'.format(hash[0:16], file_count))

                if file_count == 1:
                    l.info('{}: no duplicates'.format(files[0]))
                elif file_count > 1:
                    # Determine the shortest file name
                    shortest, others = shortest_filename(files)

                    l.info('{}: {} duplicates found'.format(shortest, file_count))

                    # Remove duplicate files
                    for duplicate in others:
                        l.info('{}: remove duplicate {}'.format(shortest, duplicate))

                        if not dry_run:
                            try:
                                os.remove(duplicate)
                                cl.addChange(__name__, 'remove', True, path=duplicate, original=shortest)
                            except OSError as e:
                                l.error('{}: failed to remove {}: {}'.format(shortest, duplicate, str(e)))
                        else:
                            cl.addChange(__name__, 'remove', False, path=duplicate, original=shortest)
        else:
            l.error('"{}" is not a directory'.format(directory))
    else:
        l.error('"{}" does not exist'.format(directory))
