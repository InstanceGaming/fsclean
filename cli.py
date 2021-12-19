import os
import sys
import time
import logging
import argparse
import datetime
from common import ChangeLog
from naming import STYLE_NAMES, rename_dir
from empties import remove_empty
from duplicates import remove_duplicates


DESCRIPTION = 'fsclean v1.1 by Jacob Jewett'

DEV_FORMATTER = logging.Formatter('[{asctime}] {levelname:>8}: {message} '
                                  '[{name}@{lineno}]',
                                  datefmt='%x %H:%M:%S',
                                  style='{')
FORMATTER = logging.Formatter('[{asctime}] {levelname:>8}: {message}',
                              style='{')


def configure_logger(log):
    handler = logging.StreamHandler()

    # noinspection PyUnreachableCode
    if log.level == logging.DEBUG:
        handler.setFormatter(DEV_FORMATTER)
    else:
        handler.setFormatter(FORMATTER)

    log.handlers.clear()
    log.addHandler(handler)


LOG = logging.getLogger('fsclean')


def timing_counter():
    return time.perf_counter() * 1000


def pretty_ms(milliseconds):
    if milliseconds is not None:
        if milliseconds <= 1000:
            if isinstance(milliseconds, float):
                return '{:04.2f}ms'.format(milliseconds)
            return '{:04d}ms'.format(milliseconds)
        elif 1000 < milliseconds <= 60000:
            seconds = milliseconds / 1000
            return '{:02.2f}s'.format(seconds)
        elif milliseconds > 60000:
            minutes = milliseconds / 60000
            return '{:02.2f}min'.format(minutes)
    return None

NAMING_OPERATION = 'naming'
EMPTIES_OPERATION = 'empties'
DUPLICATES_OPERATION = 'duplicates'
OPERATION_NAMES = [
    NAMING_OPERATION,
    EMPTIES_OPERATION,
    DUPLICATES_OPERATION
]


if __name__ == '__main__':
    LOG.info(DESCRIPTION)

    op_list = ', '.join(OPERATION_NAMES)
    style_list = ', '.join(STYLE_NAMES)
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument('--op', '-o',
                    required=True,
                    type=str,
                    nargs=1,
                    dest='operations',
                    help='operations to perform on the target directories, '
                         f'comma-separated. {op_list}.')
    ap.add_argument('--changelog', '-c',
                    nargs='?',
                    dest='changelog_path',
                    const='changelog.json',
                    help='enable and set path for JSON log of '
                         'changes made by this program. '
                         'default filename is "changelog.json".')
    ap.add_argument('--dry', '-d',
                    action='store_true',
                    dest='dry_run',
                    help='don\'t actually manipulate files, '
                         'only log what will happen.')
    ap.add_argument('--recurse', '-r',
                    action='store_true',
                    dest='recursive',
                    help='Recursively enter subdirectories.')
    ap.add_argument('--style', '-s',
                    type=str,
                    nargs=1,
                    dest='style',
                    help='specify additional naming rules during the naming '
                         f'operation. {style_list}.')
    ap.add_argument('--space', '-S',
                    nargs=1,
                    dest='space_char',
                    default=None,
                    const=None,
                    help='replace file name spaces with this character '
                         'during the naming operation.')
    ap.add_argument('--level', '-l',
                    nargs=1,
                    type=int,
                    dest='log_level',
                    default=[20],
                    help='logging level (10-50). '
                         'default is 20 INFO.')
    ap.add_argument(nargs='+',
                    dest='targets',
                    help='one or more paths to target directories.')
    apr = ap.parse_args(sys.argv[1:])

    LOG.setLevel(apr.log_level[0])
    configure_logger(LOG)

    operations_text = apr.operations[0]
    changelog_path = apr.changelog_path
    targets = apr.targets
    dry_run = apr.dry_run
    recursive = apr.recursive
    style_text = apr.style[0] if apr.style is not None else None
    space_char = apr.space_char[0] if apr.space_char is not None else None

    if space_char is not None and len(space_char) > 1:
        LOG.error('space character argument cannot be more than one character')
        exit(10)

    if dry_run:
        LOG.info('dry run enabled')

    if recursive:
        LOG.info('recursive search enabled')

    # prepare a new instance of a ChangeLog to record changes to files
    cl = ChangeLog()

    # record time before starting the operations
    start = datetime.datetime.now()
    stopwatch = timing_counter()

    operations = operations_text.split(',')
    bytes_freed = 0

    valid_targets = []
    for target in targets:
        if not os.path.isdir(target):
            LOG.error(f'invalid target "{target}": not a directory')
        else:
            valid_targets.append(target)

    for op in operations:
        if op.lower() == NAMING_OPERATION:
            # filename consistency normalizer routine.
            LOG.info('operation: filename consistency')

            style = None
            if style_text is not None:
                style_text = style_text.strip().lower()

                if style_text not in STYLE_NAMES:
                    LOG.warning(f'ignoring unknown style "{style_text}"')
                else:
                    style = style_text

            for target in valid_targets:
                rename_dir(cl, target, dry_run, recursive,
                           style=style, space_char=space_char)
        elif op.lower() == EMPTIES_OPERATION:
            # empty files and dirs routine.
            LOG.info('operation: empty files and directories')

            for target in valid_targets:
                remove_empty(cl, target, dry_run, recursive)
        elif op.lower() == DUPLICATES_OPERATION:
            # duplicate search routine.
            LOG.info('operation: duplicate search')

            for target in valid_targets:
                bytes_freed += remove_duplicates(cl,
                                                 target,
                                                 dry_run,
                                                 recursive)

        else:
            LOG.warning(f'ignoring unknown operation "{op}"')

    job_time = timing_counter() - stopwatch
    # format the duration message
    duration_text = pretty_ms(job_time)

    LOG.info('{} changes in {}'.format(len(cl.changes), duration_text))

    # add version and statistics to root object of JSON file
    cl.addRootProperties({
        'version': 2,
        'start': start.isoformat(),
        'duration': job_time,
        'bytes_freed': bytes_freed
    })

    # write dictionary to JSON file
    if changelog_path is not None:
        LOG.info('writing changelog to "{}"'.format(changelog_path))
        try:
            cl.save(changelog_path, indent=True)
        except IOError as e:
            LOG.error(f'could not write changelog to "{changelog_path}": '
                      f'{str(e)}')
            exit(2)
    else:
        LOG.info('no changelog specified')
        exit(3)
else:
    print('This Python file must be ran directly.')
    exit(1)
