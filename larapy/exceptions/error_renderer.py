from typing import Dict, Any, Optional, List, Tuple
import traceback
import linecache
import html
import json
import os


class ErrorRenderer:

    def __init__(self, debug: bool = False):
        self.debug = debug

    def render_html(
        self, exception: Exception, status_code: int, context: Optional[Dict[str, Any]] = None
    ) -> str:
        if self.debug:
            return self._render_debug_html(exception, status_code, context or {})
        else:
            return self._render_production_html(status_code)

    def render_json(
        self, exception: Exception, status_code: int, context: Optional[Dict[str, Any]] = None
    ) -> str:
        error_data = {
            "message": str(exception),
            "status_code": status_code,
        }

        if self.debug:
            error_data["exception"] = type(exception).__name__
            error_data["file"] = self._get_exception_file(exception)
            error_data["line"] = self._get_exception_line(exception)
            error_data["trace"] = self._get_stack_trace(exception)

            if context:
                error_data["context"] = context

        return json.dumps(error_data, indent=2 if self.debug else None)

    def render_text(self, exception: Exception, status_code: int) -> str:
        if self.debug:
            return self._format_exception_text(exception)
        else:
            return f"Error {status_code}: {str(exception)}"

    def _render_debug_html(
        self, exception: Exception, status_code: int, context: Dict[str, Any]
    ) -> str:
        exception_name = type(exception).__name__
        exception_message = html.escape(str(exception))
        file_path = html.escape(self._get_exception_file(exception) or "Unknown")
        line_number = self._get_exception_line(exception) or 0

        code_snippet = self._get_code_snippet(self._get_exception_file(exception), line_number)

        stack_trace = self._get_stack_trace_html(exception)
        context_html = self._render_context_html(context)

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{exception_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; color: #333; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .error-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .error-header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .error-header .message {{ font-size: 18px; opacity: 0.95; }}
        .error-header .location {{ font-size: 14px; opacity: 0.8; margin-top: 10px; }}
        .section {{ background: white; border-radius: 8px; padding: 25px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .section h2 {{ font-size: 20px; margin-bottom: 15px; color: #667eea; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; }}
        .code-snippet {{ background: #2d2d2d; color: #f8f8f2; padding: 20px; border-radius: 6px; overflow-x: auto; font-family: 'Monaco', 'Menlo', 'Courier New', monospace; font-size: 13px; }}
        .code-line {{ display: flex; padding: 2px 0; }}
        .line-number {{ color: #6c6c6c; width: 50px; text-align: right; padding-right: 15px; user-select: none; }}
        .line-content {{ flex: 1; white-space: pre; }}
        .error-line {{ background: rgba(255, 85, 85, 0.15); border-left: 3px solid #ff5555; }}
        .error-line .line-number {{ color: #ff5555; font-weight: bold; }}
        .stack-trace {{ font-family: 'Monaco', 'Menlo', 'Courier New', monospace; font-size: 13px; }}
        .stack-frame {{ padding: 12px; margin-bottom: 8px; background: #f8f8f8; border-left: 3px solid #ddd; border-radius: 4px; }}
        .stack-frame.error-frame {{ border-left-color: #ff5555; background: #fff5f5; }}
        .stack-frame-header {{ font-weight: bold; color: #667eea; margin-bottom: 5px; }}
        .stack-frame-location {{ color: #666; font-size: 12px; }}
        .context-section {{ margin-bottom: 15px; }}
        .context-section h3 {{ font-size: 16px; color: #555; margin-bottom: 10px; padding-bottom: 5px; border-bottom: 1px solid #e0e0e0; }}
        .context-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        .context-table td {{ padding: 8px; border-bottom: 1px solid #f0f0f0; }}
        .context-table td:first-child {{ font-weight: bold; color: #667eea; width: 200px; vertical-align: top; }}
        .context-value {{ font-family: 'Monaco', 'Menlo', monospace; color: #333; word-break: break-all; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="error-header">
            <h1>{exception_name}</h1>
            <div class="message">{exception_message}</div>
            <div class="location">{file_path}:{line_number}</div>
        </div>

        {code_snippet}

        <div class="section">
            <h2>Stack Trace</h2>
            {stack_trace}
        </div>

        {context_html}
    </div>
</body>
</html>"""

    def _render_production_html(self, status_code: int) -> str:
        status_messages = {
            400: ("Bad Request", "The request could not be understood by the server."),
            401: ("Unauthorized", "Authentication is required and has failed."),
            403: ("Forbidden", "You do not have permission to access this resource."),
            404: ("Not Found", "The requested resource could not be found."),
            405: ("Method Not Allowed", "The request method is not supported."),
            500: ("Server Error", "The server encountered an internal error."),
            503: ("Service Unavailable", "The server is temporarily unavailable."),
        }

        title, message = status_messages.get(status_code, ("Error", "An error occurred."))

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{status_code} - {title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }}
        .error-container {{ text-align: center; max-width: 600px; }}
        .error-code {{ font-size: 120px; font-weight: bold; opacity: 0.9; line-height: 1; margin-bottom: 20px; }}
        .error-title {{ font-size: 36px; margin-bottom: 15px; }}
        .error-message {{ font-size: 18px; opacity: 0.9; margin-bottom: 30px; }}
        .error-link {{ display: inline-block; padding: 12px 30px; background: rgba(255,255,255,0.2); color: white; text-decoration: none; border-radius: 6px; font-size: 16px; transition: background 0.3s; }}
        .error-link:hover {{ background: rgba(255,255,255,0.3); }}
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-code">{status_code}</div>
        <div class="error-title">{title}</div>
        <div class="error-message">{message}</div>
        <a href="/" class="error-link">Go Home</a>
    </div>
</body>
</html>"""

    def _get_code_snippet(
        self, file_path: Optional[str], line_number: int, context_lines: int = 7
    ) -> str:
        if not file_path or line_number == 0:
            return ""

        try:
            # Handle symlink/alias paths that may not exist
            # Try to resolve to real path, and also handle common symlink patterns
            resolved_path = os.path.realpath(file_path)
            
            # If resolved path doesn't exist, try common path substitutions
            # (e.g., /Downloads/larapy/ might be aliased to /Herd/)
            possible_paths = [resolved_path, file_path]
            if '/Downloads/larapy/' in file_path:
                possible_paths.append(file_path.replace('/Downloads/larapy/', '/Herd/'))
            if '/Herd/' in file_path:
                possible_paths.append(file_path.replace('/Herd/', '/Downloads/larapy/'))
            
            # Try to read the file directly first
            lines = []
            start = max(1, line_number - context_lines)
            end = line_number + context_lines
            
            # Try each possible path to read the file
            found_file = False
            for path in possible_paths:
                if os.path.exists(path):
                    found_file = True
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        all_lines = f.readlines()
                        for i in range(start, min(end + 1, len(all_lines) + 1)):
                            if i - 1 < len(all_lines):
                                line = all_lines[i - 1]
                                is_error_line = i == line_number
                                line_class = "code-line error-line" if is_error_line else "code-line"
                                line_content = html.escape(line.rstrip())

                                lines.append(
                                    f'<div class="{line_class}">'
                                    f'<span class="line-number">{i}</span>'
                                    f'<span class="line-content">{line_content}</span>'
                                    f"</div>"
                                )
                    break  # Successfully read file, exit loop
            
            # If we couldn't read the file directly, try linecache
            if not found_file:
                for path_to_try in possible_paths:
                    # Test if this path works with linecache
                    test_line = linecache.getline(path_to_try, line_number)
                    if test_line:
                        # This path works, read all lines
                        for i in range(start, end + 1):
                            line = linecache.getline(path_to_try, i)
                            if not line:
                                break

                            is_error_line = i == line_number
                            line_class = "code-line error-line" if is_error_line else "code-line"
                            line_content = html.escape(line.rstrip())

                            lines.append(
                                f'<div class="{line_class}">'
                                f'<span class="line-number">{i}</span>'
                                f'<span class="line-content">{line_content}</span>'
                                f"</div>"
                            )
                        break  # Successfully read lines, exit loop

            if not lines:
                return ""

            return f"""
        <div class="section">
            <h2>Code Snippet</h2>
            <div class="code-snippet">
                {''.join(lines)}
            </div>
        </div>"""
        except Exception:
            return ""

    def _get_stack_trace_html(self, exception: Exception) -> str:
        frames = []
        tb = exception.__traceback__
        error_file = self._get_exception_file(exception)
        error_line = self._get_exception_line(exception)

        while tb is not None:
            frame = tb.tb_frame
            filename = frame.f_code.co_filename
            line_number = tb.tb_lineno
            function_name = frame.f_code.co_name

            is_error_frame = filename == error_file and line_number == error_line
            frame_class = "stack-frame error-frame" if is_error_frame else "stack-frame"

            frames.append(
                f"""
                <div class="{frame_class}">
                    <div class="stack-frame-header">{html.escape(function_name)}</div>
                    <div class="stack-frame-location">{html.escape(filename)}:{line_number}</div>
                </div>
            """
            )

            tb = tb.tb_next

        return '<div class="stack-trace">' + "".join(frames) + "</div>"

    def _get_stack_trace(self, exception: Exception) -> List[Dict[str, Any]]:
        trace = []
        tb = exception.__traceback__

        while tb is not None:
            frame = tb.tb_frame
            trace.append(
                {
                    "file": frame.f_code.co_filename,
                    "line": tb.tb_lineno,
                    "function": frame.f_code.co_name,
                }
            )
            tb = tb.tb_next

        return trace

    def _render_context_html(self, context: Dict[str, Any]) -> str:
        if not context:
            return ""

        sections = []

        # Separate dict sections from scalar values
        dict_sections = {}
        scalar_values = {}
        
        for section_name, section_data in context.items():
            if isinstance(section_data, dict):
                dict_sections[section_name] = section_data
            else:
                scalar_values[section_name] = section_data

        # Render dict sections
        for section_name, section_data in dict_sections.items():
            if not section_data:
                continue

            rows = []
            for key, value in section_data.items():
                value_str = html.escape(str(value))
                rows.append(
                    f"""
                    <tr>
                        <td>{html.escape(str(key))}</td>
                        <td class="context-value">{value_str}</td>
                    </tr>
                """
                )

            if rows:
                sections.append(
                    f"""
                    <div class="context-section">
                        <h3>{html.escape(section_name.title())}</h3>
                        <table class="context-table">
                            {''.join(rows)}
                        </table>
                    </div>
                """
                )
        
        # Render scalar values in a "Custom" section
        if scalar_values:
            rows = []
            for key, value in scalar_values.items():
                value_str = html.escape(str(value))
                rows.append(
                    f"""
                    <tr>
                        <td>{html.escape(str(key))}</td>
                        <td class="context-value">{value_str}</td>
                    </tr>
                """
                )
            
            sections.append(
                f"""
                <div class="context-section">
                    <h3>Custom</h3>
                    <table class="context-table">
                        {''.join(rows)}
                    </table>
                </div>
            """
            )

        if not sections:
            return ""

        return f"""
        <div class="section">
            <h2>Context</h2>
            {''.join(sections)}
        </div>"""

    def _format_exception_text(self, exception: Exception) -> str:
        return "".join(
            traceback.format_exception(type(exception), exception, exception.__traceback__)
        )

    def _get_exception_file(self, exception: Exception) -> Optional[str]:
        tb = exception.__traceback__
        if tb is None:
            return None

        while tb.tb_next is not None:
            tb = tb.tb_next

        return tb.tb_frame.f_code.co_filename

    def _get_exception_line(self, exception: Exception) -> Optional[int]:
        tb = exception.__traceback__
        if tb is None:
            return None

        while tb.tb_next is not None:
            tb = tb.tb_next

        return tb.tb_lineno
