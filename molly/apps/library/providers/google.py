import simplejson
from urllib import quote_plus
from urllib2 import urlopen, HTTPError
from logging import getLogger

from django.conf import settings

from molly.apps.library.providers import BaseMetadataProvider

logger = getLogger(__name__)

class GoogleBooksProvider(BaseMetadataProvider):
    
    # There's a double % here, because this is going to be sprintf'd twice -
    # once now, and then once later to build the query
    BOOK_SEARCH_ENDPOINT = 'https://www.googleapis.com/books/v1/volumes?q=%%s&key=%s' % settings.API_KEYS.get('google_books', '')
    
    def annotate(self, books):
        """
        @param books: The books to be annotated
        @type books: [LibrarySearchResult]
        @rtype: None
        """

        for book in books:
            # ISBNs from OLIS aren't always well-formed
            for isbn in [isbn.split()[0] for isbn in book.isbns]:
                try:
                    results = simplejson.load(
                        urlopen(self.BOOK_SEARCH_ENDPOINT % quote_plus(isbn)))
                    result = results['items'][0]
                except HTTPError, KeyError:
			logger.info('Google Books lookup failed', exc_info=True)
                else:
                    # Get the image
                    image_links = result.get('volumeInfo',{}
                                             ).get('imageLinks', [])

                    # Find the biggest one we have as a basis for resize
                    for image_size in ('extraLarge', 'large', 'medium',
                                       'small', 'thumbnail',
                                       'smallThumbnail'):
                        if image_size in image_links:
                            book.cover_image = image_links[image_size]
                            break

                    # Annotate epub link
                    book.epub = result.get('accessInfo', {}).get(
                        'epub', {}).get('downloadLink')

                    # Annotate PDF link
                    book.pdf = result.get('accessInfo', {}).get(
                        'pdf', {}).get('downloadLink')

                    # This ISBN got us a cover image, don't look up anymore
                    if hasattr(book, 'cover_image'):
                        break
