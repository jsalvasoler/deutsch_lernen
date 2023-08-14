import streamlit as st
import pandas as pd
from utils import *


def intro():
    st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide", initial_sidebar_state="auto",
                       menu_items=None)
    st.title('Dashboard')
    st.write('Take a look at your learning progress!')

    df = pd.read_csv(GERMAN_WORDS_PATH, na_values=pd.NA)

    st.divider()
    cols = st.columns(5)
    cols[0].metric(label=f'Total words to learn:', value=f'{df.shape[0]}')
    words = df[~df.last_reviewed.isna()].copy()
    words['last_reviewed'] = pd.to_datetime(words['last_reviewed'])
    cols[1].metric(label=f'LR in the last 24 hours:',
                   value=f'{words[((words["last_reviewed"] - pd.Timestamp.now()).dt.days < 1)].shape[0]}')
    cols[2].metric(label=f'LR in the last 7 days:',
                   value=f'{words[((words["last_reviewed"] - pd.Timestamp.now()).dt.days < 7)].shape[0]}')

    # Percentage of words that have been reviewed at least once
    cols[3].metric(label=f'Reviewed at least once:',
                   value=f'{df[~df.last_reviewed.isna()].shape[0] / df.shape[0] * 100:.2f} %')
    # Average bucket of words (not reviewed words are bucket 0)
    df.loc[df['last_reviewed'].isna(), 'bucket'] = 1
    cols[4].metric(label='Average bucket', value=f'{df.bucket.mean():.4f}')
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
