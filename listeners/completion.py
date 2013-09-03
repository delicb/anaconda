
# Copyright (C) 2013 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sublime
import sublime_plugin

from ..anaconda_lib.worker import Worker
from ..anaconda_lib.helpers import prepare_send_data, get_settings, active_view
from ..anaconda_lib.decorators import (
    only_python, profile, on_auto_formatting_enabled
)

JUST_COMPLETED = False


class AnacondaEventListener(sublime_plugin.EventListener):
    """Anaconda events listener class
    """

    completions = []
    ready_from_defer = False

    @only_python
    @profile
    def on_query_completions(self, view, prefix, locations):
        """Sublime Text autocompletion event handler
        """

        global JUST_COMPLETED

        if self.ready_from_defer is True:
            completion_flags = 0

            if get_settings(view, 'suppress_word_completions', False):
                completion_flags = sublime.INHIBIT_WORD_COMPLETIONS

            if get_settings(view, 'suppress_explicit_completions', False):
                completion_flags |= sublime.INHIBIT_EXPLICIT_COMPLETIONS

            cpl = self.completions
            self.completions = []
            self.ready_from_defer = False
            JUST_COMPLETED = True

            return (cpl, completion_flags)

        location = view.rowcol(locations[0])
        data = prepare_send_data(location, 'autocomplete')

        Worker().execute(self._complete, **data)
        return

    @only_python
    @on_auto_formatting_enabled
    def on_pre_save_async(self, view):
        """Called just before the file is going to be saved
        """

        view.run_command('anaconda_auto_format')

    @only_python
    def on_modified_async(self, view):
        """Called after changes has been made to a view.
        """
        global JUST_COMPLETED

        if (view.substr(view.sel()[0].begin() - 1) == '('
                and view.substr(view.sel()[0].begin()) == ')'):
            if JUST_COMPLETED:
                view.run_command('anaconda_complete_funcargs')

            JUST_COMPLETED = False
        elif view.substr(sublime.Region(
                view.sel()[0].begin() - 7, view.sel()[0].end())) == 'import ':
            view.run_command('auto_complete')

    def _complete(self, data):

        proposals = data['completions'] if data['success'] else []

        if proposals:
            active_view().run_command("hide_auto_complete")
            self.completions = proposals
            self.ready_from_defer = True

            active_view().run_command("auto_complete", {
                'disable_auto_insert': True,
                'api_completions_only': get_settings(
                    active_view(), 'hide_snippets_on_completion', False),
                'next_completion_if_showing': False,
                'auto_complete_commit_on_tab': True,
            })