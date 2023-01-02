from svgdiagram.elements.svg import Svg

import inspect

import os


SAVE_MISMATCH_TO = ''
OVERRIDE = False
INDENT_COUNT = 2
REFERENCE_LOCATION_ROOT = os.path.join(
    os.path.dirname(__file__), 'expected_svgs')


def assert_equal_svg(actual_svg):
    if not isinstance(actual_svg, Svg):
        actual_svg = Svg(children=actual_svg)

    parent_stack = inspect.stack()[1]
    file_name = parent_stack.filename.split('/tests/')[-1][:-3]
    func_name = parent_stack.function

    file_path = os.path.join(REFERENCE_LOCATION_ROOT, file_name)
    if not os.path.isdir(file_path):
        os.makedirs(file_path)
    expected_svg_file_name = os.path.join(file_path, f'{func_name}.svg')

    actual_svg_content = actual_svg.create_svg_text(indent_count=INDENT_COUNT)

    if not os.path.isfile(expected_svg_file_name) or OVERRIDE:
        with open(expected_svg_file_name, 'w') as f:
            f.write(actual_svg_content)

    with open(expected_svg_file_name, 'r') as f:
        expected_svg_content = f.read()

    svg_matches = expected_svg_content == actual_svg_content

    if SAVE_MISMATCH_TO and not svg_matches:
        missmatch_path = os.path.join(SAVE_MISMATCH_TO, file_name)
        if not os.path.isdir(missmatch_path):
            os.makedirs(missmatch_path)
        missmatch_file_name = os.path.join(missmatch_path, f'{func_name}.html')

        with open(missmatch_file_name, 'w') as f:
            f.write(f"""
            <html>
                <body>
                    <table>
                        <tr>
                            <th>Expected<th>
                            <th>Actual<th>
                        </tr>
                        <tr>
                            <td>{expected_svg_content}</td>
                            <td>{actual_svg_content}</td>
                        </tr>
                    </table>
                </body>
            </html>
            """)

    assert svg_matches
