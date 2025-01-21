import os
import json
import re
from ui import *

# +---+---------------------------------------------------------------+
# | 0 |  {Item1: amount1, etc.} -[Machine]-> {output1: amount1, etc.} |
# |...| ...                                                           |
# +---+---------------------------------------------------------------+
# TODO: refactor whole thing with flowchart
# TODO: ability to pick from multiple recipes when crafting
# TODO: multiple recipe dbs for different mods/versions
# TODO: rephrase prompts to be more user friendly + user guide in readme
# TODO: handle recursion limit
#  --> if a recipe loops back on itself, it will recurse infinitely, and will eventually trigger a RecursionError
# TODO: scraper, so that recipes can be added automatically
# TODO: input validation



# regular expression to remove ansi codes
ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
# matches: [esc]\[ + any digit or ; + any number of those characters + m

# recipe struct
class Recipe:
    def __init__(self, ins, outs, machine):
        self.ins = ins
        self.outs = outs
        self.machine = machine


# load recipes from file: recipes.json
# creates not recipes.json if it doesn't exist
if not os.path.exists("recipes.json"):
    with open("recipes.json", "w") as f:
        # write template string to recipes file (indented)
        template = """
        {
            "base_items" : [

            ],
            "recipes" : [

            ]
        }
        """
        json.dump(json.loads(template), f, indent=4)

# create exports folder
if not os.path.isdir("exports"):
    os.mkdir("exports")

# colours for text formatting
reset_colour = "\x1b[0m"
# gradient of background colours for recipe output
text_colours = [232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243,
                244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255]

# array that keeps track of raw materials required to craft an item
raw_required = {}


# exists solely to remove numpy dependency
def ceil(num):
    if float(num).is_integer():
        return int(num)
    else:
        return int(num + 1)


# returns a list of recipes that can produce the query item
def search_recipes(query):
    # list is used for multiple return values
    possible_recipes = []

    # loop through all recipes
    for recipe in recipes:
        # loop through hall output items
        # O(n²), could be slow with large files
        for item in recipe.outs.keys():
            # does the output item match the query item?
            if item.lower() == query.lower():
                # if so, add recipe to list
                possible_recipes.append(recipe)

    return possible_recipes


def add_recipe(additional_recipe):
    # add recipe to db and save it
    recipes.append(additional_recipe)
    save_recipes()


def save_recipes():
    # format recipes list into JSON-able list
    formatted_recipes = []
    for recipe in recipes:
        formatted_recipes.append([recipe.ins, recipe.outs, recipe.machine])

    # write base items and formatted recipes to recipes file
    # this overwrites the whole file, could perform poorly with large files
    with open("recipes.json", "w") as recipes_file:
        json.dump({"base_items": base_items, "recipes": formatted_recipes}, recipes_file, indent=4)


def load_recipes(recipes_file):
    # if trying to load a non-existent file, prompt to create it

    # load recipes from file: recipes.json
    json_data = json.load(open(recipes_file, "r"))
    base_items = json_data["base_items"]
    raw_recipes = json_data["recipes"]

    # format recipes into a list of Recipe objects
    recipes = []
    for recipe in raw_recipes:
        recipes.append(Recipe(recipe[0], recipe[1], recipe[2]))

    return base_items, recipes


def format_dict(dictionary):
    # format dictionary with list comprehension
    return ''.join(f"{key} x{value}, " for key, value in dictionary.items()) + "\b\b"


def str_into_dict(string):
    items = []
    amounts = []
    for item in string.split(", "):
        item_split = item.split(" x")
        items.append(item_split[0])
        amounts.append(int(item_split[1]))

    return dict(zip(items, amounts))

def add_recipe_prompt(req_item):
    db_dialog = input(f"{req_item} not found in recipe database. Add it to db? [Y/N]: ") + " "
    # if first char of input is y, add item to db
    if db_dialog[0].lower() == "y":

        # print information
        print("\n\x1b[1m\x1b[3mNOTE: \x1b[23mThe amount of a certain fluid should be inputted as the amount of "
              "millibuckets or liters required")
        print("For example: 144 millibuckets / 144L or redstone alloy should be inputted as Redstone Alloy x144\x1b[0m")

        # get inputs
        inputs = input(f"Enter inputs to make {req_item} separated by commas. Type raw to mark it as a raw material: ")

        # mark as raw material if input is "raw"
        if inputs == "raw":
            base_items.append(req_item)
            return

        # otherwise, get outputs and machine
        outputs = input("Enter outputs separated by commas (Example: Electronic Circuit x1, etc.): ")
        machine = input(f"Enter machine in which {req_item} is made: ")

        inputs_formatted = str_into_dict(inputs)
        outputs_formatted = str_into_dict(outputs)

        # add the recipe
        add_recipe(Recipe(inputs_formatted, outputs_formatted, machine))


