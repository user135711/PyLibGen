import argparse
import re
import os
from urllib import request
from urllib.parse import urlencode
from tabulate import tabulate
from bs4 import BeautifulSoup
from settings import *


def getSearchResults(term, page, column):
    params = urlencode({'req': term, 'column': column, 'page': page})
    url = 'http://libgen.io/search.php?&%s' % params

    source = request.urlopen(url)
    soup = BeautifulSoup(source, 'lxml')
    if page == 1:
        books_found = re.search(r'(\d+) books found', str(soup))
        print(books_found.group().upper())
        n_books = int(books_found.groups()[0])

    page_books = soup.find_all('tr')
    page_books = page_books[3:-1]  # Ignore 3 first and the last <tr> label.
    books = page_books
    if page == 1:
        return(books, n_books)
    else:
        return(books)


def formatBooks(books, page):
    fmt_books = []
    books_mirrors = []  # List of dics with complete titles and mirrors

    for i, rawbook in enumerate(books):
        i += (page - 1) * 25

        book_attrs = rawbook.find_all('td')

        authors = [a.text for a in book_attrs[1].find_all('a')]
        author = ', '.join(authors[:N_AUTHORS])
        author = author[:MAX_CHARS_AUTHORS]

        title = book_attrs[2].find(title=True).text
        tinytitle = title[:MAX_CHARS_TITLE]

        publisher = book_attrs[3].text[:MAX_CHARS_PUBLISHER]
        year = book_attrs[4].text
        lang = book_attrs[6].text[:2]  # Show only 2 first characters
        size = book_attrs[7].text
        ext = book_attrs[8].text
        mirror_list = []  # List of all the four mirrors
        for mirror in range(9, 13):
            mirror_list.append(book_attrs[mirror].a.attrs['href'])

        book = (str(i + 1), author, tinytitle, publisher,
                year, lang, ext, size)  # Start at 1

        book_mirrors = {'title': title, 'mirrors': mirror_list}
        books_mirrors.append(book_mirrors)

        fmt_books.append(book)

    return(fmt_books, books_mirrors)


def selectBook(books, mirrors, page, n_books):
    headers = ['#', 'Author', 'Title', 'Publisher',
               'Year', 'Lang', 'Ext', 'Size']

    print(tabulate(books[(page - 1) * 25:page * 25], headers))
    # Detect when all the books are found.
    no_more_matches = n_books == len(books)

    if no_more_matches:
        print("\nEND OF LIST. NO MORE BOOKS FOUND")

    while True:
        if no_more_matches:
            elec = input('Type # of book to download or q to quit: ')
        else:
            elec = input(
                '\nType # of book to download, q to quit or just press Enter to see more matches: ')

        if elec.isnumeric():
            choice = int(elec) - 1
            if choice < len(books) and choice >= 0:  # Selection
                title = '{}.{}'.format(
                    mirrors[choice]['title'], books[choice][-2])

                if True:
                    ''' This is the default mirror.
                    In the case we can get the other mirrors to work,
                    change True to a boolean variable defined in settings.py
                    that defines if the user want to have a option to 
                    select from the different mirrors. '''
                    DownloadBook.default_mirror(
                        mirrors[choice]['mirrors'][0], title)
                else:
                    number_of_mirrors = 4
                    print(
                        "\n #1: Mirror libgen.io (default)",
                        "\n #2: Mirror libgen.pw",
                        "\n #3: Mirror bookfi.net",
                        "\n #4: Mirror b-ok",
                    )
                    while True:
                        option = input(
                            '\nType # of mirror to start download or q to quit: ')

                        if option.isnumeric() and int(option) > 0 and int(option) <= number_of_mirrors:
                            if int(option) == 1:
                                DownloadBook.default_mirror(
                                    mirrors[choice]['mirrors'][0], title)
                                pass
                            elif int(option) == 2:
                                DownloadBook.second_mirror(
                                    mirrors[choice]['mirrors'][1], title)
                                pass
                            elif int(option) == 3:
                                DownloadBook.third_mirror(
                                    mirrors[choice]['mirrors'][2], title)
                                pass
                            elif int(option) == 4:
                                DownloadBook.fourth_mirror(
                                    mirrors[choice]['mirrors'][3], title)
                                pass

                            return(False)

                        elif option == 'q' or option == 'Q':  # Quit
                            return(False)
                        else:
                            print("Not a valid option.")
                            continue

                return(False)

            else:
                print("Couldn't fetch the book #{}".format(str(choice + 1)))
                continue

        elif elec == 'q' or elec == 'Q':  # Quit
            return(False)

        elif not elec:
            if no_more_matches:
                print('Not a valid option')
                continue
            else:
                return(True)

        else:
            print('Not a valid option.')


