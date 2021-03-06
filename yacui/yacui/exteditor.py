import os
import io
import tempfile
import jinja2
import yaml


class ExtEditor:
    """
    Prepare temporary file, execute external editor, parse resulting file.

    Handle errors:
    - file not edited (by timestamp),
    - error in file (non-parseable).

    TODO: Add cursor position setting and option to command template
    """

    def __init__(self, app, command, template_path):
        """
        Args:
          app: application, required to ask user questions, trigger redraw, etc.
          command: command to execute an editor with a {} placeholder for file
          template_path: Location of all templates.
        """
        self.app = app
        self.command = command
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_path),
            autoescape=True
        )

    def edit(self, template, tmpl_args, validator=None):
        """
        Run editor with a given template file.

        Args:
          template: name of the template file within configured directory of templates.
          tmpl_args: Arguments to the template
          validator: Additional validator which must return non-None to accept the edit.
        """
        template = self.env.get_template(template)
        clean_template = template.render(**tmpl_args)

        with tempfile.NamedTemporaryFile(mode="w+") as f:
            f.write(clean_template)
            f.flush()
            mod_time = os.stat(f.name).st_mtime
            editor_command = self.command.format(f.name)
            while True:
                # 1. Execute an editor and check if the user saved the data
                self.app.console.cleanup()
                os.system(editor_command)
                self.app.console.start()
                self.app.display.redraw()
                file_was_saved = mod_time != os.stat(f.name).st_mtime
                if not file_was_saved:
                    answer = self.app.console.query_bool("You haven't saved the file, "
                                                         "do you want to retry?")
                    if not answer:
                        return None
                    continue

                f.seek(0, os.SEEK_SET)
                data_after_change = f.read()
                # 2. Handle YAML parsing
                try:
                    parsed = yaml.safe_load(io.StringIO(data_after_change))
                except Exception:
                    msg = "Unable to parse result as YAML, do you want to retry?"
                    answer = self.app.console.query_bool(msg)
                    if not answer:
                        return None
                    continue

                # 3. Handle external validation
                if validator is not None:
                    try:
                        parsed = validator(parsed)
                    except Exception as e:
                        msg = " ".join(e.args)
                        msg = "Unable to parse values ({}), do you want to retry?".format(msg)
                        answer = self.app.console.query_bool(msg)
                        if not answer:
                            return None
                        continue

                return parsed