def change_recipe_dialog():
    print_recipes()
    recipe_num = get_int(len(recipes), "Recipe number: ")
    change_recipe_prompt(recipe_num)


def change_recipe_prompt(recipe_num):
    original_inputs = recipes[recipe_num].ins
    original_outputs = recipes[recipe_num].outs
    original_machine = recipes[recipe_num].machine
    print(f"Original recipe: {format_dict(original_inputs)} -[ {original_machine} ]-> {format_dict(original_outputs)}")

    # info message
    print(
        "\x1b[1m\x1b[3mNOTE: \x1b[23mThe amount of a certain fluid should be inputted as the amount of millibuckets "
        "or liters required. Example: 144 millibuckets / 144L or redstone alloy should be inputted as Redstone Alloy "
        "x144\x1b[0m")

    # get user input
    inputs = input("New recipe inputs (Example: Resistor x2, Steel Casing x1, etc.) Type raw to mark it as a raw material: ")
    if inputs == "raw":
        base_items.append(inputs)
        recipes.pop(recipe_num)
        return

    outputs = input("New recipe outputs (Example: Electronic Circuit x1, etc.): ")
    machine = input("New recipe machine: ")

    # format inputs and outputs into dictionaries
    inputs_formatted = str_into_dict(inputs)
    outputs_formatted = str_into_dict(outputs)

    # commit changes
    recipes[recipe_num] = Recipe(inputs_formatted, outputs_formatted, machine)


def get_recipe_str(req_recipe, recursion_level, scale):
    global raw_required

    # initialise strings
    input_str = ""
    output_str = ""
    indent = " " * recursion_level * 4

    # initialise colours
    text_bg_index = recursion_level % len(text_colours)
    prev_bg_index = (recursion_level - 1) % len(text_colours)
    text_bg = f"\x1b[48;5;{text_colours[text_bg_index]}m"
    prev_bg = f"\x1b[48;5;{text_colours[prev_bg_index]}m"
    text_colour = '\x1b[38;5;255m' if text_colours[text_bg_index] < 244 else '\x1b[38;5;232m'
    prev_colour = '\x1b[38;5;255m' if text_colours[text_bg_index] < 244 else '\x1b[38;5;232m'

    # arrays for input and output items and amounts
    input_items = list(req_recipe.ins.keys())
    input_amounts = list(req_recipe.ins.values())
    output_items = list(req_recipe.outs.keys())
    output_amounts = list(req_recipe.outs.values())

    # string for output items
    for i in range(len(req_recipe.outs)):
        # add item and amount to string
        output_str += (", " if i > 0 else "") + f"{prev_colour}{prev_bg}{output_items[i]} x{output_amounts[i] * scale}"

    output_str += f": {req_recipe.machine}{reset_colour}"


    # string for input items
    for i in range(len(req_recipe.ins)):

        # initialise string
        input_temp = f"\n{text_colour}{text_bg}{indent}" if i > 0 else f"{text_colour}{text_bg}{indent}"
        current_item = input_items[i]

        # base item, has no recipe
        if current_item in base_items:
            amount = input_amounts[i] * scale
            input_temp += f"{current_item} x{amount}"

            # add to raw required
            if current_item in raw_required:
                raw_required[current_item] += amount
            else:
                raw_required[current_item] = amount
        # has recipe
        elif search_recipes(current_item):
            # get recipe of needed item
            new_recipe = search_recipes(current_item)[0]
            # get amount of item needed recipe produces
            new_recipe_amount = list(new_recipe.outs.values())[0] * scale
            # get amount needed for this recipe
            recipe_amount = input_amounts[i] * scale
            # calculate scale of needed recipe
            new_recipe_scale = ceil(recipe_amount * scale / new_recipe_amount)

            # add recipe string to output
            input_temp += get_recipe_str(new_recipe, recursion_level + 1, new_recipe_scale)
        # no recipe, not base item
        else:
            # prompt for recipe
            add_recipe_prompt(current_item)

            # add to recipe str (no recipe)
            current_item_amount = input_amounts[i] * scale
            input_temp += f"{current_item} x{current_item_amount}"

        # add line to input_str
        # side note: apparently the colours weren't being drawn correctly after the text, so they are just cut off
        # i couldn't find a solution for this either, so if anyone comes up with one, make a PR
        input_str += input_temp + reset_colour

    return f"{output_str}\n{input_str}"


