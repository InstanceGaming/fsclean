import os
import logging
from common import ChangeLog


LOG = logging.getLogger('fsclean.empties')


def remove_empty(cl: ChangeLog,
                 directory,
                 dry_run,
                 recursive):
    for cd, dirs, files in os.walk(directory, followlinks=False):
        files = [os.path.join(cd, f) for f in files]
        for file in files:
            size = os.stat(file).st_size

            if size == 0:
                LOG.info(f'remove empty file "{file}"')

                if not dry_run:
                    try:
                        os.remove(file)
                        cl.addChange(__name__,
                                     True,
                                     path=file)
                    except OSError as e:
                        LOG.error(f'failed to remove "{file}": {str(e)}')
                        cl.addChange(__name__,
                                     False,
                                     path=file,
                                     message=str(e),
                                     errno=e.errno)
                else:
                    cl.addChange(__name__,
                                 False,
                                 path=file)
        for sd in dirs:
            sd_path = os.path.join(cd, sd)
            if os.path.exists(sd_path):
                content = []
                try:
                    content = os.listdir(sd_path)
                except OSError as e:
                    LOG.error(f'failed to list directory "{sd_path}": {str(e)}')
                    cl.addChange(__name__,
                                 False,
                                 path=sd_path,
                                 message=str(e),
                                 errno=e.errno)

                if len(content) == 0:
                    LOG.info(f'remove empty directory "{sd_path}"')

                    if not dry_run:
                        try:
                            os.rmdir(sd_path)
                            cl.addChange(__name__,
                                         True,
                                         path=sd_path)
                        except OSError as e:
                            LOG.error(f'failed to remove "{sd_path}": {str(e)}')
                            cl.addChange(__name__,
                                         False,
                                         path=sd_path,
                                         message=str(e),
                                         errno=e.errno)
                    else:
                        cl.addChange(__name__,
                                     False,
                                     path=sd_path)
        if not recursive:
            break
