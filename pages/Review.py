import streamlit as st
from utils import *
from unidecode import unidecode
import pandas as pd
from google.oauth2 import service_account
from gsheetsdb import connect


def soften_string(s):
    return unidecode(s.lower())


def display_results():
    st.subheader('Results:')
    n_correct_words = sum(st.session_state.user_results.values())
    st.write(f'✅ {n_correct_words} | '
             f'❌ {st.session_state.n_words_review - n_correct_words}  '
             f'({round(n_correct_words / st.session_state.n_words_review * 100, 2)}%)')
    st.write('Words you did not get correct:')
    _, center, _ = st.columns([1, 2, 1])
    for card in reversed(st.session_state.current_batch):
        if st.session_state.user_results[card.german] == 0:
            center.divider()
            display_word_info(card, center)

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


def display_word_info(current, place):
    left, right = place.columns(2)
    left.markdown(f'**German**: {current.german}')
    left.markdown(f'**Type**: {current.type_of_word}')
    left.markdown(f'**Sentence**: {current.sentence}')
    right.markdown(f'**English**: {current.english}')
    right.markdown(f'**Bucket**: {current.bucket}')
    right.markdown(f'**Level**: {current.level}')
    right.markdown(f'**Plural**: {current.plural}')


def validate_user_translation(current, place, help_needed):
    place.divider()
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

    display_word_info(current, place)
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
    df = df[df['type_of_word'].isin(st.session_state.types_to_review)]

    # Check that the last review date is not too recent
    df = df[
        (pd.isna(df['last_reviewed'])) |
        (df['last_reviewed'].apply(lambda x: (pd.Timestamp.now() - pd.Timestamp(x)).days) >= MIN_DAYS_BETWEEN_REVIEWS)]
    # Filter accordingly to include new
    if not st.session_state.include_new:
        df = df[~pd.isna(df['last_reviewed'])]

    # Sample
    if df.empty:
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
    left.write(f'Word {st.session_state.word_iter + 1}/{st.session_state.n_words_review}\n'
               f'✅ {sum(st.session_state.user_results.values())} | '
               f'❌ {len(st.session_state.user_results) - sum(st.session_state.user_results.values())}')
    center.subheader(current.english)
    help_needed = right.button('Get help', key='help_needed', on_click=display_word_info, kwargs={'current': current,
                                                 'place': right})
    left.write(f'**Type**: {current.type_of_word}')
    left.write(f'**Level**: {current.level}')
    center.text_input('Your translation', key='user_translation', on_change=validate_user_translation,
                      kwargs={'current': current, 'place': center, 'help_needed': help_needed})


def sidebar():
    st.sidebar.title('Review')
    st.sidebar.write('This is the review page. Start by selecting the number of words that you want to review.')
    st.sidebar.divider()
    st.sidebar.number_input('Number of words to review', key='n_words_review',
                            min_value=5, max_value=50, value=10, step=1)
    st.sidebar.multiselect('Select buckets to review', key='buckets_to_review', options=range(1, N_BUCKETS + 1),
                           default=range(1, N_BUCKETS + 1))
    st.sidebar.multiselect('Select types to review', key='types_to_review', options=WORD_TYPES,
                           default=WORD_TYPES)
    st.sidebar.slider('Select levels to review', key='levels_to_review',
                      min_value=1, max_value=170, value=(40, 170), step=15)
    st.sidebar.checkbox('Include new words', key='include_new', value=True,
                        help='Include words that have never been reviewed')
    st.sidebar.button('Start review', on_click=start_review)


def db_test():
    # Create a connection object.
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
        ],
    )
    conn = connect(credentials=credentials)

    def run_query(query):
        rows = conn.execute(query, headers=1)
        rows = rows.fetchall()
        return rows

    sheet_url = st.secrets["private_gsheets_url"]
    rows = run_query(f'SELECT * FROM "{sheet_url}"')

    # Print results.
    for row in rows:
        st.write(f"{row.german} has a :{row.english}:")


if __name__ == '__main__':
    # app()
    db_test()
