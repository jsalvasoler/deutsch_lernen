import streamlit as st
import pandas as pd
from utils import *


def intro():
    st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide", initial_sidebar_state="auto",
                       menu_items=None)
    st.title('Dashboard')
    st.write('This is the dashboard page')

    words = pd.read_csv(GERMAN_WORDS_PATH, na_values=pd.NA)
    words['last_reviewed'] = pd.to_datetime(words['last_reviewed'])

    st.divider()
    left, center, right = st.columns(3)
    left.write(f'**Total number of words to learn:** {words.shape[0]}')
    words = words[~words.last_reviewed.isna()]
    center.write(f'**Words reviewed in the last 24 hours:** '
                 f'{words[((words["last_reviewed"] - pd.Timestamp.now()).dt.days < 1)].shape[0]}')
    right.write(f'**Words reviewed in the last 7 days:** '
                f'{words[((words["last_reviewed"] - pd.Timestamp.now()).dt.days < 7)].shape[0]}')

    st.divider()
    _, center, _ = st.columns([1, 2, 1])
    # Plot number of words in each bucket
    center.write('**Distribution of words in each bucket**')
    center.bar_chart(words['bucket'].value_counts().sort_index())
    center.divider()
    center.write('**Number of words reviewed in the last 7 days**')
    # Plot the time series of the last week
    words['date'] = words['last_reviewed'].dt.date
    center.line_chart(words[words['last_reviewed'] > pd.Timestamp.now() - pd.Timedelta(days=7)].groupby('date').size())


if __name__ == '__main__':
    intro()
