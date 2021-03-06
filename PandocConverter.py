# -*- coding: utf-8 -*-
# @Author: klmp200
# @Date:   2016-03-17 19:08:11
# @Last Modified by:   klmp200
# @Last Modified time: 2016-03-19 16:30:02

import sublime
import sublime_plugin
import subprocess
import re
import os


class PandocConverterCommand(sublime_plugin.TextCommand):
    """
        Provide necessary in order to get the file converted
        and opened
    """

    # Convert the file and open it
    def run(self, edit, output):

        # Define some variables
        self.select_pandoc()
        self.detect_input_format(output)

        # Set working directory to let add images
        work_dir = os.path.dirname(self.view.file_name())
        os.chdir(work_dir)

        # Launch command line and open file
        proc = subprocess.Popen(self.build_command_line(output),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True)
        error = proc.communicate()[1]

        if proc.returncode == 0:
            self.open(output)
        else:
            self.show_errors(error)

    # Show errors in sublime
    def show_errors(self, error):
        sublime.active_window().run_command("show_panel", {
            "panel": "console", "toggle": True})
        print(error)

    # Build conversion command line
    def build_command_line(self, output):

        command_line = []
        self.build_output_name(output)
        base_command = [
            self.pandoc,
            "-f", self.input_format,
            self.view.file_name(),
            "-o", self.ofile
        ]
        for command in base_command:
            command_line.append(command)
        for arg in output["pandoc-arguments"]:
            command_line.append(arg)
        return command_line

    # Build output name
    def build_output_name(self, output):

        old_name = self.view.file_name()
        new_name = re.sub(r'(?<=\.)([A-Za-z0-9]+)$',
                          output["output-format"], old_name)
        self.ofile = new_name

    # Open the file
    def open(self, output):

        oformat = output["output-format"]
        if oformat in _s("pandoc-format-file"):
            try:
                if sublime.platform() == 'osx':
                    subprocess.call(['open', self.ofile])
                elif sublime.paltform() == 'windows':
                    os.startfile(self.ofile)
                elif sublime.platform() == 'linux':
                    subprocess.call(['xdg-open', self.ofile])
            except:
                sublime.message_dialog('Wrote to file ' + self.ofile)
        else:
            sublime.active_window().open_file(self.ofile).set_syntax_file(
                output["syntax_file"])

    # Define Pandoc path
    def select_pandoc(self):
        pandoc_path = _s("pandoc-path")[sublime.platform()]
        if pandoc_path == '':
            sublime.message_dialog('Warning : Pandoc path not defined')
            pandoc_path = 'pandoc'
        self.pandoc = pandoc_path

    # Define format of the converted file
    def detect_input_format(self, output):

        scopes = re.split('\s', self.view.scope_name(0))
        self.input_format = output["scope"][scopes[0]]


class PandocConverterPanelCommand(sublime_plugin.WindowCommand):
    """
        Display informations in quick panel and let the user
        chose output settings
    """

    # Main function
    def run(self):

        self.view = self.window.active_view()
        self.window.show_quick_panel(self.get_list(), self.convert)

    # Generate a list of available outputs
    def get_list(self):

        avaliables_outputs = []
        outputs = _s("outputs")

        for output in _s("outputs"):
            added = False
            for scope in outputs[output]["scope"]:
                if self.view.score_selector(0, scope) and not added:
                    avaliables_outputs.append(output)
                    added = True

        self.outputs = avaliables_outputs

        return avaliables_outputs

    # Launch conversion
    def convert(self, i):
        if i != -1:
            choice = _s("outputs")[self.outputs[i]]
            self.view.run_command('pandoc_converter', {
                "output": choice,
            })

# Allow to access easily to settings
def _s(key):
    settings = sublime.load_settings("PandocConverter.sublime-settings")
    return settings.get(key, {})
