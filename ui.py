"""
Structure of box:
+----------+---------------+
| option 1 | description 1 |
| option 2 | description 2 |
| ...      | ...           |
+----------+---------------+
"""


def get_int(max_val, message="Enter an integer: "):
    while True:
        try:
            return int(input(message))
        except ValueError:
            print("Invalid input. Please enter an integer between 0 and " + str(max_val) + ".")


def display_options(options, descriptions, desc_length=None):
    options = [str(option) for option in options]
    descriptions = [str(description) for description in descriptions]
    max_option_length = max(len(opt) for opt in options)
    max_description_length = max(len(desc) for desc in descriptions)
    if desc_length is not None:
        max_description_length = desc_length
    border_str = f"+-{'-' * max_option_length}-+-{'-' * max_description_length}-+"

    print(border_str)
    for item in zip(options, descriptions):
        print(f"| {item[0].ljust(max_option_length)} | {item[1].ljust(max_description_length)} |")

    print(border_str)
