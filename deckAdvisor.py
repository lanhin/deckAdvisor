'''
@2017-07  by lanhin

'''

import os
import json
import operator
from datetime import datetime as dt
from hearthstone.deckstrings import Deck
from hearthstone.enums import FormatType
from hearthstone.cardxml import load
from hearthstone.enums import Locale,Rarity,CardClass
from collection import Collection

def initDatabaseFromXml(path, locale="zhCN"):
    """Load card database from CardDefs.xml
    and use it to initialize DBF database

    Args:
      path: The xml file to load for init
      locale: The language setting for database
    Returns:
      db_dbf: The all-cards database
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

    Args:
      path: The file that contains the deckstrings
      collection: Cards collection for calculation
      db_dbf: The all-cards database
    Returns:
      newlist: A list of dict, each of which contains the results for a deck
    """
    newlist = []
    with open (path, "rt") as f:
        for line in f.readlines():
            cardsInDeck = 0
            deck = Deck.from_deckstring(line)
            for cardPair in deck.cards:
                cardsInDeck += cardPair[1]
            if cardsInDeck < 30:
                # Ignore the decks containing less than 30 cards
                continue
            newdict = {}
            newdict["name"] = "Deck name"
            newdict["url"] = "Unknown"
            newdict["date"] = "Unknown"
            newdict["type"] = "Unknown"
            newdict["rating-sum"] = "Unknown"
            newdict["deck-type"] = "Unknown"
            newdict["rarchetype"] = "Unknown"
            newdict["deck"] = deck
            newdict["deckstring"] = line
            newdict["lacked"], newdict["alreadyHave"] = collection.calculateLacks(deck.cards)
            _, newdict["dust"] = calcArcaneDust(newdict["lacked"], db_dbf)
            newdict["power"] = 1
            newlist.append(newdict)
    return newlist

def calculateLacksFromJSONFile(path, collection, db_dbf, dateLimit="07/01/2017", ratingLimit=20, filteredJSONFile=None):
    """Calculate the lacked cards from a json file

    Args:
      path: The path of the input json file
      collection: My card collection
      db_dbf: The database of all cards
      dateLimit: A date string, we only consider the decks newer than that
      ratingLimit: An int, ignore the decks who's 'rating-sum' is smaller than it
      filteredJSONFile: If it isn't None, store the filted JSON into it.
    Returns:
      newlist: a list of dict, each of which is the result for a deck
    """
    newlist = []
    deckstringSet = set()
    date = dt.strptime(dateLimit, "%m/%d/%Y")
    with open (path, "rt") as f:
        if filteredJSONFile != None:
            JSONOut = open(filteredJSONFile, "wt")
        for line in f.readlines():
            cardsInDeck = 0
            linedict = json.loads(line)
            if linedict.get('result') != None: # A json file produced by pyspider directly
                data = linedict['result']
            else:
                data = linedict
            deckCreatedDate = dt.strptime(data['date'].split(' ')[1], "%m/%d/%Y")
            if date > deckCreatedDate: # Ignore old decks
                continue
            if data['deckstring'] in deckstringSet: # The deckstring has already processed
                continue
            deckstringSet.add(data['deckstring'])
            deckRating = int(data['rating-sum'])
            if ratingLimit > deckRating: # Ignore decks with small rank points
                continue
            try:
                deck = Deck.from_deckstring(data['deckstring'])
            except:
                print("exception catched, dechstring:", data['deckstring'])
            for cardPair in deck.cards:
                cardsInDeck += cardPair[1]
            if cardsInDeck < 30:
                # Ignore the decks containing less than 30 cards
                continue
            newdict = {}
            newdict["name"] = data['title'].split('-')[0]
            newdict["url"] = data['url']
            newdict["date"] = data['date'].split(' ')[1]
            newdict["type"] = data['type']
            newdict["rating-sum"] = int(data['rating-sum'])
            newdict["deck-type"] = data['deck-type'].split(':')[1]
            newdict["archetype"] = data['archetype'].split(':')[1]
            newdict["deck"] = deck
            newdict["deckstring"] = data['deckstring']
            newdict["lacked"], newdict["alreadyHave"] = collection.calculateLacks(deck.cards)
            _, newdict["dust"] = calcArcaneDust(newdict["lacked"], db_dbf)
            newdict["power"] = 1
            newlist.append(newdict)
            if filteredJSONFile != None:
                json.dump(data, JSONOut)
                JSONOut.write('\n')

        if filteredJSONFile != None:
            JSONOut.close()

    return newlist


