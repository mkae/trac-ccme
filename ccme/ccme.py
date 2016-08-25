# Cc Me! Plugin
"""Cc Me!"""

import re

from genshi.builder import tag
from genshi.filters import Transformer

from trac.core import Component, implements, TracError
from trac.ticket import Ticket
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

    def match_request(self, req): # pylint: disable=no-self-use
        """
        Decide whether the given request `req` should be handled by this
        component.
        """
        if req.method == 'POST' and req.path_info == "/ccme":
            return True

        return False


    def process_request(self, req):
        """
        Handle the POST and add or remove the current user from Cc of the given
        ticket.
        """
        cclist = []

        # extract the ticket number from the request
        try:
            ticket_id = int(req.args.get('ticket'))
        except ValueError:
            raise TracError(_("Could not parse ticket ID for Cc Me!"))

        if not req.perm.has_permission('TICKET_APPEND'):
            add_warning(req,
                        _("You do not have permission to Cc yourself to ticket #%d"),
                        ticket_id)
            return self._redirect(req, ticket_id)

        # pylint: disable=no-member
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

    def _redirect(self, req, ticket_id): # pylint: disable=no-self-use
        return req.redirect("%s/ticket/%s" % (req.base_path, ticket_id))

    # ITemplateStreamFilter methods

    # pylint: disable=too-many-arguments, unused-argument
    def filter_stream(self, req, method, filename, stream, data):
        """
        Filter the ticket template and add the Cc Me! button next to the Cc
        list.
        """
        if filename == 'ticket.html':
            ticket = data.get('ticket')
            if ticket and ticket.exists and \
                    'TICKET_APPEND' in req.perm(ticket.resource):
                transformer = Transformer('//th[@id="h_cc"]')
                stream |= transformer.append(self._ccme_form(req, ticket, data))
            add_stylesheet(req, 'ccme/css/ccme.css')
        return stream

    def _ccme_form(self, req, ticket, data): # pylint: disable=no-self-use
        return tag.form(
            tag.div(
                tag.input(type="submit", name="ccme",
                          value=captioned_button(req, u'\u2709', _("Cc Me!")),
                          title=_("Add/remove yourself to/from the Cc list")),
                tag.input(type="hidden", name='ticket', value=ticket.id),
                class_="inlinebuttons"),
            method="post", action=req.href('/ccme'))

    # ITemplateProvider methods
    def get_templates_dirs(self): # pylint: disable=no-self-use
        """Return a list of directories containing the provided templates."""
        return []

    def get_htdocs_dirs(self): # pylint: disable=no-self-use
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
