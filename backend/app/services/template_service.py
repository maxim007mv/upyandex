import re
from typing import Dict, Any, List, Set, Tuple
from jinja2 import Environment, meta, TemplateSyntaxError, Undefined


class SilentUndefined(Undefined):
    def _fail_with_undefined_error(self, *args, **kwargs):
        return ""


jinja_env = Environment(undefined=SilentUndefined, autoescape=True)


class TemplateService:
    @staticmethod
    def extract_variables(template_str: str) -> List[str]:
        """
        Extracts variable names from a Jinja2 template string,
        including dot notation (e.g. user.full_name) as well as root variables.
        """
        found_set: Set[str] = set()

        # Regex to find dotted names in {{ ... }}
        matches = re.findall(r"\{\{\s*([a-zA-Z0-9_\.]+)\s*\}\}", template_str)
        for m in matches:
            clean = m.strip()
            if clean:
                found_set.add(clean)

        # Jinja AST undeclared variables
        try:
            ast = jinja_env.parse(template_str)
            for var in meta.find_undeclared_variables(ast):
                found_set.add(var)
        except Exception:
            pass

        return sorted(list(found_set))

    @staticmethod
    def validate_template(template_str: str) -> Tuple[bool, str]:
        """Validates Jinja2 template syntax. Returns (is_valid, error_message)."""
        try:
            jinja_env.parse(template_str)
            return True, ""
        except TemplateSyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.message}"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def render(template_str: str, context: Dict[str, Any]) -> str:
        """Renders a Jinja2 template string safely with context dictionary."""
        template = jinja_env.from_string(template_str)
        return template.render(**context)