def calcArcaneDust(cards, db_dbf):
    """Calculate the aracne dust
    Return how much dust will be generated from the cards (dustOut)
    or how much is needed to prodece the cards (dustIn)

    Args:
      cards: A card pair list for calculation
      db_dbf: The all-cards database
    Returns:
      dustOut: How much dust will get if we break down these cards
      dustIn: How much dust will consume if we produce these cards
    """
    dustOut = 0
    dustIn = 0
    for cardPair in cards:
        card = db_dbf[cardPair[0]]
        if card.rarity == Rarity.COMMON:
            dustOut += 5 * cardPair[1]
            dustIn += 40 * cardPair[1]
        elif card.rarity == Rarity.RARE:
            dustOut += 20 * cardPair[1]
            dustIn += 100 * cardPair[1]
        elif card.rarity == Rarity.EPIC:
            dustOut += 100 * cardPair[1]
            dustIn += 400 * cardPair[1]
        elif card.rarity == Rarity.LEGENDARY:
            dustOut += 400 * cardPair[1]
            dustIn += 1600 * cardPair[1]
    return dustOut, dustIn

def outputRecommend(db, deckList, top=20, dustLimit=-1, decktype=None, keywordList=[]):
    """Output recommend deck list

    Args:
      db: The all cards' database
      deckList: The recommand deck list to output
      top: The number of decks to output
      dustLimit: If this value > 0, filter decks that need more dust than it.
      decktype: The type of decks to output. Value: standard, wild or None(standard and wild).
      keywordList: A keyword list for output range
    """
    step = 0
    if decktype == 'standard':
        decktype = 'Standard'
    if decktype == 'wild':
        decktype = 'Wild'
    deckgoaltype = 'Ranked'
    print (type(deckList), len(deckList))
    for item in deckList:
        #if decktype and item['type'] != decktype and item['type'] != "Unknown": # Let "Unknown" go.
        if decktype and not (decktype in item['type']) and item['type'] != "Unknown": # Let "Unknown" go.
            continue
        if deckgoaltype and not (deckgoaltype in item['deck-type']):
            continue
        if dustLimit > 0 and item['dust'] > dustLimit:
            continue
        print ("========")
        print ("Name:",item['name'], ",  type:",item['type'],  ",  date:", item['date'], ",  dust in need:",item['dust'])
        print ("Deck type:", item['deck-type'], ",  Archetype:", item['archetype'], ",  Rating:",item['rating-sum'], )
        print ("Deckstring:", item['deckstring'])
        print ("URL:",item['url'])
        if len(item['lacked']) > 0:
            print("Lacked cards:")
        for cardPair in item['lacked']:
            card = db[cardPair[0]]
            print (cardPair[1], 'x ('+str(card.cost)+')', card.name, ":", card.rarity)
        if len(item['alreadyHave']) > 0:
            print("Already have:")
        for cardPair in item['alreadyHave']:
            card = db[cardPair[0]]
            print (cardPair[1], 'x ('+str(card.cost)+')', card.name, ":", card.rarity)
        step += 1
        if step >= top:
            break
    print ("========")

def outputDictListToJSON(path, deckList, ignore='deck'):
    """Write the deck list into a json file with path PATH.

    Args:
      path: The output json file
      deckList: A list of dict to be written into json file.
      ignore: ignore this filed in the dict when output
    TODO: check if path already exists, mkdir if not.
    """
    with open (path, "w") as f:
        for item in deckList:
            # Pop ignore from item before store
            # eg. Pop 'deck' from item since deck is not JSON serializable
            if item.get(ignore) != None:
                deck = item[ignore]
                item.pop(ignore)
                json.dump(item, f)
                f.write('\n')
                item['deck'] = deck
            else:
                json.dump(item, f)
                f.write('\n')

