'''
@2017-07  by lanhin

'''

import os
import json
import operator
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
    """Output recommend deck list
    Args:
      db: The all cards' database
      deckList: The recommand deck list to be outputed
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

def outputRecommendToJSON(path, deckList):
    """Write the recommand deck list into a json file with path PATH.
    Args:
      path: The output json file
      deckList: A list of dict to be written into json file.
    TODO: check if path already exists, mkdir if not.
    """
    with open (path, "w") as f:
        for item in deckList:
            # Pop 'deck' from item since deck is not JSON serializable
            deck = item['deck']
            item.pop('deck')
            json.dump(item, f)
            item['deck'] = deck

def theUselessCards(collection, deckList):
    """Find out the cards that are useless
    Sum the 'alreadyHave' cards in deckList, and then find out the most useless ones from the collection
    Args:
    Return:
      newdict: the used times of every card, 
    """
    newdict = {}
    for item in deckList:
        for cardPair in item['alreadyHave']:
            if newdict.get(cardPair[0]) != None: # the card exists in the dict
                newdict[cardPair[0]] += cardPair[1]
            else:
                newdict[cardPair[0]] = cardPair[1]
    for card in collection.collect_db:
        if newdict.get(card) == None: # the card doesn't exist in the dict
            newdict[card] = 0

    # sort newdict by value then return it
    return sorted(newdict.items(), key=operator.itemgetter(1))

def theMostWantedCards(deckList):
    """Find out the cards that are most wanted
    Sum the 'lacked' cards in deckList, find the most wanted ones.
    Args:
    Returns:
    
    """
    lackedOne = {}
    lackedTwo = {}
    totalLacked = {}
    for item in deckList:
        for cardPair in item['lacked']:
            if totalLacked.get(cardPair[0]) != None: # the card exists in the dict
                totalLacked[cardPair[0]] += cardPair[1]
            else:
                totalLacked[cardPair[0]] = cardPair[1]

    # reverse sort titalLacked by value then return it
    return reversed(sorted(lackedOne.items(), key=operator.itemgetter(1))), reversed(sorted(lackedTwo.items(), key=operator.itemgetter(1))), reversed(sorted(totalLacked.items(), key=operator.itemgetter(1)))

def outputCardsFromList(cardPairList, db):
    """Output cards(the appearance times and name) from a card pair list.
    """
    for cardPair in cardPairList:
        card  = db[cardPair[0]]
        print (cardPair[1], 'x', card.name,' ', card.rarity)
    
def main():
    cardDefs = os.path.join("hsdata","CardDefs.xml")
    collectionFile = "inputs/mycards.csv"
    collectionDeckstringFile = "inputs/mycards"
    deckFile = "inputs/decks"
    deckJSONFile = "inputs/decks.json"
    recommendJSONFile = "outputs/recommend.json"

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
        col.limitTo(2)
    else:
        col.initFromDeckStringFile(collectionDeckstringFile)
        col.limitTo(2)
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

    outputRecommendToJSON(recommendJSONFile, sortedLacks)

    #test start
    unused = theUselessCards(col, sortedLacks)
    time1, time2, timetotal = theMostWantedCards(sortedLacks)

    print ("========")
    print ("The unsed cards:")
#    print (unused)
    outputCardsFromList(unused, db)
    print ("========")
    print ("The most wanted cards:")
    outputCardsFromList(timetotal, db)
    #test end
    
if __name__ == "__main__":
    main()
