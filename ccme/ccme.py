# Cc Me! Plugin
"""Cc Me!"""
version= "1.1"

import datetime
import re

from genshi.builder import tag
from genshi.filters import Transformer

from trac.core import *
from trac.ticket import Ticket
from trac.util.datefmt import utc
from trac.util.presentation import captioned_button
from trac.util.presentation import captioned_button
from trac.util.translation import _
from trac.web.api import IRequestHandler, ITemplateStreamFilter
from trac.web.chrome import add_notice, add_stylesheet, add_warning, ITemplateProvider

class CcMe(Component):
    """
    Cc Me!

    Trac plugin for handling a CC button without TICKET_CHGPROP perms
    """


    implements(IRequestHandler, ITemplateProvider, ITemplateStreamFilter)

    def __init__(self):
        pass

    # IRequestHandler methods

    def match_request(self, req):

        if req.method == 'POST' and req.path_info == "/ccme":
            return True

        return False


    def process_request(self, req):
        cclist = []

        # extract the ticket number from the request
        try:
            ticket_id = int(req.args.get('ticket'))
        except ValueError:
            raise TracError(_("Could not parse ticket ID for Cc Me!"))

        if not req.perm.has_permission('TICKET_APPEND'):
            add_warning(req, _("You do not have permission to Cc yourself to ticket #%d"), ticket_id)
            return self._redirect(req, ticket_id)

        ticket = Ticket(self.env, ticket_id)

        if len(ticket['cc']) > 0:
            cclist = re.split(r'[;,\s]+', ticket['cc'])        

        user = req.authname
        if user is None:
            add_warning(req, _("Unauthenticated users cannot Cc themselves to tickets"))
            return self._redirect(req, ticket_id)

        if user in cclist:
            add_notice(req, _("You will no longer receive notifications for #%d"), ticket_id)
            cclist.remove(user)
        else:
            add_notice(req, _("You will now receive notifications for ticket #%d"), ticket_id)
            cclist.append(user)

        ticket['cc'] = ', '.join(cclist)

        ticket.save_changes(author=user)
        
        return self._redirect(req, ticket_id)


    def _redirect(self, req, id):
        return req.redirect("%s/ticket/%s" % (req.base_path, id))
        
    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html':
            ticket = data.get('ticket')
            if ticket and ticket.exists and \
                    'TICKET_APPEND' in req.perm(ticket.resource):
                filter = Transformer('//th[@id="h_cc"]')
                stream |= filter.append(self._ccme_form(req, ticket, data))
	    add_stylesheet(req, 'ccme/css/ccme.css')
        return stream

    def _ccme_form(self, req, ticket, data):
        return tag.form(
            tag.div(
                tag.input(type="submit", name="ccme",
                          value=captioned_button(req, u'\u2709', _("Cc Me!")),
                          title=_("Add/remove yourself to/from the Cc list")),
                tag.input(type="hidden", name='ticket', value=ticket.id),
		class_="inlinebuttons"),
            method="post", action=req.href('/ccme'))

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """Return a list of directories containing the provided templates."""
	return []

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.

        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('ccme', resource_filename(__name__, 'htdocs'))]

