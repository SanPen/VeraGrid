from pathlib import Path
import sys


def add_mathjax(html_text: str) -> str:
    """
    Add MathJax support to one Sphinx HTML page.

    :param html_text: Original HTML page text.
    :return: HTML page text with the MathJax loader present.
    """
    marker: str = "</head>"
    loader_url: str = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"

    # Avoid injecting MathJax twice when the script is re-run locally or by CI.
    if loader_url in html_text:
        updated_text: str = html_text
    else:
        # Wrap Sphinx's raw span.math content in MathJax delimiters before MathJax renders the page.
        script: str = (
            '<script>window.MathJax={startup:{pageReady:function(){'
            'document.querySelectorAll("span.math").forEach(function(e){'
            'var p=e.parentElement;var d=false;if(p){var g=p.parentElement;if(g){d=g.classList.contains("math");}}'
            'var t=e.textContent;if(t.slice(0,2)!=="\\\\("){if(t.slice(0,2)!=="\\\\["){'
            'e.textContent=(d?"\\\\["+t+"\\\\]":"\\\\("+t+"\\\\)");}}});'
            'return MathJax.startup.defaultPageReady();}}};</script>'
            '<script defer src="' + loader_url + '"></script>'
        )

        # Insert before the HTML head closes so MathJax is configured before loading.
        if marker in html_text:
            updated_text = html_text.replace(marker, script + marker, 1)
        else:
            updated_text = html_text

    return updated_text


def patch_html_file(html_file: Path) -> bool:
    """
    Patch one HTML file in place.

    :param html_file: HTML file to patch.
    :return: True when the file was changed, False otherwise.
    """
    # Read the generated page exactly as Sphinx emitted it.
    original_text: str = html_file.read_text(encoding="utf-8")
    updated_text: str = add_mathjax(original_text)

    # Write only changed files to keep rebuilds and local diffs quieter.
    if updated_text != original_text:
        html_file.write_text(updated_text, encoding="utf-8")
        changed: bool = True
    else:
        changed = False

    return changed


def inject_mathjax(html_dir: Path) -> int:
    """
    Inject MathJax into every copied HTML page.

    :param html_dir: Root directory containing the HTML pages copied for Read the Docs.
    :return: Process exit code.
    """
    if html_dir.is_dir():
        html_files: list[Path] = list(html_dir.rglob("*.html"))
        changed_count: int = 0

        # Walk every page because formulas can appear anywhere in the generated docs.
        for html_file in html_files:
            changed: bool = patch_html_file(html_file)
            if changed:
                changed_count += 1
            else:
                changed_count = changed_count

        print(f"Injected MathJax into {changed_count} HTML files.")
        exit_code: int = 0
    else:
        print(f"HTML directory not found: {html_dir}", file=sys.stderr)
        exit_code = 1

    return exit_code


def main(argv: list[str]) -> int:
    """
    Run the MathJax injection command.

    :param argv: Command-line arguments including the script name.
    :return: Process exit code.
    """
    if len(argv) == 2:
        html_dir: Path = Path(argv[1])
        exit_code: int = inject_mathjax(html_dir)
    else:
        print("Usage: python doc/inject_mathjax.py HTML_DIR", file=sys.stderr)
        exit_code = 2

    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