def theUselessCards(collection, deckList):
    """Find out the cards that are useless
    Sum the 'alreadyHave' cards in deckList, and then find out the most useless ones from the collection

    Args:
      collection: One's card collection
      deckList: A list of dict produced by calculateLacksFromJSONFile() or calculateLacksFromFile()
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
      deckList: A list of dict produced by calculateLacksFromJSONFile() or calculateLacksFromFile()
    Returns:
      lackedOne: A card pair list contains how many times the card appears in a lack-one deck
      lackedTwo: A card pair list contains how many times the card appears in a lack-two deck
      totalLacked: Total times of every card in need, it's also a card pair list
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
            if cardPair[1] == 1:
                if lackedOne.get(cardPair[0]) != None:
                    lackedOne[cardPair[0]] += 1
                else:
                    lackedOne[cardPair[0]] = 1
            else: # cardPair[1] == 2
                if lackedTwo.get(cardPair[0]) != None:
                    lackedTwo[cardPair[0]] += 1
                else:
                    lackedTwo[cardPair[0]] = 1

    # reverse sort titalLacked by value then return it
    return reversed(sorted(lackedOne.items(), key=operator.itemgetter(1))), reversed(sorted(lackedTwo.items(), key=operator.itemgetter(1))), reversed(sorted(totalLacked.items(), key=operator.itemgetter(1)))

def outputCardsFromList(cardPairList, db, top=10):
    """Output cards(the appearance times and name) from a card pair list.

    Args:
      cardPairList: The list of card pair to output
      db: The all cards database
      top: The number of cards to output
    """
    step = 0
    for cardPair in cardPairList:
        card  = db[cardPair[0]]
        print (cardPair[1], 'x ('+str(card.cost)+')', card.name,':', card.rarity)
        step += 1
        if step >= top:
            break
    
def main():
    cardDefs = os.path.join("hsdata","CardDefs.xml")
    collectionFile = "inputs/mycards.csv"
    collectionDeckstringFile = "inputs/mycards"
    deckFile = "inputs/decks"
    deckJSONFile = "inputs/decks.json"
    recommendJSONFile = "outputs/recommend.json"
    dateLimit = "01/05/2015"
    ratingLimit = 5
    outputCounts = 20
    dustLimitation = 0
    typeLimitation = None
    filteredDeckJSON = "inputs/decks_db.json"

    # Cereate and init the database
    db = initDatabaseFromXml(cardDefs)

    # test start
    '''
    deck = Deck.from_deckstring("AAEBAf0ECMAB5gT7BPsFigbYE5KsAv2uAgucArsClQONBKsEtAThBJYF7Ae8CImsAgA=")

    for cardPair in deck.cards:
        card = db[cardPair[0]]
        print (cardPair[1],"x(", card.cost,")", card.name)
    '''
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
    #deckLacks0 = calculateLacksFromFile(deckFile, col, db)
    if os.path.exists(filteredDeckJSON):
        deckLacks = calculateLacksFromJSONFile(filteredDeckJSON, col, db, dateLimit, ratingLimit, None)
    else:
        deckLacks = calculateLacksFromJSONFile(deckJSONFile, col, db, dateLimit, ratingLimit, filteredDeckJSON)

    def dust(a):
        return a['dust']
    def rate(a):
        return a['rating-sum']
    sortedLacks_tmp = reversed(sorted(deckLacks, key=rate))
    #outputRecommend(db, list(sortedLacks_tmp), top=outputCounts, dustLimit=dustLimitation, decktype=typeLimitation)
    sortedLacks = sorted(sortedLacks_tmp, key=dust)
    
    #test start
    #print (deckLacks)
    #print (sortedLacks)
    #outputRecommend(db, deckLacks0)
    #test end

    # Output recommend decks in detail
    outputRecommend(db, sortedLacks, top=outputCounts, dustLimit=dustLimitation, decktype=typeLimitation)
    #outputRecommend(db, list(sortedLacks_tmp), top=outputCounts, dustLimit=dustLimitation, decktype=typeLimitation)

    outputDictListToJSON(recommendJSONFile, sortedLacks)

    #test start
    unused = theUselessCards(col, sortedLacks)
    time1, time2, timetotal = theMostWantedCards(sortedLacks)

    print ("========")
    print ("The unused cards:")
#    print (unused)
    outputCardsFromList(unused, db)
    print ("========")
    print ("The most wanted cards:")
    outputCardsFromList(timetotal, db)
    #test end
    
if __name__ == "__main__":
    main()
