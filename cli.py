import sys
import argparse
import logging
import time
import datetime
from naming import rename_dir, CAPITALIZED, TITLECASE, LOWERCASE, UPPERCASE
from duplicates import remove_duplicates
from common import ChangeLog

DESCRIPTION = 'fsclean v1.0 by Jacob Jewett'

l = logging.Logger('fsclean')
lh = logging.StreamHandler()
lh.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d]: %(message)s'))
l.addHandler(lh)


def pretty_duration(seconds):
    return str(datetime.timedelta(seconds=seconds))


def monotonic_ms():
    return time.monotonic() * 1000


if __name__ == '__main__':
    l.info(DESCRIPTION)

    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument('--op', '-o', required=True, nargs='+', dest='operations',
                    choices=[
                        'duplicates',
                        'naming'
                    ],
                    help='operations to perform on the target directories.')
    ap.add_argument('--changelog', '-c', nargs='?', dest='changelog_path',
                    default=None, const='changelog.json',
                    help='enable and set path for JSON log of changes made by this program.'
                         'default filename is "changelog.json".')
    ap.add_argument('--dry', '-d', action='store_true', dest='dry_run',
                    help='don\'t actually manipulate files, only log what will happen.')
    ap.add_argument('--recurse', '-r', action='store_true', dest='recursive',
                    help='Recursively enter subdirectories.')
    ap.add_argument('--style', '-s', nargs=1, dest='style', default=None, const=None,
                    choices=[
                        CAPITALIZED,
                        TITLECASE,
                        LOWERCASE,
                        UPPERCASE
                    ],
                    help='specify additional naming rules when using the naming operation.')
    ap.add_argument('--space', '-S', nargs=1, dest='space_char', default=None, const=None,
                    help='replace file name spaces with this character. '
                         'only applies to the naming operation.')
    ap.add_argument('--level', '-l', nargs=1, type=int, dest='log_level', default=[20],
                    help='logging level (10-50). '
                         'default is 20 INFO.')
    ap.add_argument(nargs='+', dest='targets',
                    help='one or more paths to target directories.')
    apr = ap.parse_args(sys.argv[1:])

    l.setLevel(apr.log_level[0])

    operations = apr.operations
    changelog_path = apr.changelog_path
    targets = apr.targets
    dry_run = apr.dry_run
    recursive = apr.recursive
    style = apr.style[0] if apr.style is not None else None
    space_char = apr.space_char[0] if apr.space_char is not None else None

    if dry_run:
        l.info('dry run enabled')

    if recursive:
        l.info('recursive search enabled')

    # prepare a new instance of a ChangeLog to record changes to files
    cl = ChangeLog()

    # record time before starting the operations
    start = datetime.datetime.now()
    stopwatch = monotonic_ms()

    for op in operations:
        if op.lower() == 'duplicates':
            # recursive duplicate search routine.
            l.info('operation: duplicate search mode')

            for target in targets:
                remove_duplicates(l, cl, target, dry_run, recursive)

        if op.lower() == 'naming':
            # filename consistency normalizer routine.
            l.info('operation: filename consistency')

            for target in targets:
                rename_dir(l, cl, target, dry_run, recursive,
                           style=style, space_char=space_char)

    # determine how long it took for all operations
    duration = (monotonic_ms() - stopwatch) / 1000
    # format the duration message
    duration_text = pretty_duration(duration) if duration > 1 else duration

    l.info('{} changes in {}'.format(len(cl.changes), duration_text))

    # add version and statistics to root object of JSON file
    cl.addRootProperties({
        'version': 1,
        'start': start.isoformat(),
        'duration': duration
    })

    # write dictionary to JSON file
    if changelog_path is not None:
        l.info('writing changelog to {}'.format(changelog_path))
        try:
            cl.save(changelog_path, indent=True)
        except IOError as e:
            l.error('could not write changelog to {}: {}'.format(changelog_path, str(e)))
            exit(2)
    else:
        l.error('no changelog')
        exit(3)
else:
    print('This Python file must be ran directly.')
    exit(1)
