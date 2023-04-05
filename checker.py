import argparse
import requests
import json
import os
import codecs
import time


parser = argparse.ArgumentParser(description = "MTG Card Price Checker")
parser.add_argument('filenames', nargs = '*',
                    help = 'csv files containing collections of cards')

parser.add_argument('-u', '--update-files', help = "update the files, puts card prices in the given files",
                    action = 'store_true', dest = 'update_files')
parser.add_argument('-o', '--output-files', help = "output new files (in cwd) containing card names, quantities and prices",
                    action = 'store_true', dest = 'output_files')


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

    # File format (no header row):
    # <name><delimiter><quantity>\n
    # <name><delimiter><quantity>\n
    # ...
    
    collection = []
    delimiter = ';'
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


def write_collection(filename, collection):
    current_dir = os.getcwd()
    absolute_path = os.path.join(current_dir, filename)

    delimiter = ';'
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


args = parser.parse_args()

for filename in args.filenames:
    print("Getting data for {}".format(filename))
    try:
        collection = read_collection(filename)
    except FileNotFoundError:
        print("File {} has not been found, skipping\n".format(filename))
        continue
    except ValueError as inst:
        print(inst)
        print("Skipping\n")
        continue

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
    print("Collection total: {:.2f}\n".format(calculate_total(collection)))
