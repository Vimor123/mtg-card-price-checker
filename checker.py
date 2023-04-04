import argparse
import requests
import json
import os
import codecs
import time


parser = argparse.ArgumentParser(description = "MTG Card Price Checker")
parser.add_argument('filenames', nargs = '*',
                    help = 'csv files containing collections of cards')


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
            card["price"] = "N"

    print(collection)
        
    print("")
