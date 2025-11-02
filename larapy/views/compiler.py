"""
Template Compiler

Compiles Blade-like template syntax to Python code.
"""

import html
import re
from typing import Any, Dict, List, Optional, Tuple


class Compiler:
    """
    Template compiler for Blade-like syntax.

    Compiles templates to Python code that can be executed with context data.
    """

    def __init__(self) -> None:
        self.raw_tags = ("{!!", "!!}")
        self.escaped_tags = ("{{", "}}")
        self.comment_tags = ("{{--", "--}}")
        self.custom_directives: Dict[str, callable] = {}
        self.sections: Dict[str, str] = {}
        self.section_stack: List[str] = []
        self.extends_template: Optional[str] = None
        self.compiled_code: List[str] = []
        self.indent_level = 0
        self.local_vars: List[str] = []

    def compile(self, template: str) -> str:
        """
        Compile template to Python code.

        Args:
            template: Template string

        Returns:
            Compiled Python code
        """
        self.compiled_code = []
        self.sections = {}
        self.section_stack = []
        self.extends_template = None
        self.indent_level = 0
        self.local_vars = []

        self._emit("import html")
        self._emit("def render(__context__):")
        self._indent()
        self._emit("__output__ = []")
        self._emit("__append__ = __output__.append")

        lines = template.split("\n")
        self._compile_lines(lines)

        self._emit("return ''.join(__output__)")
        self._dedent()

        return "\n".join(self.compiled_code)

    def _compile_lines(self, lines: List[str]) -> None:
        """Compile list of template lines."""
        i = 0
        while i < len(lines):
            line = lines[i]

            line = self._compile_comments(line)

            if not line.strip():
                i += 1
                continue

            if self._contains_directive(line):
                directive_match = re.search(r"@(\w+)", line)
                if directive_match:
                    directive = directive_match.group(1)
                    
                    args = ""
                    start_pos = directive_match.end()
                    if start_pos < len(line) and line[start_pos] == '(':
                        paren_count = 1
                        pos = start_pos + 1
                        while pos < len(line) and paren_count > 0:
                            if line[pos] == '(':
                                paren_count += 1
                            elif line[pos] == ')':
                                paren_count -= 1
                            pos += 1
                        args = line[start_pos + 1:pos - 1]
                        directive_end = pos
                    else:
                        directive_end = start_pos

                    before = line[: directive_match.start()]
                    after = line[directive_end:]

                    if before.strip():
                        self._compile_line(before)

                    i = self._compile_directive(directive, args, lines, i)

                    if after.strip():
                        self._compile_line(after)

                    i += 1
                    continue

            self._compile_line(line)
            i += 1

    def _compile_line(self, line: str) -> None:
        """Compile single line of template."""
        if not line.strip():
            return

        parts = []
        last_pos = 0

        raw_pattern = re.escape(self.raw_tags[0]) + r"\s*(.+?)\s*" + re.escape(self.raw_tags[1])
        escaped_pattern = (
            re.escape(self.escaped_tags[0]) + r"\s*(.+?)\s*" + re.escape(self.escaped_tags[1])
        )

        for match in re.finditer(f"({raw_pattern})|({escaped_pattern})", line):
            if match.start() > last_pos:
                text = line[last_pos : match.start()]
                if text:
                    parts.append(("text", text))

            if match.group(1):
                expr = match.group(2).strip() if match.group(2) else ""
                parts.append(("raw", expr))
            else:
                expr = match.group(4).strip() if match.group(4) else ""
                parts.append(("escaped", expr))

            last_pos = match.end()

        if last_pos < len(line):
            text = line[last_pos:]
            if text:
                parts.append(("text", text))

        if not parts:
            return

        for part_type, content in parts:
            if part_type == "text":
                self._emit_text(content)
            elif part_type == "raw":
                self._emit_raw(content)
            elif part_type == "escaped":
                self._emit_escaped(content)

    def _compile_comments(self, template: str) -> str:
        """Remove Blade comments."""
        pattern = re.escape(self.comment_tags[0]) + r".*?" + re.escape(self.comment_tags[1])
        return re.sub(pattern, "", template, flags=re.DOTALL)

    def _compile_raw_echoes(self, template: str) -> str:
        """Compile raw echo statements."""
        pattern = re.escape(self.raw_tags[0]) + r"\s*(.+?)\s*" + re.escape(self.raw_tags[1])

        def replace(match):
            expr = match.group(1).strip()
            return "' + str(__context__.get('" + expr + "', '')) + '"

        return re.sub(pattern, replace, template)

    def _compile_escaped_echoes(self, template: str) -> str:
        """Compile escaped echo statements."""
        pattern = re.escape(self.escaped_tags[0]) + r"\s*(.+?)\s*" + re.escape(self.escaped_tags[1])

        def replace(match):
            expr = match.group(1).strip()

            if expr.startswith("$"):
                expr = expr[1:]

            if "." in expr:
                parts = expr.split(".")
                access = "__context__.get('" + parts[0] + "', {})"
                for part in parts[1:]:
                    if part.isdigit():
                        access = f"({access}[{part}] if isinstance({access}, list) and len({access}) > {part} else '')"
                    else:
                        access = f"({access}.get('{part}', '') if isinstance({access}, dict) else getattr({access}, '{part}', ''))"
                return "' + html.escape(str(" + access + ")) + '"
            else:
                return "' + html.escape(str(__context__.get('" + expr + "', ''))) + '"

        return re.sub(pattern, replace, template)

    def _compile_directive(
        self, directive: str, args: str, lines: List[str], current_line: int
    ) -> int:
        """
        Compile directive statement.

        Args:
            directive: Directive name
            args: Directive arguments
            lines: All template lines
            current_line: Current line index

        Returns:
            New line index after directive processing
        """
        if directive == "if":
            self._compile_if(args)
            return current_line

        elif directive == "elseif":
            self._compile_elseif(args)
            return current_line

        elif directive == "else":
            self._compile_else()
            return current_line

        elif directive == "endif":
            self._compile_endif()
            return current_line

        elif directive == "unless":
            self._compile_unless(args)
            return current_line

        elif directive == "endunless":
            self._compile_endunless()
            return current_line

        elif directive == "foreach":
            self._compile_foreach(args)
            return current_line

        elif directive == "endforeach":
            self._compile_endforeach()
            return current_line

        elif directive == "for":
            self._compile_for(args)
            return current_line

        elif directive == "endfor":
            self._compile_endfor()
            return current_line

        elif directive == "while":
            self._compile_while(args)
            return current_line

        elif directive == "endwhile":
            self._compile_endwhile()
            return current_line

        elif directive == "break":
            self._compile_break()
            return current_line

        elif directive == "continue":
            self._compile_continue()
            return current_line

        elif directive == "extends":
            self._compile_extends(args)
            return current_line

        elif directive == "section":
            return self._compile_section(args, lines, current_line)

        elif directive == "endsection":
            return current_line

        elif directive == "yield":
            self._compile_yield(args)
            return current_line

        elif directive == "parent":
            self._compile_parent()
            return current_line

        elif directive == "include":
            self._compile_include(args)
            return current_line

        elif directive == "isset":
            self._compile_isset(args)
            return current_line

        elif directive == "endisset":
            self._compile_endisset()
            return current_line

        elif directive == "empty":
            self._compile_empty(args)
            return current_line

        elif directive == "endempty":
            self._compile_endempty()
            return current_line

        elif directive == "auth":
            self._compile_auth(args)
            return current_line

        elif directive == "endauth":
            self._compile_endauth()
            return current_line

        elif directive == "guest":
            self._compile_guest()
            return current_line

        elif directive == "endguest":
            self._compile_endguest()
            return current_line

        elif directive in self.custom_directives:
            self._compile_custom_directive(directive, args)
            return current_line

        return current_line

    def _compile_if(self, condition: str) -> None:
        """Compile @if directive."""
        condition = self._convert_condition(condition)
        self._emit(f"if {condition}:")
        self._indent()

    def _compile_elseif(self, condition: str) -> None:
        """Compile @elseif directive."""
        self._dedent()
        condition = self._convert_condition(condition)
        self._emit(f"elif {condition}:")
        self._indent()

    def _compile_else(self) -> None:
        """Compile @else directive."""
        self._dedent()
        self._emit("else:")
        self._indent()

    def _compile_endif(self) -> None:
        """Compile @endif directive."""
        self._dedent()

    def _compile_unless(self, condition: str) -> None:
        """Compile @unless directive."""
        condition = self._convert_condition(condition)
        self._emit(f"if not ({condition}):")
        self._indent()

    def _compile_endunless(self) -> None:
        """Compile @endunless directive."""
        self._dedent()

    def _compile_foreach(self, args: str) -> None:
        """Compile @foreach directive."""
        match = re.match(r"(.+?)\s+as\s+(\w+)(?:\s*,\s*(\w+))?", args.strip())
        if not match:
            raise ValueError(f"Invalid foreach syntax: {args}")

        collection = self._convert_expression_to_python(match.group(1))
        first_var = match.group(2)
        second_var = match.group(3)

        if second_var:
            self.local_vars.extend([first_var, second_var])
            self._emit(
                f"for {first_var}, {second_var} in (enumerate({collection}) if isinstance({collection}, list) else {collection}.items() if isinstance({collection}, dict) else []):"
            )
        else:
            self.local_vars.append(first_var)
            self._emit(
                f"for {first_var} in ({collection} if isinstance({collection}, (list, dict)) else []):"
            )

        self._indent()

    def _compile_endforeach(self) -> None:
        """Compile @endforeach directive."""
        self._dedent()
        if self.local_vars:
            self.local_vars.pop()
            if len(self.local_vars) > 0 and self.indent_level == 1:
                self.local_vars.pop()

    def _compile_for(self, args: str) -> None:
        """Compile @for directive."""
        match = re.match(r"(\w+)\s+in\s+(.+)", args.strip())
        if match:
            loop_var = match.group(1)
            self.local_vars.append(loop_var)
        
        self._emit(f"for {args}:")
        self._indent()

    def _compile_endfor(self) -> None:
        """Compile @endfor directive."""
        self._dedent()
        if self.local_vars:
            self.local_vars.pop()

    def _compile_while(self, condition: str) -> None:
        """Compile @while directive."""
        condition = self._convert_condition(condition)
        self._emit(f"while {condition}:")
        self._indent()

    def _compile_endwhile(self) -> None:
        """Compile @endwhile directive."""
        self._dedent()

    def _compile_break(self) -> None:
        """Compile @break directive."""
        self._emit("break")

    def _compile_continue(self) -> None:
        """Compile @continue directive."""
        self._emit("continue")

    def _compile_extends(self, parent: str) -> None:
        """Compile @extends directive."""
        self.extends_template = parent.strip("'\"")

    def _compile_section(self, name: str, lines: List[str], current_line: int) -> int:
        """Compile @section directive."""
        section_name = name.strip("'\"").split(",")[0].strip("'\"")
        self.section_stack.append(section_name)

        section_content = []
        i = current_line + 1
        depth = 1

        while i < len(lines) and depth > 0:
            line = lines[i]
            if "@section" in line:
                depth += 1
            elif "@endsection" in line:
                depth -= 1
                if depth == 0:
                    break
            section_content.append(line)
            i += 1

        self.sections[section_name] = "\n".join(section_content)
        self.section_stack.pop()

        return i

    def _compile_yield(self, section: str) -> None:
        """Compile @yield directive."""
        parts = [p.strip().strip("'\"") for p in section.split(",")]
        section_name = parts[0]
        default = parts[1] if len(parts) > 1 else "''"

        self._emit(
            f"__append__(__context__.get('__sections__', {{}}).get('{section_name}', {default}))"
        )

    def _compile_parent(self) -> None:
        """Compile @parent directive."""
        if self.section_stack:
            section_name = self.section_stack[-1]
            self._emit(
                f"__append__(__context__.get('__parent_sections__', {{}}).get('{section_name}', ''))"
            )

    def _compile_include(self, args: str) -> None:
        """Compile @include directive."""
        parts = args.split(",", 1)
        view_name = parts[0].strip().strip("'\"")
        data = parts[1].strip() if len(parts) > 1 else "{}"

        self._emit(
            f"__append__(str(__context__.get('__view_factory__').make('{view_name}', {data}).render()))"
        )

    def _compile_isset(self, var: str) -> None:
        """Compile @isset directive."""
        var = var.strip()
        self._emit(f"if '{var}' in __context__ and __context__['{var}'] is not None:")
        self._indent()

    def _compile_endisset(self) -> None:
        """Compile @endisset directive."""
        self._dedent()

    def _compile_empty(self, var: str) -> None:
        """Compile @empty directive."""
        var = var.strip()
        self._emit(f"if not __context__.get('{var}'):")
        self._indent()

    def _compile_endempty(self) -> None:
        """Compile @endempty directive."""
        self._dedent()

    def _compile_auth(self, guard: str = None) -> None:
        """Compile @auth directive."""
        if guard:
            guard = guard.strip().strip('"').strip("'")
            condition = f"__context__.get('__auth__', {{}}).get('{guard}', {{}}).get('check', lambda: False)()"
        else:
            condition = "__context__.get('__auth__', {}).get('check', lambda: False)()"
        self._emit(f"if {condition}:")
        self._indent()

    def _compile_endauth(self) -> None:
        """Compile @endauth directive."""
        self._dedent()

    def _compile_guest(self) -> None:
        """Compile @guest directive."""
        condition = "__context__.get('__auth__', {}).get('guest', lambda: True)()"
        self._emit(f"if {condition}:")
        self._indent()

    def _compile_endguest(self) -> None:
        """Compile @endguest directive."""
        self._dedent()

    def _compile_custom_directive(self, directive: str, args: str) -> None:
        """Compile custom directive."""
        handler = self.custom_directives[directive]
        result = handler(args)
        if result:
            self._emit_output(result)

    def _convert_condition(self, condition: str) -> str:
        """Convert Blade condition to Python condition."""
        condition = condition.strip()
        
        operators = ['>=', '<=', '==', '!=', '>', '<', ' and ', ' or ', ' not ', ' in ']
        has_operator = any(op in condition for op in operators)
        
        if has_operator:
            for word in condition.split():
                if word and not any(op in word for op in ['>=', '<=', '==', '!=', '>', '<']) and word not in ['and', 'or', 'not', 'in', '(', ')']:
                    if word.startswith("$"):
                        word_clean = word[1:]
                    else:
                        word_clean = word
                    
                    if word_clean in self.local_vars:
                        continue
                    
                    if '.' in word_clean:
                        parts = word_clean.split('.')
                        var = parts[0]
                        if var in self.local_vars:
                            continue
                        attr_path = '.'.join(parts[1:])
                        replacement = f"getattr(__context__.get('{var}', {{}}), '{attr_path}', '')"
                        condition = condition.replace(word, replacement)
                    elif word_clean and word_clean[0].isalpha() and word not in ['True', 'False', 'None']:
                        replacement = f"__context__.get('{word_clean}')"
                        condition = condition.replace(word, replacement)
            
            return condition

        if condition.startswith("$"):
            condition = condition[1:]

        condition = condition.replace("$", "")
        
        if condition in self.local_vars:
            return condition

        parts = condition.split(".")
        if len(parts) > 1:
            var = parts[0]
            if var in self.local_vars:
                return condition
            
            result = f"__context__.get('{var}', {{}})"
            for part in parts[1:]:
                result = f"({result}.get('{part}', '') if isinstance({result}, dict) else getattr({result}, '{part}', ''))"
            return result

        return f"__context__.get('{condition}')"

    def _convert_expression(self, expr: str) -> str:
        """Convert Blade expression to Python expression."""
        expr = expr.strip()

        if expr.startswith("$"):
            expr = expr[1:]

        if "." in expr:
            parts = expr.split(".")
            return f"__context__.get('{parts[0]}', {{}}).get('{'.'.join(parts[1:])}', [])"

        return f"__context__.get('{expr}', [])"

    def _is_comment(self, line: str) -> bool:
        """Check if line is a comment."""
        return self.comment_tags[0] in line and self.comment_tags[1] in line

    def _contains_directive(self, line: str) -> bool:
        """Check if line contains directive."""
        return "@" in line and re.search(r"@\w+", line) is not None

    def _emit(self, code: str) -> None:
        """Emit line of Python code."""
        indent = "    " * self.indent_level
        self.compiled_code.append(indent + code)

    def _emit_output(self, text: str) -> None:
        """Emit output statement."""
        if not text:
            return

        text = text.replace("'", "\\'")
        text = text.replace("\n", "\\n")
        self._emit(f"__append__('{text}')")

    def _emit_text(self, text: str) -> None:
        """Emit plain text output."""
        text = text.replace("'", "\\'").replace("\n", "\\n")
        self._emit(f"__append__('{text}')")

    def _emit_raw(self, expr: str) -> None:
        """Emit raw expression output."""
        expr = self._convert_expression_to_python(expr)
        self._emit(f"__append__(str({expr}))")

    def _emit_escaped(self, expr: str) -> None:
        """Emit escaped expression output."""
        expr = self._convert_expression_to_python(expr)
        self._emit(f"__append__(html.escape(str({expr})))")

    def _convert_expression_to_python(self, expr: str) -> str:
        """Convert template expression to Python expression."""
        expr = expr.strip()

        if expr.startswith("$"):
            expr = expr[1:]

        if "." in expr:
            parts = expr.split(".")
            base = parts[0]
            
            if base in self.local_vars:
                result = base
            else:
                result = f"__context__.get('{base}', {{}})"

            for part in parts[1:]:
                if part.isdigit():
                    result = f"({result}[{part}] if isinstance({result}, list) and len({result}) > {part} else '')"
                else:
                    result = f"({result}.get('{part}', '') if isinstance({result}, dict) else getattr({result}, '{part}', ''))"

            return result
        else:
            if expr in self.local_vars:
                return expr
            return f"__context__.get('{expr}', '')"

    def _indent(self) -> None:
        """Increase indentation level."""
        self.indent_level += 1

    def _dedent(self) -> None:
        """Decrease indentation level."""
        self.indent_level = max(0, self.indent_level - 1)

    def directive(self, name: str, handler: callable) -> None:
        """
        Register custom directive.

        Args:
            name: Directive name (without @)
            handler: Callable that takes args and returns string
        """
        self.custom_directives[name] = handler
