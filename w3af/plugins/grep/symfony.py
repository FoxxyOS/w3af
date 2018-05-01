"""
symfony.py

Copyright 2011 Andres Riancho and Carlos Pantelides

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import re

from w3af.core.data.kb.info import Info
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.parsers.mp_document_parser import mp_doc_parser
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin


class symfony(GrepPlugin):
    """
    Grep every page for traces of the Symfony framework.

    :author: Carlos Pantelides (carlos.pantelides@yahoo.com)
    :author: Andres Riancho (andres.riancho@gmail.com)
    :author: Pablo Mouzo (pablomouzo@gmail.com)
    """

    def __init__(self):
        GrepPlugin.__init__(self)

        # Internal variables
        self._override = False
        self._symfony_detected = False

        # Compile only once
        self._symfony_re = re.compile('symfony=', re.IGNORECASE)
        self._csrf_token_re = re.compile('.*csrf_token', re.IGNORECASE)

    def grep(self, request, response):
        """
        Plugin entry point.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None, all results are saved in the kb.
        """
        if not response.is_text_or_html():
            return
        
        if not self.symfony_detected(response):
            return

        if self.has_csrf_token(response):
            return

        desc = ('The URL: "%s" seems to be generated by the Symfony framework'
                ' and contains a form that has CSRF protection disabled.')
        desc %= response.get_url()

        i = Info('Symfony Framework with CSRF protection disabled',
                 desc, response.id, self.get_name())
        i.set_url(response.get_url())
        self.kb_append_uniq(self, 'symfony', i, 'URL')

    def symfony_detected(self, response):
        if self._override:
            return True

        if self._symfony_detected:
            return True

        headers = response.get_headers()
        set_cookie_value, _ = headers.iget('set-cookie', '')
        cookie_value, _ = headers.iget('cookie', '')

        if self._symfony_re.search(cookie_value) or \
           self._symfony_re.search(set_cookie_value):

            self._symfony_detected = True
            return True

        return False

    def has_csrf_token(self, response):
        """
        :return: True if there is CSRF protection enabled in this symfony app
        """
        for tag in mp_doc_parser.get_tags_by_filter(response, ('input',)):
            input_id = tag.attrib.get('id', '')
            if self._csrf_token_re.search(input_id):
                return True

        return False

    def set_options(self, options_list):
        self._override = options_list['override'].get_value()

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Skip symfony detection and search for the csrf (mis)protection.'
        o = opt_factory('override', self._override, d, 'boolean')
        ol.add(o)

        return ol

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every page for traces of the Symfony framework and the
        lack of CSRF protection.
        """
