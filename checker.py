import argparse
import requests
import json
import os
import codecs
import time


# Arguments

parser = argparse.ArgumentParser(description = "MTG Card Price Checker")
parser.add_argument('filenames', nargs = '*',
                    help = 'csv files containing collections of cards')

parser.add_argument('-u', '--update-files', help = "update the files, puts card prices in the given files",
                    action = 'store_true', dest = 'update_files')
parser.add_argument('-o', '--output-files', help = "output new files (in cwd) containing card names, quantities and prices",
                    action = 'store_true', dest = 'output_files')
parser.add_argument('-p', '--print-only', help = "don't check for prices online, simply check the prices currently stored in the files",
                    action = 'store_true', dest = 'print_only')
parser.add_argument('-a', '--all-cards', help = "print the prices of all cards in the collection",
                    action = 'store_true', dest = 'print_all')


# Global variables

delimiter = ';'


def get_card_price(card_name):
    url = "https://api.scryfall.com/cards/named?exact=" + card_name
    response = requests.get(url)
    
    if response.status_code == 404:
        raise NameError("Card \"{}\" could not be found!".format(card_name))
    
    data = json.loads(response.content)
    price = data["prices"]["eur"]
    if price == None:
        price = 0
    return float(price)


def read_collection(filename):
    current_dir = os.getcwd()
    absolute_path = os.path.join(current_dir, filename)
    
    if not os.path.exists(absolute_path):
        raise FileNotFoundError("File \"{}\" could not be found!".format(filename))

    # File format:
    # <name><delimiter><quantity>\n
    # <name><delimiter><quantity>\n
    # ...
    
    collection = []
    file = codecs.open(absolute_path, 'r', 'utf-8')

    for index, line in enumerate(file):
        stripped_line = line.strip()
        segments = stripped_line.split(delimiter)
        if len(segments) < 2 or not segments[1].isnumeric():
            raise ValueError("Wrong text format! (line: {})\nLine: \"{}\"\n" \
                             "Needs to be: \"<card name>{}<card quantity>\""
                             .format(index + 1, stripped_line, delimiter))
        collection.append({ "name" : segments[0],
                            "quantity" : int(segments[1]) })

    file.close()

    return collection


def read_collection_priced(filename):
    current_dir = os.getcwd()
    absolute_path = os.path.join(current_dir, filename)

    if not os.path.exists(absolute_path):
        raise FileNotFoundError("File \"{}\" could not be found!".format(filename))

    # File format:
    # <name><delimiter><quantity><delimiter><price>
    # <name><delimiter><quantity><delimiter><price>
    # ...

    collection = []
    file = codecs.open(absolute_path)

    for index, line in enumerate(file):
        stripped_line = line.strip()
        segments = stripped_line.split(delimiter)
        if len(segments) < 3 or not segments[1].isnumeric():
            raise ValueError("Wrong text format! (line: {})\n Line: \"{}\"\n" \
                             "Needs to be: \"<card name>{}<card quantity>{}<card price>\""
                             .format(index + 1, stripped_line, delimiter, delimiter))
        try:
            price = float(segments[2])
        except ValueError:
            price = segments[2]
        
        collection.append({ "name" : segments[0],
                            "quantity" : int(segments[1]),
                            "price": price})

    file.close()

    return collection


def write_collection(filename, collection):
    current_dir = os.getcwd()
    absolute_path = os.path.join(current_dir, filename)

    file = codecs.open(absolute_path, 'w', 'utf-8')

    for card in collection:
        if isinstance(card["price"], str):
            full_price = card["price"]
            file.write("{}{}{}{}{}{}{}\n".format(card["name"], delimiter,
                                                 card["quantity"], delimiter,
                                                 card["price"], delimiter,
                                                 full_price))
        else:
            # Computers are bad at decimals, so we should make the price a natural number
            # before the multiplication, and return it to normal after
            full_price = (card["price"] * 100) * card["quantity"] / 100
        
            file.write("{}{}{}{}{:.2f}{}{:.2f}\n".format(card["name"], delimiter,
                                                         card["quantity"], delimiter,
                                                         card["price"], delimiter,
                                                         full_price))

    file.close()


