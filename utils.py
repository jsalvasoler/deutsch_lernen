import os

APP_TITLE = 'Dummkopf'
APP_ICON = ':pretzel:'

GERMAN_WORDS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'processed_4000_german_words.csv')

N_BUCKETS = 7
MIN_DAYS_BETWEEN_REVIEWS = 3
WORD_TYPES = ['prep', 'part', 'verb', 'pron', 'adv', 'conj', 'adj', 'noun', 'num', 'interj']
