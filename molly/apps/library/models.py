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
