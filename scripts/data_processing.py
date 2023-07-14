import pandas as pd
import os


def process_4000_german_words():
    """
    This function processes the file Deutsch_4000_German_Words_by_Frequency.csv
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    df_path = os.path.join(root, 'data', 'Deutsch_4000_German_Words_by_Frequency.csv')
    df = pd.read_csv(df_path)

    rename_dict = {'German': 'german', 'German Alternatives': 'german_alternatives', 'English': 'english',
                   'English Hidden Alternatives': 'english_alternatives', 'Plural and inflected forms': 'plural',
                   'Sample sentence': 'sentence', 'Part of Speech': 'type_of_word', 'Level': 'level'}

    df = df[rename_dict.keys()].rename(columns=rename_dict)
    df['type_of_word'] = df['type_of_word'].apply(
        lambda x: x if pd.isna(x) or ';' not in x else ', '.join([w[3:] for w in x.split('; ')])
    ).replace({'p, j': 'prep, conj'})

    df['bucket'] = 1
    df['last_reviewed'] = pd.NA

    timestamp = pd.Timestamp.now().strftime('%Y%m%d%H%M%S')
    df.to_csv(os.path.join(root, 'data', f'processed_4000_german_words_{timestamp}.csv'), index=False)


if __name__ == '__main__':
    process_4000_german_words()
