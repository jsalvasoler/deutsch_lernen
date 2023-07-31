import streamlit as st
from utils import *
from unidecode import unidecode
import pandas as pd
import numpy as np


def soften_string(s):
    return unidecode(s.lower()).replace('!', "")


def display_results():
    st.subheader('Results:')
    n_correct_words = sum(st.session_state.user_results.values())
    st.write(f'✅ {n_correct_words} | '
             f'❌ {st.session_state.n_words_review - n_correct_words}  '
             f'({round(n_correct_words / st.session_state.n_words_review * 100, 2)}%)')
    if not n_correct_words == st.session_state.n_words_review:
        st.write('Words you did not get correct:')
        _, center, _ = st.columns([1, 2, 1])
        for card in reversed(st.session_state.current_batch):
            if st.session_state.user_results[card.german] == 0:
                center.divider()
                display_card(card, center)

    left, right = st.columns(2)
    left.button('Continue reviewing', on_click=start_review)


def save_results():
    df = pd.read_csv(GERMAN_WORDS_PATH)
    for card in st.session_state.current_batch:
        if st.session_state.user_results[card.german] == 1:
            bucket = min(card.bucket + 1, N_BUCKETS)
        else:
            bucket = max(card.bucket - 1, 1)
        df.loc[df['german'] == card.german, 'bucket'] = bucket
        df.loc[df['german'] == card.german, 'last_reviewed'] = pd.Timestamp.now()
    df.to_csv(GERMAN_WORDS_PATH, index=False)


def display_card(current, place):
    left, right = place.columns(2)
    left.markdown(f'**German**: {current.german}')
    left.markdown(f'**Alternatives (G)**: {current.german_alternatives}')
    left.markdown(f'**Type**: {current.type_of_word}')
    left.markdown(f'**Sentence**: {current.sentence}')
    right.markdown(f'**English**: {current.english}')
    right.markdown(f'**Alternatives (E)**: {current.english_alternatives}')
    right.markdown(f'**Bucket**: {current.bucket}')
    right.markdown(f'**Level**: {current.level}')
    right.markdown(f'**Plural**: {current.plural}')
    left.markdown(f'Last reviewed: {current.last_reviewed}')


def validate_user_translation(current, place, help_needed):
    if st.session_state.user_translation == '':
        return
    if help_needed:
        place.warning('You needed help... It counts as incorrect.')
        st.session_state.user_results[current.german] = 0
    elif soften_string(st.session_state.user_translation) == soften_string(current.german) or \
            soften_string(st.session_state.user_translation) in [soften_string(s) for s in current.german.split(', ')]:
        place.success('Correct!')
        st.session_state.user_results[current.german] = 1
    else:
        place.error('Incorrect!')
        st.session_state.user_results[current.german] = 0

    display_card(current, place)
    st.session_state.word_iter += 1
    st.session_state.user_translation = ''
    if st.session_state.word_iter == st.session_state.n_words_review:
        st.session_state.word_iter = None
        display_results()
        save_results()
        st.session_state.current_batch = None
        st.session_state.user_results = {}


def initialize_session_state():
    if 'word_iter' not in st.session_state:
        st.session_state['word_iter'] = None
    if 'current_batch' not in st.session_state:
        st.session_state['current_batch'] = None
    if 'user_results' not in st.session_state:
        st.session_state['user_results'] = {}


def start_review():
    # Load next batch of words
    df = pd.read_csv(GERMAN_WORDS_PATH, na_values=pd.NA)
    # Filter by level
    df = df[df['level'].between(*st.session_state.levels_to_review)]
    # Filter by bucket
    df = df[df['bucket'].isin(st.session_state.buckets_to_review)]
    # Filter by type
    if st.session_state.types_to_review:
        df = df[df['type_of_word'].isin(st.session_state.types_to_review)]

    # Check that the last review date is not too recent
    # - If the word has never been reviewed, it is included
    # - If the word is in bucket 1 and already reviewed, it is included (no need to wait)
    # - If the word has been reviewed, it is included if the last review was more than MIN_DAYS_BETWEEN_REVIEWS ago
    df = df[
        (df['last_reviewed'].isna()) |
        (~df['last_reviewed'].isna() & (df.bucket == 1)) |
        (df.apply(lambda x: (pd.Timestamp.now() - pd.Timestamp(x['last_reviewed'])).days >=
                            MIN_DAYS_BETWEEN_REVIEWS[x['bucket']], axis=1))]
    # Filter accordingly to include new
    if not st.session_state.include_new:
        df = df[~pd.isna(df['last_reviewed'])]

    # Sample
    if df.empty or len(df) < st.session_state.n_words_review:
        st.error('No words to review. Please change your filters.')
        return

    df['german'] = df['german'].astype(str)
    df = df.sample(st.session_state.n_words_review)
    st.session_state.current_batch = list(df.itertuples())
    st.session_state.word_iter = 0
    st.session_state.user_results = {}


def app():
    initialize_session_state()
    st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide", initial_sidebar_state="auto",
                       menu_items=None)
    sidebar()

    if st.session_state.word_iter is None:
        return

    current = st.session_state.current_batch[st.session_state.word_iter]
    left, center, right = st.columns([1, 2, 1])
    left.write(f'Word {st.session_state.word_iter + 1}/{st.session_state.n_words_review}')
    left.write(f'\n✅ {sum(st.session_state.user_results.values())} | '
               f'❌ {len(st.session_state.user_results) - sum(st.session_state.user_results.values())}')

    center.subheader(current.english)
    right.button('Get help', key='help_needed', on_click=get_help, kwargs={'current': current, 'place': right})
    left.write(f'**Type**: {current.type_of_word}')
    left.write(f'**Level**: {current.level}')
    center.text_input('Your translation', key='user_translation', on_change=validate_user_translation,
                      kwargs={'current': current, 'place': center, 'help_needed': st.session_state.help_needed},
                      label_visibility='collapsed')


def get_help(current, place):
    st.session_state.user_translation = ""
    display_card(current, place)


def sidebar():
    st.sidebar.number_input('Number of words to review', key='n_words_review',
                            min_value=5, max_value=50, value=10, step=1)
    st.sidebar.multiselect('Select buckets to review', key='buckets_to_review', options=range(1, N_BUCKETS + 1),
                           default=range(1, N_BUCKETS + 1))
    st.sidebar.multiselect('Select types to review', key='types_to_review', options=WORD_TYPES,
                           default=[])
    st.sidebar.slider('Select levels to review', key='levels_to_review',
                      min_value=1, max_value=170, value=(1, 170), step=15)
    st.sidebar.checkbox('Include new words', key='include_new', value=False,
                        help='Include words that have never been reviewed')
    st.sidebar.button('Start review', on_click=start_review)


if __name__ == '__main__':
    app()
