# Usage:
# import fanficfinder as fff
# fff.get_data_from_page(<url of fic listings page on fanfiction.net>)

import re
import requests
import pandas as pd
from bs4 import BeautifulSoup

# selectors
STORIES_SLTR = 'div.z-list.zhover.zpointer'
STORY_TITLES_SLTR = 'a.stitle'
USER_PATH = '/u/'
USERNAME_REGEX = '\/u\/\d*\/(\w+)'
STORY_INFO_SLTR = 'div.z-indent.z-padtop'
STORY_STATS_REGEX = (
    "Rated: ([K+TM]+)"                              # 1:    Rating
    " - (\w+)"                                      # 2:    Language
    "( - ([-\w\/]*))?"                              # 4:    Genres
    " - Chapters: (\d+)"                            # 5:    Chapters
    " - Words: ([\d\,]+)"                           # 6:    Words
    "( - Reviews: ([\d\,]+))?"                      # 8:    Reviews
    "( - Favs: ([\d\,]+))?"                         # 10:   Favs
    "( - Follows: ([\d\,]+))?"                      # 12:   Follows
    "( - Updated: <span data-xutime='([\d]+)'>"     # 14:   Updated
        "[\d\w\s\,\/]+<\/span>)?"
    "( - Published: <span data-xutime='([\d]+)'>"   # 16:   Published
        "[\d\w\s\,\/]+<\/span>)?"
    "( - ((\[[\w\s\.\,\[\]]*\])*"                   # 19:   Pairings
    "([\w\s\.\,]*)))?"                              # 18:   Characters
    "(- Complete)?"                                 # 21:   Complete
)
STORY_STATS_COLS = [ 'rating', 'language', 'genres', 'chapter_count',
                     'word_count', 'review_count', 'fav_count', 'follow_count',
                     'updated_date', 'published_date', 'characters', 'pairings',
                     'complete' ]
COLUMNS = [ 'title', 'link', 'author', 'author_link', 'summary', 'rating',
            'language', 'genres', 'chapter_count', 'word_count', 'review_count',
            'fav_count', 'follow_count', 'updated_date', 'published_date',
            'characters', 'pairings', 'complete']

def get_titles(page):
    return [ title.text for title in page.select(STORY_TITLES_SLTR) ]

def get_story_links(page):
    return [ title['href'] for title in page.select(STORY_TITLES_SLTR) ]

def get_author_links(page):
    def parse_author_link(story):
        link = story.find(href=re.compile(USER_PATH))
        return link['href'] if link else ''

    return [ parse_author_link(story) for story in page.select(STORIES_SLTR) ]

def get_authors(page):
    author_links = get_author_links(page)
    return [ re.search(USERNAME_REGEX, author_link).group(1) if author_link != '' else '' for author_link in author_links ]

def get_summaries(page):
    return [ summary.find(text=True, recursive=False) for summary in page.select(STORY_INFO_SLTR) ]

def get_stats(page_text, titles_len):
    stats = re.findall(STORY_STATS_REGEX, page_text)
    assert(titles_len == len(stats))
    df = pd.DataFrame(None, index=xrange(len(stats)), columns=STORY_STATS_COLS)
    for i, stat in enumerate(stats):
        df.ix[i,'rating'] = stat[0]
        df.ix[i,'language'] = stat[1]
        df.ix[i,'genres'] = stat[3].replace('/',', ')
        df.ix[i,'chapter_count'] = int(stat[4].replace(',',''))
        df.ix[i,'word_count'] = int(stat[5].replace(',',''))
        df.ix[i,'review_count'] = \
            int(stat[7].replace(',','')) if stat[7] != '' else 0
        df.ix[i,'fav_count'] = \
            int(stat[9].replace(',','')) if stat[9] != '' else 0
        df.ix[i,'follow_count'] = \
            int(stat[11].replace(',','')) if stat[11] != '' else 0
        df.ix[i,'updated_date'] = \
            int(stat[13]) if stat[13] != '' else int(stat[15])
        df.ix[i,'published_date'] = int(stat[15])
        df.ix[i,'pairings'] = stat[18].replace('] [', '], [')
        df.ix[i,'characters'] = re.sub(r'] $', '', stat[17]) \
                                    .replace('] [',', ') \
                                    .replace(']',',') \
                                    .replace('[','') \
                                    .replace('Complete','')
        df.ix[i,'complete'] = (stat[20] != '') or (stat[17] == 'Complete')
    return df

def get_data_from_page(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    titles = get_titles(soup)
    page_df = pd.DataFrame(None, index=xrange(len(titles)), columns=COLUMNS)
    page_df.ix[:,'title'] = titles
    page_df.ix[:,'link'] = get_story_links(soup)
    page_df.ix[:,'author'] = get_authors(soup)
    page_df.ix[:,'author_link'] = get_author_links(soup)
    page_df.ix[:,'summary'] = get_summaries(soup)
    page_df.ix[:,STORY_STATS_COLS] = get_stats(r.text, len(titles))
    return page_df