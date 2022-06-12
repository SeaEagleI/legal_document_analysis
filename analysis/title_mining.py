# coding: utf-8
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import NMF, LatentDirichletAllocation
import pickle
import re
from tqdm import tqdm

# files
path = "../../data/"
dataset = "cb12/"
raw_path = path + dataset + "raw/"
interim_path = path + dataset + "interim/"
jobs_path = raw_path + "jobs.csv"
jobs_cleaned_path = interim_path + "jobs_cleaned.csv"


# run lda model to calculate topics from given text list
def calc_lda(df, no_features=1000, no_topics=20):
    # LDA can only use raw term counts for LDA because it is a probabilistic graphical model
    tf_vectorizer = CountVectorizer(max_df=0.95, min_df=2, max_features=no_features, stop_words='english')
    tf = tf_vectorizer.fit_transform(df)
    tf_feature_names = tf_vectorizer.get_feature_names()
    # Run LDA
    lda = LatentDirichletAllocation(n_components=no_topics, max_iter=5, learning_method='online', learning_offset=50.,
                                    random_state=0).fit(tf)
    return lda, tf_feature_names


# display topic results
def display_topics(model, feature_names, no_top_words=5):
    for topic_idx, topic in enumerate(model.components_):
        print("Topic %d:" % (topic_idx))
        print(" ".join([feature_names[i] for i in topic.argsort()[:-no_top_words - 1:-1]]))


# 拿到分类结果，即Topic类别编号
def apply_topics(text, model, feature_names, fn_dict):
    words = re.findall(r"[\w']+", text)
    overlap = set(feature_names) & set(words)
    max_topic_idx = np.argmax([sum(topic[fn_dict[word]] for word in overlap) for topic in model.components_])
    return max_topic_idx


# Read data
jobs = pd.read_csv(jobs_path, header=0, error_bad_lines=False)
jobs = jobs.rename(columns={"JobID": "item_id", "State": "state", "Country": "country", "City": "city", "Zip5": "zip5"})
jobs = jobs.set_index("item_id")

# text field preprocess
jobs["Description"].fillna("", inplace=True)
jobs['Description'] = jobs['Description'].map(lambda x: re.sub('<[^<]+?>', '', x)).map(
    lambda x: re.sub('\\\\r', '', x)).map(lambda x: re.sub('\\\\n', '', x)).map(lambda x: re.sub('&nbsp;', ' ', x)).map(
    lambda x: re.sub('[—]+', ' ', x)).map(lambda x: re.sub('/', ' ', x))
jobs['Description'] = jobs['Description'].str.lower()
jobs.head()

# save to cache
print(len(jobs.Description.unique()))
# other codes
# print("Unique cities: " + str(len(jobs.city.unique())))
# # print(jobs['city'].value_counts(normalize=True) * 100)
# print("Unique states: " + str(len(jobs.state.unique())))
# print("Unique zip codes: " + str(len(jobs.zip5.unique())))
# print("Unique countries: " + str(len(jobs.country.unique())))


# 训练LDA并保存结果
# TODO LIST: 这段训练LDA模型的代码要运行很久, 可以后期找个有进度条的实现方式
lda_desc, tf_feature_names_desc = calc_lda(jobs["Description"])
pickle.dump(lda_desc, open(interim_path + "lda_desc.model", 'wb'), protocol=4)
pickle.dump(tf_feature_names_desc, open(interim_path + "lda_desc.fnames", 'wb'), protocol=4)
# 加载结果
# lda_desc = pickle.load(open(interim_path + "lda_desc.model", 'rb'))
# tf_feature_names_desc = pickle.load(open(interim_path + "lda_desc.fnames", 'rb'))
# display
display_topics(lda_desc, tf_feature_names_desc, 10)

# 加标记
fn_dict_desc = {name: f_idx for f_idx, name in enumerate(tf_feature_names_desc)}
tqdm.pandas(desc='pandas bar')
jobs['DescTopic'] = jobs.progress_apply(
    lambda x: apply_topics(x['Description'], lda_desc, tf_feature_names_desc, fn_dict_desc), axis=1)

jobs = jobs.drop(columns=["WindowID", "Title", "Description", "Requirements", "StartDate", "EndDate"])
jobs.to_csv(jobs_cleaned_path)
print(jobs.head())
print(jobs.shape)
