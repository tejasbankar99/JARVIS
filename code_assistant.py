"""
code_assistant.py — JARVIS Code Assistant Module
=================================================
Handles all code-related tasks:
  - Writing code in any language
  - Debugging code
  - Explaining code
  - Saving generated code to files
"""

import re
from pathlib import Path
from config import CODE_OUTPUT_DIR
from brain import ask


# ── Code Extraction Helper ────────────────────────────────────────────────────

def _extract_code_blocks(text: str) -> list:
    """
    Extract code blocks from a markdown-formatted response.
    Returns list of (language, code) tuples.
    """
    pattern = r'```(\w*)\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    return [(lang or "text", code.strip()) for lang, code in matches]


def _save_code_to_file(code: str, filepath: str) -> str:
    """Save code string to a file, creating directories as needed."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(code, encoding="utf-8")
    return str(path.resolve())


# ── Main Code Functions ───────────────────────────────────────────────────────

def write_code(description: str, language: str = "python", save_to: str = None) -> str:
    """
    Generate code based on a description using Claude.

    Args:
        description: What the code should do
        language:    Programming language (default: python)
        save_to:     Optional file path to save the generated code

    Returns:
        Generated code as a string (with save confirmation if applicable)
    """
    prompt = (
        f"Write {language} code that does the following:\n\n"
        f"{description}\n\n"
        f"Requirements:\n"
        f"- Write clean, well-commented, production-quality code\n"
        f"- Include error handling where appropriate\n"
        f"- Add a brief explanation before the code block\n"
        f"- Wrap the code in a proper ```{language} code block"
    )

    response = ask(prompt)

    # Auto-save if path provided
    if save_to:
        blocks = _extract_code_blocks(response)
        if blocks:
            _, code = blocks[0]
            saved_path = _save_code_to_file(code, save_to)
            response += f"\n\n✅ Code saved to: `{saved_path}`"
        else:
            response += "\n\n⚠️ Could not extract code block to save."
    else:
        # Suggest default save location
        CODE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        blocks = _extract_code_blocks(response)
        if blocks and not save_to:
            ext_map = {
                "python": "py", "javascript": "js", "typescript": "ts",
                "java": "java", "cpp": "cpp", "c": "c", "rust": "rs",
                "go": "go", "html": "html", "css": "css", "sql": "sql",
                "bash": "sh", "powershell": "ps1", "r": "r",
            }
            lang_key = blocks[0][0].lower()
            ext = ext_map.get(lang_key, "txt")
            response += f"\n\n💡 *Tip: Say 'save that to filename.{ext}' to save the code.*"

    return response


def debug_code(code: str, error_message: str = None, language: str = None) -> str:
    """
    Debug provided code, optionally with an error message.

    Args:
        code:          The code to debug
        error_message: The error/traceback (optional)
        language:      Programming language (auto-detected if not provided)

    Returns:
        Debugging analysis and corrected code
    """
    error_section = ""
    if error_message:
        error_section = f"\n\nError/Traceback:\n```\n{error_message}\n```"

    prompt = (
        f"Debug the following code and provide a corrected version:\n\n"
        f"```{language or ''}\n{code}\n```"
        f"{error_section}\n\n"
        f"In your response:\n"
        f"1. Identify what's wrong and why\n"
        f"2. Provide the corrected code in a proper code block\n"
        f"3. Briefly explain what you changed\n"
        f"Be direct and concise."
    )

    return ask(prompt)


def explain_code(code: str, detail_level: str = "concise") -> str:
    """
    Explain what a piece of code does.

    Args:
        code:         The code to explain
        detail_level: "concise" or "detailed"

    Returns:
        Natural language explanation of the code
    """
    if detail_level == "detailed":
        instruction = (
            "Provide a detailed explanation covering:\n"
            "1. Overall purpose\n"
            "2. Line-by-line or block-by-block walkthrough\n"
            "3. Any important patterns, algorithms, or gotchas\n"
            "4. Potential improvements"
        )
    else:
        instruction = (
            "Provide a concise explanation covering:\n"
            "1. What this code does (1-2 sentences)\n"
            "2. Key logic or notable patterns\n"
            "Keep it under 150 words."
        )

    prompt = (
        f"Explain the following code:\n\n"
        f"```\n{code}\n```\n\n"
        f"{instruction}"
    )

    return ask(prompt)


def save_last_code(response_text: str, filepath: str) -> str:
    """
    Extract code from a previous JARVIS response and save it to a file.

    Args:
        response_text: The previous JARVIS response containing code
        filepath:      Where to save the file

    Returns:
        Confirmation message with saved path
    """
    blocks = _extract_code_blocks(response_text)

    if not blocks:
        # Try to save the raw text if no code blocks found
        saved = _save_code_to_file(response_text, filepath)
        return f"Saved text to `{saved}`, sir."

    _, code = blocks[0]  # Take first code block
    saved = _save_code_to_file(code, filepath)
    return f"Code saved to `{saved}`, sir."


def optimize_code(code: str, language: str = None) -> str:
    """
    Suggest optimizations and improvements for existing code.

    Args:
        code:     Code to optimize
        language: Programming language (optional)

    Returns:
        Optimized code with explanation of changes
    """
    prompt = (
        f"Optimize and improve the following code:\n\n"
        f"```{language or ''}\n{code}\n```\n\n"
        f"Focus on:\n"
        f"- Performance improvements\n"
        f"- Better readability\n"
        f"- Best practices and idioms\n"
        f"- Error handling\n"
        f"Provide the optimized version in a code block with a brief changelog."
    )
    return ask(prompt)


def generate_tests(code: str, framework: str = None, language: str = "python") -> str:
    """
    Generate unit tests for provided code.

    Args:
        code:      The code to test
        framework: Test framework (e.g., "pytest", "jest", "junit")
        language:  Programming language

    Returns:
        Generated test code
    """
    fw_hint = f"using {framework}" if framework else "using the standard testing framework"
    prompt = (
        f"Write unit tests {fw_hint} for the following {language} code:\n\n"
        f"```{language}\n{code}\n```\n\n"
        f"Include tests for:\n"
        f"- Normal/expected inputs\n"
        f"- Edge cases\n"
        f"- Error conditions\n"
        f"Make the tests comprehensive and runnable."
    )
    return ask(prompt)
