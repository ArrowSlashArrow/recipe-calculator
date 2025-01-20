import os
import json

# +---+---------------------------------------------------------------+
# | 0 |  {Item1: amount1, etc.} -[Machine]-> {output1: amount1, etc.} |
# |...| ...                                                           |
# +---+---------------------------------------------------------------+
# TODO: refactor whole thing with flowchart
# TODO: ability to pick from multiple recipes when crafting
# TODO: multiple recipe dbs for different mods/versions
# TODO: rephrase prompts to be more user friendly (maybe add a user guide)
# TODO: commands (ls, exit, etc.)
# COMMANDS
# ls - list recipes
# change - change recipe
# flush - flush recipe db (clear)
# exit - exit program
# help - print help (commands message)
# export - export prev recipe str to file
# rmb - remove base item
# rmr - remove recipe
# swdb - switch recipe db

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
        f.write("{\n\t\"base_items\" : [\n\t\n\t],\n\t\"recipes\" : [\n\t\n\t]\n}")

# load recipes from file: recipes.json
json_data = json.load(open("recipes.json", "r"))
base_items = json_data["base_items"]
raw_recipes = json_data["recipes"]

# format recipes into a list of Recipe objects
recipes = []
for recipe in raw_recipes:
    recipes.append(Recipe(recipe[0], recipe[1], recipe[2]))

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


def format_dict(dictionary):
    # format dictionary with list comprehension
    return ''.join(f"{key} x{value}, " for key, value in dictionary.items())


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

        # parse inputs
        input_items = []
        input_amounts = []
        for inp in inputs.split(", "):
            # split each input item into item str and amount
            inp_split = inp.split(" x")
            input_items.append(inp_split[0])  # item
            input_amounts.append(int(inp_split[1]))  # amount

        # parse outputs
        output_items = []
        output_amounts = []
        for out in outputs.split(", "):
            # split each output item into item str and amount
            out_split = out.split(" x")
            output_items.append(out_split[0])  # item
            output_amounts.append(int(out_split[1]))  # amount

        # format inputs and outputs into dictionaries
        inputs_formatted = dict(zip(input_items, input_amounts))
        outputs_formatted = dict(zip(output_items, output_amounts))

        # add the recipe
        add_recipe(Recipe(inputs_formatted, outputs_formatted, machine))


def change_recipe_dialog():
    # TODO: print all recipes in box dialog

    recipe_num = input("[TODO: print all recipes in box dialog]\nRecipe number: ")
    change_recipe_prompt(int(recipe_num))


def change_recipe_prompt(recipe_num):
    # info message
    print(
        "\x1b[1m\x1b[3mNOTE: \x1b[23mThe amount of a certain fluid should be inputted as the amount of millibuckets "
        "or liters required. Example: 144 millibuckets / 144L or redstone alloy should be inputted as Redstone Alloy "
        "x144\x1b[0m")

    # get user input
    inputs = input("New recipe inputs (Example: Resistor x2, Steel Casing x1, etc.): ")
    outputs = input("New recipe outputs (Example: Electronic Circuit x1, etc.): ")
    machine = input("New recipe machine: ")

    # parse input
    input_items = []
    input_amounts = []
    for inp in inputs.split(", "):
        inp_split = inp.split(" x")
        input_items.append(inp_split[0])
        input_amounts.append(int(inp_split[1]))

    # parse outputs
    output_items = []
    output_amounts = []
    for out in outputs.split(", "):
        out_split = out.split(" x")
        output_items.append(out_split[0])
        output_amounts.append(int(out_split[1]))

    # format inputs and outputs into dictionaries
    inputs_formatted = dict(zip(input_items, input_amounts))
    outputs_formatted = dict(zip(output_items, output_amounts))

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
        # initialise string
        output_temp = ""
        if i > 0:  # if there are multiple items, add a comma in between them
            output_temp += f", "

        # add item and amount to string
        output_str += f"{prev_colour}{prev_bg}{output_items[i]} x{output_amounts[i] * scale}: {req_recipe.machine}{reset_colour}"


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


def main():
    # i don't like global vars but whatever
    global raw_requiredmd
    while True:
        request = input(
            "Item x Amount (Example: Electronic Circuit x5. Type change to change a recipe, exit to exit): ")
        if request == "exit":
            break

        elif request == "change":
            change_recipe_dialog()
            continue

        req_item = request.split(" x")[0]
        req_amount = 1 if " x" not in request else int(request.split(" x")[1])

        # checks if item is in recipe db
        results = search_recipes(req_item)

        if results:  # if item is in recipe db:
            # get the first recipe
            req_recipe = results[0]
            # get string for recipe and raw materials
            req_recipe_str = get_recipe_str(req_recipe, 1, req_amount)
            raw_required_str = f"\x1b[1m{format_dict(raw_required)}\b\b"

            # print formatted output
            print(f"{reset_colour}{req_recipe_str}\n{reset_colour}")
            print(f"Raw materials required to craft {req_item} x{req_amount}: {raw_required_str} {reset_colour}")
        else:  # if item is not in recipe db:
            # prompts user to add item to recipe db
            add_recipe_prompt(req_item)

        save_recipes()

        # reset raw_required dict
        raw_required = {}

    save_recipes()


if __name__ == '__main__':
    main()
