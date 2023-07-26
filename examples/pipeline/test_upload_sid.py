#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
from fate_client.pipeline import FateFlowPipeline

pipeline = FateFlowPipeline().set_roles(
    local="0")
pipeline.set_site_role("local")
pipeline.set_site_party_id("0")

meta = {'delimiter': ',',
        'dtype': 'float64',
        'input_format': 'dense',
        'label_type': 'int64',
        'label_name': 'y',
        'match_id_name': 'id',
        'match_id_range': 0,
        'sample_id_name': 'sid',
        'tag_value_delimiter': ':',
        'tag_with_value': False,
        'weight_type': 'float64'}

pipeline.transform_local_file_to_dataframe("/Users/yuwu/PycharmProjects/FATE/examples/data/breast_hetero_guest_sid.csv",
                                           meta=meta, head=True, extend_sid=False,
                                           namespace="experiment_sid",
                                           name="breast_hetero_guest")

meta = {'delimiter': ',',
        'dtype': 'float64',
        'input_format': 'dense',
        'label_type': 'int64',
        'sample_id_name': 'sid',
        'match_id_range': 0,
        'match_id_name': 'id',
        'tag_value_delimiter': ':',
        'tag_with_value': False,
        'weight_type': 'float64'}

pipeline.transform_local_file_to_dataframe("/Users/yuwu/PycharmProjects/FATE/examples/data/breast_hetero_host_sid.csv",
                                           meta=meta, head=True, extend_sid=False,
                                           namespace="experiment_sid",
                                           name="breast_hetero_host")