def output_collection(filename, collection):
    current_dir = os.getcwd()
    absolute_path = os.path.join(current_dir, filename)

    if os.path.exists(absolute_path):
        raise FileExistsError("File {} already exists".format(filename))

    write_collection(filename, collection)


def calculate_total(collection):
    total = 0.0
    for card in collection:
        if not isinstance(card["price"], str):
            total += card["price"] * 100 * card["quantity"]
    return total / 100


def print_collection(collection):
    column_widths = { "name" : 9,
                      "quantity" : 3,
                      "price" : 5,
                      "total" : 5}
    for card in collection:
        if not isinstance(card["price"], str):
            card["total"] = card["price"] * 100 * card["quantity"] / 100
        else:
            card["total"] = "N/A"

        for key in column_widths:
            if isinstance(card[key], float):
                if len("{:.2f}".format(card[key])) > column_widths[key]:
                    column_widths[key] = len("{:.2f}".format(card[key]))
            else:
                if len(str(card[key])) > column_widths[key]:
                    column_widths[key] = len(str(card[key]))

    column_widths["price"] += 1
    column_widths["total"] += 1

    print("{}|{}|{}|{}".format("Card name".ljust(column_widths["name"]),
                               "Qty".ljust(column_widths["quantity"]),
                               "Price".ljust(column_widths["price"]),
                               "Total".ljust(column_widths["total"])))
    
    keys = list(column_widths.keys())
    for i in range(len(keys) - 1):
        print("-" * column_widths[keys[i]], end = "")
        print("+", end = "")
    print("-" * column_widths[keys[-1]])
    
    for card in collection:
        if not isinstance(card["price"], str):
            print("{}|{}|{}|{}".format(card["name"].ljust(column_widths["name"]),
                                       str(card["quantity"]).rjust(column_widths["quantity"]),
                                       "{:.2f}€".format(card["price"]).rjust(column_widths["price"]),
                                       "{:.2f}€".format(card["total"]).rjust(column_widths["total"])))
        else:
            print("{}|{}|{}|{}".format(card["name"].ljust(column_widths["name"]),
                                       str(card["quantity"]).rjust(column_widths["quantity"]),
                                       card["price"].rjust(column_widths["price"]),
                                       card["total"].rjust(column_widths["total"])))

    for i in range(len(keys) - 1):
        print("-" * column_widths[keys[i]], end = "")
        print("+", end = "")
    print("-" * column_widths[keys[-1]])


args = parser.parse_args()

for filename in args.filenames:
    print("Getting data from {}".format(filename))

    if args.print_only:
        try:
            collection = read_collection_priced(filename)
        except FileNotFoundError:
            print("File {} has not been found, skipping\n".format(filename))
            continue
        except ValueError as inst:
            print(inst)
            print("Skipping\n")
            continue
    
    else:
        try:
            collection = read_collection(filename)
        except FileNotFoundError:
            print("File {} has not been found, skipping\n".format(filename))
            continue
        except ValueError as inst:
            print(inst)
            print("Skipping\n")
            continue

        print("Checking card prices")

        for card in collection:

            # Wait 200 milliseconds not to overload the API
            # https://scryfall.com/docs/api

            time.sleep(0.2)
            
            try:
                card["price"] = get_card_price(card["name"])
            except NameError as inst:
                print(inst)
                print("Skipping {}".format(card["name"]))
                card["price"] = "N/A"


    if args.update_files:
        print("Updating {}".format(filename))
        write_collection(filename, collection)

    if args.output_files:
        # For keeping file extensions
        filename_segments = os.path.basename(filename).split('.')
        if len(filename_segments) < 2:
            # No extension
            new_filename = filename + " (1)"
        else:
            filename_segments[-2] += " (1)"
            new_filename = ".".join(filename_segments)
            
        print("Outputting to {}".format(new_filename))
        try:
            output_collection(new_filename, collection)
        except FileExistsError as inst:
            print(inst)
            print("Skipping")

    print("Done")
    
    if args.print_all:
        print("All cards:")
        print_collection(collection)
    
    print("Collection total: {:.2f}€\n".format(calculate_total(collection)))
