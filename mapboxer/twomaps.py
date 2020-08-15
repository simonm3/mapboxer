import logging
import os
from os.path import expanduser
from pathlib import Path

import yaml
import yatl

from .utils import tempdir

log = logging.getLogger(__name__)

token = yaml.safe_load(open(expanduser("~") + "/.mapbox/creds.yaml"))


class Twomaps:
    """ containing two maps  """

    def __init__(self, map1, map2, template="slider"):
        """
        :param template: template.html or just template

        todo: create a template for side by side comparison
        """
        self.map1 = map1
        self.map2 = map2
        self.map1.container = "map1"
        self.map2.container = "map2"
        if not os.path.splitext(template)[-1]:
            template = template + ".html"
        self.template = template

    def html(self):
        """ return html page
        """
        with tempdir(Path(__file__).parent.parent / "templates"):
            html = open(self.template).read()
            self.map1.legends = self.map1.get_legends()
            return yatl.render(
                html,
                delimiters="[[ ]]",
                context=dict(token=token, map1=self.map1, map2=self.map2),
            )

    def save(self, filename):
        """ save map as html """
        if not os.path.splitext(filename)[-1]:
            filename = filename + ".html"
        if not filename.find(os.sep) >= 0:
            filename = Path(__file__).parent.parent / "data/output" / filename
        with open(filename, "w", encoding="utf8") as f:
            f.write(self.html())
