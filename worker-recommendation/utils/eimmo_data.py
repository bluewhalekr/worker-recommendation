import pymongo
import pandas as pd
from bson.objectid import ObjectId


class DataExtractor:
    """Extract Data from GTaaS eimmo."""
    def __init__(self, user='datalab', password='vAhm2lF4S30DsbwP'):
        self.user = user
        self.password = password
        self.conn = pymongo.MongoClient('mongodb+srv://{0}:{1}@eimmo-gtaas-prod.1jkei.azure.mongodb.net/eimmo?retryWrites=true&w=majority'.format(self.user, self.password))
        self.db = self.conn.eimmo
    
    def get_all_projects_info(self):
        """Get all projects information.

        Args:
            None
        
        Returns:
            pandas.DataFrame
                Index:
                    RangeIndex
                Columns:
                    _id: project_id, dtype: str
                    name: project_name, dtype: str
                    annotation_type: annotation_type, dtype: str
                    classes: class_information, dtype: list
                    stages: stage_id, dtype: list

        """
        db_prj = self.db['project']
        pipelines = list()
        pipelines.append({'$unwind': '$annotation_configs'})
        pipelines.append(
            {
                '$match': {'annotation_configs.is_active': True, 
                        'participant_count': {'$gt': 10}}
            }
        )
        pipelines.append(
            {
                '$project': {'_id': 1, 
                            'name': 1, 
                            'annotation_configs.annotation_type': 1,
                            'annotation_configs.class_items': 1,
                            'stage_configs': 1}
            }
        )
        df_prj = pd.DataFrame(db_prj.aggregate(pipelines))
        
        df_prj['annotation_type'] = df_prj['annotation_configs'].map(
            lambda x: x['annotation_type']
        )
        df_prj['classes'] = df_prj['annotation_configs'].map(
            lambda x: [i['name'] for i in x['class_items']]
        )
        df_prj['stages'] = df_prj['stage_configs'].map(
            lambda x: [i['id'] for i in x]
        )
        df_prj = df_prj.drop(['annotation_configs', 'stage_configs'], axis=1)
        
        return df_prj

    def get_workers_stat(self, prj_id, stage_id):
        """Get workers' stats at certain stage of the project.

        Args:
            prj_id(str): Project ID
            stage_id(str): Stage ID
        
        Returns:
            pandas.DataFrame
                Index:
                    RangeIndex
                Columns:
                    user_id: user_id, dtype: str
                    file_cnt: number of files, dtype: int
                    created: number of created instances, dtype: int
                    deleted: number of deleted instances, dtype: int
                    updated: number of updated instances, dtype: int
                    unchanged: number of unchanged instance, dtype: int
                    total: sum of created, deleted, updated, unchanged instances, dtype: int
                    work_time: working time, dtype: float
                    idle_time: idle time, dtype: float
                    att_eval_total: total number of attributes, dtype: int
                    att_eval_missing: number of missed attributes, dtype: int
                    att_eval_error: number of error attributes, dtype: int
                    geo_eval_total: total number of instances, dtype: int
                    geo_eval_missing: number of missed instances, dtype: int
                    geo_eval_error: number of error instances, dtype: int

        """
        prj_id = str(prj_id)
        collection = '_worker_session_stat_' + prj_id
        db_work = self.db[collection]
        try:
            if not db_work.count_documents({}):
                raise Exception('No working records at the project')
        except Exception as e:
            print(e)
            raise

        pipelines = list()
        pipelines.append(
            {
                '$match': {'session_result': {'$in': ['done', 'rework']},
                        'rework': False,
                        'stage_id': ObjectId(str(stage_id))}
            }
        )
        pipelines.append({'$unwind': '$answer_changes'})
        pipelines.append(
            {
                '$group': {'_id': {'user_id': '$user_id', 'rework': '$rework'},
                        'file_cnt': {'$sum': 1},
                        'created': {'$sum': '$answer_changes.created'},
                        'deleted': {'$sum': '$answer_changes.deleted'},
                        'updated': {'$sum': '$answer_changes.updated'},
                        'unchanged': {'$sum': '$answer_changes.unchanged'},
                        'total': {'$sum': {'$sum': ['$answer_changes.created', 
                                                    '$answer_changes.deleted', 
                                                    '$answer_changes.updated', 
                                                    '$answer_changes.unchanged']}},
                        'work_time': {'$sum': '$studio_open_duration'},
                        'idle_time': {'$sum': '$idle_duration'},
                        'att_eval_total': {'$sum': '$attribute_evaluation.total'},
                        'att_eval_missing': {'$sum': '$attribute_evaluation.missing'},
                        'att_eval_error': {'$sum': '$attribute_evaluation.error'},
                        'geo_eval_total': {'$sum': '$geometric_evaluation.total'},
                        'geo_eval_missing': {'$sum': '$geometric_evaluation.missing'},
                        'geo_eval_error': {'$sum': '$geometric_evaluation.error'}}
            }
        )
        pipelines.append(
            {
                '$project': {'_id': 0,
                            'user_id': '$_id.user_id',
                            'file_cnt': 1,
                            'created': 1,
                            'deleted': 1,
                            'updated': 1,
                            'unchanged': 1,
                            'total': 1,
                            'work_time': 1,
                            'idle_time': 1,
                            'att_eval_total': 1,
                            'att_eval_missing': 1,
                            'att_eval_error': 1,
                            'geo_eval_total': 1,
                            'geo_eval_missing': 1,
                            'geo_eval_error': 1}
            }
        )
        df_work = pd.DataFrame(db_work.aggregate(pipelines))
        
        return df_work
