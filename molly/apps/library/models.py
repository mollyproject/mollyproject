class LibrarySearchQuery:
    """
    An object which gets passed to library search providers containing a library
    search query
    """
    
    STOP_WORDS = frozenset( (
    "a,able,about,across,after,all,almost,also,am,among,an,and,any,are,as,at,"
  + "be,because,been,but,by,can,cannot,could,dear,did,do,does,either,else,"
  + "ever,every,for,from,get,got,had,has,have,he,her,hers,him,his,how,however,"
  + "i,if,in,into,is,it,its,just,least,let,like,likely,may,me,might,most,must,"
  + "my,neither,no,nor,not,of,off,often,on,only,or,other,our,own,rather,said,"
  + "say,says,she,should,since,so,some,than,that,the,their,them,then,there,"
  + "these,they,this,tis,to,too,twas,us,wants,was,we,were,what,when,where,"
  + "which,while,who,whom,why,will,with,would,yet,you,your" ).split(',') )
    
    class InconsistentQuery(ValueError):
        def __init__(self, msg):
            self.msg = msg
    
    @staticmethod
    def _clean_isbn(isbn):
        """
        Tidy up ISBN input - limit to only allowed characters, replacing * with
        X
        """
        
        # Replace * with X
        isbn = isbn.replace('*', 'X')
        
        # Replace extroneous characters
        isbn = ''.join(c for c in isbn if (c in '0123456789X'))
        
        return isbn
    
    @staticmethod
    def _clean_input(input):
        """
        Remove quotes and stop words from the input
        
        @return: The cleaned string and a set of removed stop words
        @rtype: str, frozenset
        """
        
        input = input.replace('"', '').lower()
        # Cheap and nasty tokenisation
        cleaned = []
        removed = set()
        for word in input.split(' '):
            if word in LibrarySearchQuery.STOP_WORDS:
                removed.add(word)
            else:
                cleaned.append(word)
        return ' '.join(cleaned), frozenset(removed)
    
    def __init__(self, title, author, isbn):
        """
        @param title: The title of the book to search for
        @type title: str or None
        @param author: The author of the book to search for
        @type author: str or None
        @param isbn: an ISBN number to search for - can contain * in place of X
        @type isbn: str or None
        @raise LibrarySearchQuery.InconsistentQuery: If the query parameters are
            inconsistent (e.g., isbn specified alongside title and author, or no
            queries present)
        """

        if (title or author) and isbn:
            raise self.InconsistentQuery(
                "You cannot specify both an ISBN and a title or author.")

        if not (title or author or isbn):
            raise self.InconsistentQuery(
                "You must supply some subset of title or author, and ISBN.")
        
        self.removed = set()
        
        if title:
            self.title, removed = self._clean_input(title)
            self.removed |= removed
        else:
            self.title = None
        
        if author:
            self.author, removed = self._clean_input(author)
            self.removed |= removed
        else:
            self.author = None
        
        if isbn:
            self.isbn = self._clean_isbn(isbn)
        else:
            self.isbn = None

class LibrarySearchResult(object):
    
    id = ''
    """
    @ivar id: A unique ID to reference this item in the database
    @type id: str
    """
    
    title = ''
    """
    @ivar title: The title of this book
    @type title: str
    """
    
    publisher = ''
    """
    @ivar publisher: The publisher of this book
    @type publisher: str
    """
    
    author = ''
    """
    @ivar author: The author(s) of this book
    @type author: str
    """
    
    description = ''
    """
    @ivar description: A description of this book
    @type description: str
    """
    
    edition = ''
    """
    @ivar edition: The edition of this book
    @type edition: str
    """
    
    copies = 0
    """
    @ivar copies: The number of copies of this book held
    @type copies: int
    """
    
    holding_libraries = 0
    """
    @ivar holding_libraries: The number of libraries which hold copies of this
                             book
    @type holding_libraries: int
    """
    
    isbns = []
    """
    @ivar isbns: The ISBNs associated with this item
    @type isbns: list of strings
    """
    
    issns = []
    """
    @ivar isbns: The ISSNs associated with this item
    @type isbns: list of strings
    """
    
    holdings = {}
    """
    @ivar holdings: A dictionary where library names are keys and the value is
                    a list of dictionaries, one for each copy of the item held.
                    This dictionary has the following keys: due (the due date),
                    availability (one of the AVAIL_ keys below),
                    availability_display (the display text for availability
                    status) and materials_specified (an additional value
                    typically indicating what issue of a copy this is)
    @type holdings: dict
    """
    
    AVAIL_UNAVAILABLE, AVAIL_UNKNOWN, AVAIL_STACK, AVAIL_REFERENCE, \
    AVAIL_AVAILABLE = range(5)

    def __unicode__(self):
        return self.title


class Library(object):
    def __init__(self, location):
        self.location = tuple(location)
    
    def __unicode__(self):
        return " - ".join(self.location)
    __repr__ = __unicode__

    def __hash__(self):
        return hash((type(self), self.location))

    def __eq__(self, other):
        return self.location == other.location

    def availability_display(self):
        return [
            'unavailable', 'unknown', 'stack', 'reference', 'available'
        ][self.availability]