class DownloadBook():
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'
    accept = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    accept_charset = 'ISO-8859-1,utf-8;q=0.7,*;q=0.3'
    accept_lang = 'en-US,en;q=0.8'
    connection = 'keep-alive'

    headers = {
        'User-Agent': user_agent,
        'Accept': accept,
        'Accept-Charset': accept_charset,
        'Accept-Language': accept_lang,
        'Connection': connection,
    }

    def default_mirror(link, filename):
        '''This is the default (and first) mirror to download.
        The base of this mirror is http://libgen.io/ads.php?'''
        req = request.Request(link, headers=DownloadBook.headers)
        source = request.urlopen(req)
        soup = BeautifulSoup(source, 'lxml')
        mother_link = "https://libgen.pw"

        for a in soup.find_all('a'):
            if a.text == 'Open download':
                item_url = a.attrs['href']
                getpage_url = mother_link + item_url
                req2 = request.Request(getpage_url, headers=DownloadBook.headers)
                source2 = request.urlopen(req2)
                soup2 = BeautifulSoup(source2, 'lxml')

        for a in soup2.find_all('a'):
            if a.text == 'Get':
                download_url = mother_link + a.attrs['href']
                break


        if os.path.exists(DOWNLOAD_PATH) and os.path.isdir(DOWNLOAD_PATH):
            print('Downloading...')
            path = '{}/{}'.format(DOWNLOAD_PATH, filename)
            request.urlretrieve(download_url, filename=path)
            print('Book downloaded to {}'.format(os.path.abspath(path)))
        elif os.path.isfile(DOWNLOAD_PATH):
            print('The download path is not a directory. Change it in settings.py')
        else:
            print('The download path does not exist. Change it in settings.py')

    def second_mirror(link, filename):
        '''This is the second mirror to download.
        The base of this mirror is https://libgen.pw/view.php?*'''
        link = link.replace("view", "download")
        pass

    def third_mirror(link, filename):
        '''This is the third mirror to download.
        The base of this mirror is http://en.bookfi.net/md5/*'''
        pass

    def fourth_mirror(link, filename):
        '''This is the fourth mirror to download.
        The base of this mirror is http://b-ok.org/md5/*'''
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    column = parser.add_mutually_exclusive_group()
    parser.add_argument('search', nargs='+', help='search term')
    column.add_argument('-t', '--title', action='store_true',
                        help='get books from the specified title')
    column.add_argument('-a', '--author', action='store_true',
                        help='get books from the specified author')
    column.add_argument('-p', '--publisher', action='store_true',
                        help='get books from the specified publisher')
    column.add_argument('-y', '--year', action='store_true',
                        help='get books from the specified year')

    args = parser.parse_args()

    search_term = ' '.join(args.search)
    search_arguments = [(args.title, 'title'),
                        (args.author, 'author'),
                        (args.publisher, 'publisher'),
                        (args.year, 'year')]

    sel_column = 'def'
    for arg in search_arguments:
        if arg[0]:
            sel_column = arg[1]

    books = []
    mirrors = []
    page = 1
    get_next_page = True

    while get_next_page:
        if page == 1:
            raw_books, n_books = getSearchResults(search_term, page, sel_column)
        else:
            raw_books = getSearchResults(search_term, page, sel_column)

        if raw_books:
            new_books, new_mirrors = formatBooks(raw_books, page)
            books += new_books
            mirrors += new_mirrors
            get_next_page = selectBook(books, mirrors, page, n_books)
            page += 1
        elif raw_books == [] and n_books != 0:  # 0 matches in the last page
            get_next_page = selectBook(books, mirrors, page - 1, n_books)
        else:  # 0 matches total
            get_next_page = False
