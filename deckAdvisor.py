'''
@2017-07  by lanhin

'''

import os
import json
from hearthstone.deckstrings import Deck
from hearthstone.enums import FormatType
from hearthstone.cardxml import load
from hearthstone.enums import Locale,Rarity
from collection import Collection

def initDatabaseFromXml(path, locale="zhCN"):
    """Load card database from CardDefs.xml
    and use it to initialize DBF database
    """
    db, xml = load(path, locale=locale)
    db_dbf = {}
    for card in db:
        db_dbf[db[card].dbf_id] = db[card]
    return db_dbf

def calculateLacksFromFile(path, collection, db_dbf):
    """Calculate the lacked cards from decks stored in file PATH.
    The file should contain a set of deckstrings, every string in a line.
    This may will be removed in the future,
    since the function calculateLacksFromJSONFile() is more practical.
    """
    newlist = []
    with open (path, "rt") as f:
        for line in f.readlines():
            deck = Deck.from_deckstring(line)
            newdict = {}
            newdict["name"] = "Deck name"
            newdict["date"] = "Unknown"
            newdict["type"] = "Unknown"
            newdict["deck"] = deck
            newdict["lacked"], newdict["alreadyHave"] = collection.calculateLacks(deck.cards)
            _, newdict["dust"] = calcArcaneDust(newdict["lacked"], db_dbf)
            newdict["power"] = 1
            newlist.append(newdict)
    return newlist

def calculateLacksFromJSONFile(path, collection, db_dbf):
    newlist = []
    with open (path, "rt") as f:
        for line in f.readlines():
            data = json.loads(line)['result']
            deck = Deck.from_deckstring(data['deckstring'])
            if len(deck.cards) <= 0:
                # If there exists some connection problem,
                # we may get an empty deck here.
                # If so, just ignore it.
                continue
            newdict = {}
            newdict["name"] = data['title'].split('-')[0]
            newdict["url"] = data['url']
            newdict["date"] = data['date']
            newdict["type"] = data['type']
            newdict["deck"] = deck
            newdict["lacked"], newdict["alreadyHave"] = collection.calculateLacks(deck.cards)
            _, newdict["dust"] = calcArcaneDust(newdict["lacked"], db_dbf)
            newdict["power"] = 1
            newlist.append(newdict)
    return newlist


def calcArcaneDust(cards, db_dbf):
    """Calculate the aracne dust
    Return how much dust will be generated from the cards (dustOut)
    or how much is needed to prodece the cards (dustIn)
    """
    dustOut = 0
    dustIn = 0
    for cardPair in cards:
        card = db_dbf[cardPair[0]]
        if card.rarity == Rarity.COMMON:
            dustOut += 5
            dustIn += 40
        elif card.rarity == Rarity.RARE:
            dustOut += 20
            dustIn += 100
        elif card.rarity == Rarity.EPIC:
            dustOut += 100
            dustIn += 400
        elif card.rarity == Rarity.LEGENDARY:
            dustOut += 400
            dustIn += 1600
    return dustOut, dustIn

def outputRecommend(db, deckList):
    """
    """
    for item in deckList:
        print ("========")
        print ("Name:",item['name'], ", type:",item['type'],  ", date:", item['date'], ", dust in need:",item['dust'],", power:",item['power'])
        print ("URL:",item['url'])
        if len(item['lacked']) > 0:
            print("Lacked cards:")
        for cardPair in item['lacked']:
            card = db[cardPair[0]]
            print (cardPair[1], 'x', card.name, ":", card.rarity)
        if len(item['alreadyHave']) > 0:
            print("Already have:")
        for cardPair in item['alreadyHave']:
            card = db[cardPair[0]]
            print (cardPair[1], 'x', card.name, ":", card.rarity)
    print ("========")
    
def main():
    cardDefs = os.path.join("hsdata","CardDefs.xml")
    collectionFile = "inputs/mycards.csv"
    collectionDeckstringFile = "inputs/mycards"
    deckFile = "decks"
    deckJSONFile = "t3.json"

    # Cereate and init the database
    db = initDatabaseFromXml(cardDefs)

    # test start
    deck = Deck.from_deckstring("AAEBAf0ECMAB5gT7BPsFigbYE5KsAv2uAgucArsClQONBKsEtAThBJYF7Ae8CImsAgA=")

    for cardPair in deck.cards:
        card = db[cardPair[0]]
        print (cardPair[1],"x(", card.cost,")", card.name)

    #test end

    # Create and init my card collections
    col = Collection()
    if os.path.exists(collectionFile):
        col.loadFromFile(collectionFile)
    else:
        col.initFromDeckStringFile(collectionDeckstringFile)
        col.writeToFiles(collectionFile)

    #test start
    col.output()
    #test end


    # Calculate the lacked cards from deckFile
#    deckLacks = calculateLacksFromFile(deckFile, col, db)
    deckLacks = calculateLacksFromJSONFile(deckJSONFile, col, db)

    def dust(a):
        return a['dust']
    sortedLacks = sorted(deckLacks, key=dust)
    
    #test start
    print (deckLacks)
    print (sortedLacks)
    #test end

    # Output recommend decks in detail
    outputRecommend(db, sortedLacks)
    
if __name__ == "__main__":
    main()
