#!python
""" convert page.rst to page.html

Usage::

    ./rst2html.py <page>
"""
import os
import sys

import docutils.core


def main(path):
    filename, ext = os.path.splitext(path)
    if not ext:
        path = path + ".rst"
    output = filename + ".html"
    docutils.core.publish_file(
        source_path=path, destination_path=output, writer_name="html"
    )


if __name__ == "__main__":
    main(sys.argv[1])
