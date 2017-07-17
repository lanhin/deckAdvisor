import os
import json
from hearthstone.deckstrings import Deck
from hearthstone.enums import FormatType
from hearthstone.cardxml import load
from hearthstone.enums import Locale,Rarity
from collection import Collection

# Create a deck from a deckstring
deck = Deck()
deck.heroes = [7]  # Garrosh Hellscream
deck.format = FormatType.FT_WILD
# Nonsense cards, but the deckstring doesn't validate.
deck.cards = [(1, 3), (2, 3), (3, 3), (4, 3)]  # id, count pairs
print(deck.as_deckstring)  # "AAEBAQcAAAQBAwIDAwMEAw=="

# Import a deck from a deckstring
deck = Deck.from_deckstring("AAEBAf0ECMAB5gT7BPsFigbYE5KsAv2uAgucArsClQONBKsEtAThBJYF7Ae8CImsAgA=")
print (deck.cards)


# load card database from CardDefs.xml and use it to initialize DBF database
db, xml = load(os.path.join("hsdata","CardDefs.xml"), locale="zhCN")

db_dbf={}
for card in db:
    #print (card)
    db_dbf[db[card].dbf_id] = db[card]

#print (db)
for cardPair in deck.cards:
#    print (cardPair[0])
    card = db_dbf[cardPair[0]]
    print (cardPair[1],"x(", card.cost,")", card.name, card.rarity)

#print (type(deck.cards))


#col = Collection()
#for cardPair in deck.cards:
#    col.add(cardPair)
#col.output()

#col.writeToFiles("mycards.csv")

col2 = Collection()
col2.loadFromFile("mycards.csv")

col2.output()
#col2.limitTo(1)
#col2.output()

#col3 = Collection()
#col3.initFromDeckStringFile("initdeck")
#col3.output()



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
            print (data)
            print (deck.cards)
            newdict = {}
            newdict["name"] = data['title']
            newdict["date"] = data['date']
            newdict["type"] = data['type']
            newdict["deck"] = deck
            newdict["lacked"], newdict["alreadyHave"] = collection.calculateLacks(deck.cards)
#            print (newdict["lacked"])
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

#print (calculateLacksFromFile("deck1.txt", col2, db_dbf))


with open ('t3.json', 'r') as f:
    for line in f.readlines():
        data = json.loads(line)['result']
    print (data)

print (calculateLacksFromJSONFile('t3.json', col2, db_dbf))
