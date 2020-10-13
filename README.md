# fsclean
A utility for cleaning up duplicate files and file names.

What this program does:
- Search a directory for duplicate files based of of hash (recursively with `--recurse`).
- Rename files with common name inconsistencies:
    - Extraneous spaces
    - Uppercase extension names
    - Stripping beginning and end of " ", "_", "-"
    - Spaces directly before or after a "."
- Enforce file name style like all uppercase, lowercase, capitalized or title case. See `--style`.
- Remove or replace spaces in file names. See `--space`.
- Generate a JSON change log of renamed or removed files. See `--changelog`.
- Dry run to preview changes (`--dry`).

##### Usage
```
cli.py [-h] --op {duplicates,naming} [{duplicates,naming} ...]
       [--changelog [CHANGELOG_PATH]] [--dry] [--recurse]
       [--style {capitalized,titlecase,lowercase,uppercase}]
       [--space SPACE_CHAR] [--level LOG_LEVEL]
       targets [targets ...]
```
Example:
Doing a recursive duplicates and naming pass on a directory called `exampledir`.

```bash
$ python cli.py exampledir -r -o duplicates naming
```

##### Positional Arguments
- `targets` - One or more paths to directories.

##### Optional Arguments
```
-h, --help          show this help message and exit
--op {duplicates,naming} [{duplicates,naming} ...], -o {duplicates,naming} [{duplicates,naming} ...]
                    operations to perform on the target directories.
--changelog [CHANGELOG_PATH], -c [CHANGELOG_PATH]
                    enable and set path for JSON log of changes made by
                    this program.default filename is "changelog.json".
--dry, -d             don't actually manipulate files, only log what will
                    happen.
--recurse, -r         Recursively enter subdirectories.
--style {capitalized,titlecase,lowercase,uppercase}, -s {capitalized,titlecase,lowercase,uppercase}
                    specify additional naming rules when using the naming
                    operation.
--space SPACE_CHAR, -S SPACE_CHAR
                    replace file name spaces with this character. only
                    applies to the naming operation.
--level LOG_LEVEL, -l LOG_LEVEL
                    logging level (10-50). default is 20 INFO.
```

Note: Log level integer values can be found in the Python logging package documentation.