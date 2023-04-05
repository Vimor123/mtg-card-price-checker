# mtg-card-price-checker

A simple terminal card price checker for MTG decklists

## Premise

Do you want to quickly update the prices of your MTG card collections? Update your decklists, maybe track some other deck prices? Here's a command line tool for you.

You just need to pass the file name/path to your decklist/collection and tell it what you want to do with it. It's gonna check the card prices using a lovely API developed by the Scryfall team (https://scryfall.com/docs/api).

Keep in mind that this tool will only check the nonfoil, standard artwork version of the card, so it's not suitable for use if you want to know the price of alternate artwork/foil versions of cards.

## Usage

To run the price checker, simply execute it with a Python interpreter. Pass in as many files (as arguments) as you want, and the checker will go through them sequentally. Here's how it should look in the terminal:

python checker.py [flags ...] [filenames ...]

### File format

The price checker will parse the files, looking for card names and the quantities of those cards, so each line in your file should have this format:

"card name";"quantity"

Note: the collection file should not have a header and should only consist of those lines, if you want to add something after the line, just put a semicolon after the quantity.

### Use cases

So what can the price checker do? Without any flags, it will only print out the total price of each collection, but you can also:

* update the collection files - after running the checker, every line in your file should contain this: "card name";"quantity";"card price";"price * quantity"
  - python checker.py -u [filenames ...]
  - Note: this will delete everything else written in the files

* output to new collection files - the checker will create new files in the current working directory
  - python checker.py -o [filenames ...]
  - Note: this will create new files with a name "previous file name" (1)."extension" only if those files don't exist in the current working directory

## Notes

After requesting the card price for each card, the checker will wait 200 milliseconds not to overload the API.

The "requests" Python library should be installed.