def print_recipes():
    print("Recipes:")
    options = [str(option) for option in list(range(len(recipes)))]
    input_strs = [format_dict(recipe.ins) for recipe in recipes]
    machines = [recipe.machine for recipe in recipes]
    output_strs = [format_dict(recipe.outs) for recipe in recipes]

    max_input_length = max(len(inp) for inp in input_strs)
    max_machine_length = max(len(mach) for mach in machines)
    max_output_length = max(len(out) for out in output_strs)

    descriptions = [f"{item[0]:>{max_input_length}} -[ {item[1]:^{max_machine_length}} ]-> {item[2]:<{max_output_length}}" for item in zip(input_strs, machines, output_strs)]

    display_options(options, descriptions, max(len(item) for item in descriptions) - 8, '0')


def print_base_items():
    print("Raw materials:")
    options = list(range(len(base_items)))
    descriptions = base_items
    display_options(options, descriptions)


def remove_base_item():
    print_base_items()
    item_num = get_int(len(base_items), "Type the number corresponding to the raw material you want to remove: ")
    # remove chosen item
    base_items.pop(item_num)


def remove_recipe():
    print_recipes()
    item_num = get_int(len(recipes), "Type the number corresponding to the recipe you want to remove: ")
    # remove chosen recipe
    recipes.pop(item_num)


def export_recipe_str(recipe_str):
    file_name = input("Enter the name of the file to export to: ")
    # remove ansi codes
    clean_str = ansi_escape.sub('', recipe_str)
    with open(f"exports/{file_name}.txt", "w") as output_file:
        output_file.write(clean_str)


def main():
    # i don't like global vars but whatever
    global raw_required, base_items, recipes

    base_items, recipes = load_recipes("recipes.json")

    prev_output_str = ""
    while True:
        request = input(
            "Item x Amount (Example: Electronic Circuit x5). Type help for a list of commands: ")

        # COMMANDS
        # ls - list recipes: done
        # change - change recipe: done
        # flush - flush recipe db (clear): done
        # exit - exit program: done
        # help - print help (commands message): done
        # export - export prev recipe str to file
        # rmb - remove base item: done
        # rmr - remove recipe: done
        # sdb - switch recipe db

        match request:
            case "ls":
                print_recipes()
                continue
            case "change":
                change_recipe_dialog()
                continue
            case "flush":
                base_items = []
                recipes = []
                continue
            case "exit":
                break
            case "help":
                commands = ["ls", "change", "flush", "exit", "help", "export", "rmb", "rmr"]
                descriptions = ["List all recipes", "Change a recipe", "Clear recipes and raw items", "Exit program",
                                "Print this help message", "Export the previous recipe string to a file",
                                "Remove a base item", "Remove a recipe"]

                display_options(commands, descriptions)
                continue
            case "export":
                export_recipe_str(prev_output_str[:-4])
                continue
            case "rmb":
                remove_base_item()
                continue
            case "rmr":
                remove_recipe()
                continue
            case "sdb":
                pass  # maybe add this in the distant future
            case _:
                req_item = request.split(" x")[0]
                req_amount = 1 if " x" not in request else int(request.split(" x")[1])

                # checks if item is in recipe db
                results = search_recipes(req_item)

                if results:  # if item is in recipe db:
                    # get the first recipe
                    req_recipe = results[0]
                    # get string for recipe and raw materials
                    req_recipe_str = get_recipe_str(req_recipe, 1, req_amount)
                    raw_required_str = f"\x1b[1m{format_dict(raw_required)}"

                    recipe_out_str = f"{reset_colour}{req_recipe_str}\n{reset_colour}"
                    raw_out_str = f"Raw materials required to craft {req_item} x{req_amount}: {raw_required_str} {reset_colour}"
                    # print formatted output
                    output_str = f"{recipe_out_str}\n{raw_out_str}"
                    print(output_str)

                    prev_output_str = output_str
                else:  # if item is not in recipe db:
                    # prompts user to add item to recipe db
                    add_recipe_prompt(req_item)

                save_recipes()

                # reset raw_required dict
                raw_required = {}

    save_recipes()


if __name__ == '__main__':
    main()
