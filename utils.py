import os

APP_TITLE = 'Dummkopf'
APP_ICON = ':pretzel:'

GERMAN_WORDS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'processed_4000_german_words.csv')

N_BUCKETS = 7
MIN_DAYS_BETWEEN_REVIEWS = {1: 1, 2: 1, 3: 3, 4: 3, 5: 5, 6: 8, 7: 13}
WORD_TYPES = ['prep', 'part', 'verb', 'pron', 'adv', 'conj', 'adj', 'noun', 'num', 'interj']
MAX_WORDS_TO_REVIEW = 100
