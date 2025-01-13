import os
import json
import numpy as np

class Recipe:
    def __init__(self, ins, outs, machine):
        self.ins = ins
        self.outs = outs
        self.machine = machine

# load recipes from file: recipes.json

if not os.path.exists("recipes.json"):
    with open("recipes.json", "w") as f:
        f.write("{\n\t\"base_items\" : [\n\t\n\t],\n\t\"recipes\" : [\n\t\n\t]\n}")

json_data = json.load(open("recipes.json", "r"))

base_items = json_data["base_items"]
recipe_unformatted = json_data["recipes"]

recipes = []
for recipe in recipe_unformatted:
    recipes.append(Recipe(recipe[0], recipe[1], recipe[2]))


def search_recipes(query):
    possible_recipes = []
    for recipe in recipes:
        for item in recipe.outs.keys():
            if item == query:
                possible_recipes.append(recipe)

    return possible_recipes


def add_recipe(recipe):
    recipes.append(recipe)


def save_recipes():
    formatted_recipes = []
    for recipe in recipes:
        formatted_recipes.append([recipe.ins, recipe.outs, recipe.machine])

    with open("recipes.json", "w") as f:
        json.dump({"base_items": base_items, "recipes": formatted_recipes}, f, indent=4)

def add_recipe_prompt(req_item):
    db_dialog = input(f"{req_item} not found in recipe database. Add it to db? [Y/N]: ")
    if db_dialog[0] == "Y" or db_dialog[0] == "y":
        print("\x1b[1m\x1b[3mNOTE: \x1b[23mThe amount of a certain fluid should be inputted as the amount of millibuckets or liters required. Example: 144 millibuckets / 144L or redstone alloy should be inputted as Redstone Alloy x144\x1b[0m")
        inputs = input(f"Enter inputs to make {req_item} separated by commas (Example: Resistor x2, Steel Casing x1, etc., Type 'raw' to mark it as a raw material): ")
        if inputs == "raw":
            base_items.append(req_item)
            return

        outputs = input("Enter outputs separated by commas (Example: Electronic Circuit x1, etc.): ")
        machine = input(f"Enter machine in which {req_item} is made: ")

        input_items = []
        input_amounts = []
        for inp in inputs.split(", "):
            inp_split = inp.split(" x")
            input_items.append(inp_split[0])
            input_amounts.append(int(inp_split[1]))

        output_items = []
        output_amounts = []
        for out in outputs.split(", "):
            out_split = out.split(" x")
            output_items.append(out_split[0])
            output_amounts.append(int(out_split[1]))

        inputs_formatted = dict(zip(input_items, input_amounts))
        outputs_formatted = dict(zip(output_items, output_amounts))

        add_recipe(Recipe(inputs_formatted, outputs_formatted, machine))



def change_recipe(recipe_num):
    print(
        "\x1b[1m\x1b[3mNOTE: \x1b[23mThe amount of a certain fluid should be inputted as the amount of millibuckets or liters required. Example: 144 millibuckets / 144L or redstone alloy should be inputted as Redstone Alloy x144\x1b[0m")
    inputs = input("New recipe inputs (Example: Resistor x2, Steel Casing x1, etc.): ")
    outputs = input("New recipe outputs (Example: Electronic Circuit x1, etc.): ")
    machine = input("New recipe machine: ")

    input_items = []
    input_amounts = []
    for inp in inputs.split(", "):
        inp_split = inp.split(" x")
        input_items.append(inp_split[0])
        input_amounts.append(int(inp_split[1]))

    output_items = []
    output_amounts = []
    for out in outputs.split(", "):
        out_split = out.split(" x")
        output_items.append(out_split[0])
        output_amounts.append(int(out_split[1]))

    inputs_formatted = dict(zip(input_items, input_amounts))
    outputs_formatted = dict(zip(output_items, output_amounts))

    recipes[recipe_num] = Recipe(inputs_formatted, outputs_formatted, machine)

def get_recipe_str(recipe, recursion_level, scale):
    output_str = ""

    # string for output items
    for i in range(len(recipe.outs)):
        output_temp = ""
        if i > 0:  # multiple items
            output_temp += ", "

        output_temp += f"{list(recipe.outs.keys())[i]} x{list(recipe.outs.values())[i] * scale}"
        output_str += output_temp

    input_str = ""
    input_item_array = list(recipe.ins.keys())

    # string for needed items
    for i in range(len(recipe.ins)):

        # initialise string
        output_temp = ""
        if i > 0:  # multiple items, so multiple lines
            output_temp += "\n"

        current_item = input_item_array[i]

        # recursion
        if current_item in base_items:
            # base item, has no recipe
            output_temp += " " * recursion_level * 4 + f"{current_item} x{list(recipe.ins.values())[i] * scale}"

        elif search_recipes(current_item):
            # has recipe
            new_recipe = search_recipes(current_item)[0]
            new_recipe_amount = list(new_recipe.outs.values())[0]
            output_temp += " " * recursion_level * 4 + get_recipe_str(new_recipe, recursion_level + 1, int(np.ceil(scale / new_recipe_amount)))

        else:
            # no recipe, not base item
            add_recipe_prompt(current_item)
            output_temp += " " * recursion_level * 4 + f"{current_item} x{list(recipe.ins.values())[i] * scale}"
            pass
        input_str += output_temp

    return f"{output_str}: {recipe.machine}\n" + f"{input_str}"


def main():
    # TODO: ability to change recipe

    while True:
        request = input("Item x Amount (Example: Electronic Circuit x5. Type change to change a recipe, exit to exit): ")
        if request == "exit":
            break

        req_item = request.split(" x")[0]
        req_amount = int(request.split(" x")[1])

        # checks if item is in recipe db
        results = search_recipes(req_item)

        if results:
            # item is in recipe db, so it outputs the recipe
            recipe = results[0]
            print(get_recipe_str(recipe, 1, req_amount) + "\n")
        else:
            # prompts user to add item to recipe db
            add_recipe_prompt(req_item)

        save_recipes()

    save_recipes()



if __name__ == '__main__':
    main()
