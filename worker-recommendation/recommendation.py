import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from bson.objectid import ObjectId

from utils.eimmo_data import DataExtractor
from utils.preprocess import refine, tokenize


def get_similar_project(target_idx, df_context, k=3) -> list:
    """Get top- similar projects information within the context
       based on projects name.

    Args:
        target_idx (int): _id of target project within the DataFrame(df_context)
        df_context (pandas.DataFrame): projects information with same annotation type
            
    Returns:
        most_similar_k (list[object]): top-k similar projects information
                
    """
    # Refine and tokenize projects name
    df_context['refined'] = df_context['name'].map(refine)
    df_context['tokenized'] = df_context['refined'].map(tokenize)
    docs = df_context['tokenized'].to_list()

    # Embedding projects name based on TF(Term-Frequency)
    vect = CountVectorizer()
    vectors = vect.fit_transform(docs).toarray()
    
    # Calculate euclidean distances
    target_vector = vectors[target_idx]
    distances = np.sqrt(np.sum((target_vector-vectors)**2, axis=1))

    # Extract most similar projects(K)
    most_similar_k = list()
    cnt = 0
    for idx in np.argsort(distances):
        if cnt == k:
            break
        else:
            if not target_idx == idx:
                most_similar_k.append(df_context.loc[idx, ['_id', 'name', 'stages']])
                cnt += 1
    return most_similar_k


def get_recommendation(prj_id):
    """get worker recommendation based on project title similarity.
    
    Args:
        prj_id (str): project id of the target
    
    Returns:
        recommend_user_ids (list(str)): workers' id of the recommendation result

    """
    query = DataExtractor()
    # Extract all projects information from eimmo database
    df_prj = query.get_all_projects_info()
    
    # Filter same annotation_type projects
    annot_type = df_prj[df_prj._id == ObjectId(prj_id)]['annotation_type'].values[0]
    df_context = df_prj[df_prj.annotation_type == annot_type].reset_index(drop=True)
    target_idx = df_context[df_context._id == ObjectId(prj_id)].index

    similar_projects = get_similar_project(target_idx, df_context)
    for prj_info in similar_projects:
        prj_id_k = prj_info['_id']
        labeling_stage_id = prj_info['stages'][0]
        try:
            df_work_stat = query.get_workers_stat(prj_id_k, labeling_stage_id)
            break
        except:
            continue
    else:
        raise Exception('No working records for recommendation')

    # Feature Engineering
    df_work_stat['time_by_inst'] = df_work_stat['work_time'] / df_work_stat['total']
    df_work_stat['recall'] = (df_work_stat['geo_eval_total']-df_work_stat['geo_eval_missing']) / df_work_stat['geo_eval_total']
    df_work_stat['precision'] = (df_work_stat['geo_eval_total']-df_work_stat['geo_eval_error']) / df_work_stat['geo_eval_total']
    df_work_stat['f1'] = (2*df_work_stat['recall']*df_work_stat['precision']) / (df_work_stat['recall']+df_work_stat['precision'])

    recommend_user_ids = list()
    # tier_1st: fast and accurate worker(upper 25% of f1 score & upper 25% of speed)
    tier_1st = df_work_stat[
        (df_work_stat.f1 >= df_work_stat.f1.quantile(0.75))
        & (df_work_stat.time_by_inst <= df_work_stat.time_by_inst.quantile(0.25))
    ]['user_id']
    # tier_2nd: accurate but a little slow worker(upper 25% of f1 score & speed between upper 25% and 50%)
    tier_2nd = df_work_stat[
        (df_work_stat.f1 >= df_work_stat.f1.quantile(0.75))
        & (df_work_stat.time_by_inst <= df_work_stat.time_by_inst.quantile(0.5))
        & (df_work_stat.time_by_inst > df_work_stat.time_by_inst.quantile(0.25))
    ]['user_id']
    recommend_user_ids.extend(list(tier_1st))
    recommend_user_ids.extend(list(tier_2nd))
    return recommend_user_ids