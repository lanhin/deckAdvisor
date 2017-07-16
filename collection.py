from hearthstone.deckstrings import Deck

# TODO: handle exceptions
class Collection:
    """The card collection class
    To record all the card one have
    """
    def __init__(self):
        """Constructor
        All the member vars are listed
        """
        self.collect_db = {}
        self.num_of_cards = 0
        self.total_num_cards = 0
       
    def writeToFiles(self, path):
        """Write the database into a file with path PATH
        """
        with open (path, "wt") as f:
            for card in self.collect_db:
                f.write(str(card)+','+str(self.collect_db[card])+'\n')
                
    def loadFromFile(self, path):
        """Load the database from a file with path PATH
        """
        with open (path, "rt") as f:
            for line in f.readlines():
                card, cardNum = [int(x) for x in line.split(',')]
                self.add((card, cardNum))

    def calculateNumbers(self):
        """Calculate the statistic vars
        It may will be removed in the future
        """
        for card in self.collect_db:
            self.num_of_cards += 1
            self.total_num_cards += self.collect_db[card]

    def add(self, cardPair):
        """Add a card pair into the database
        """
        if self.collect_db.get(cardPair[0]) != None: # it exists
            self.collect_db[cardPair[0]] += cardPair[1]
        else:
            self.collect_db[cardPair[0]] = cardPair[1]
            self.num_of_cards += 1
        self.total_num_cards += cardPair[1]

    def output(self):
        """Print the database and the statistic number
        """
        print (self.collect_db)
        for card in self.collect_db:
            print (card,":",self.ows(card))
        print ("Number of different cards:", self.num_of_cards)
        print ("Total cards:", self.total_num_cards)

    def limitTo(self, max_card_count=2):
        """Limit the max count of cards
        In the most case, we use a value "2" here
        """
        if max_card_count < 1:
            return
        for card in self.collect_db:
            if self.collect_db[card] > max_card_count:
                self.total_num_cards -= (self.collect_db[card] - max_card_count)
                self.collect_db[card] = max_card_count

    def ows(self, card):
        """Return the count of card
        """
        if self.collect_db.get(card) == None: # it doesn't exists
            return 0
        else:
            return self.collect_db[card]

    def initFromDeckStringFile(self, path):
        """Init the database from a deckstring file
        The file should contain a set of deckstrings, every string in a line
        """
        with open (path, "rt") as f:
            for line in f.readlines():
                deck = Deck.from_deckstring(line)
                for cardPair in deck.cards:
                    self.add(cardPair)
