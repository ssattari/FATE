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
#
import argparse
from fate_client.pipeline.utils import test_utils
from fate_client.pipeline import FateFlowPipeline
from fate_client.pipeline.components.fate.nn.torch import nn, optim
from fate_client.pipeline.components.fate.nn.torch.base import Sequential
from fate_client.pipeline.components.fate.hetero_nn import HeteroNN, get_config_of_default_runner
from fate_client.pipeline.components.fate.reader import Reader
from fate_client.pipeline.components.fate.psi import PSI
from fate_client.pipeline.components.fate.nn.algo_params import TrainingArguments, SSHEArgument
from fate_client.pipeline.components.fate import Evaluation


def main(config="../../config.yaml", namespace=""):
    # obtain config
    if isinstance(config, str):
        config = test_utils.load_job_config(config)
    parties = config.parties
    guest = parties.guest[0]
    host = parties.host[0]

    pipeline = FateFlowPipeline().set_parties(guest=guest, host=host)

    reader_0 = Reader("reader_0", runtime_parties=dict(guest=guest, host=host))
    reader_0.guest.task_parameters(
        namespace=f"experiment{namespace}",
        name="breast_hetero_guest"
    )
    reader_0.hosts[0].task_parameters(
        namespace=f"experiment{namespace}",
        name="breast_hetero_host"
    )
    psi_0 = PSI("psi_0", input_data=reader_0.outputs["output_data"])

    training_args = TrainingArguments(
            num_train_epochs=1,
            per_device_train_batch_size=256,
            logging_strategy='epoch',
            log_level='debug'
        )

    guest_conf = get_config_of_default_runner(
        bottom_model=nn.Linear(10, 10),
        top_model=Sequential(
            nn.Linear(10, 1),
            nn.Sigmoid()
        ),
        training_args=training_args,
        optimizer=optim.Adam(lr=0.01),
        loss=nn.BCELoss(),
        agglayer_arg=SSHEArgument(
            guest_in_features=10,
            host_in_features=10,
            out_features=10
        )
    )

    host_conf = get_config_of_default_runner(
        bottom_model=nn.Linear(20, 10),
        optimizer=optim.Adam(lr=0.01),
        training_args=training_args,
        agglayer_arg=SSHEArgument(
            guest_in_features=10,
            host_in_features=10,
            out_features=10
        )
    )

    hetero_nn_0 = HeteroNN(
        'hetero_nn_0',
        train_data=psi_0.outputs['output_data'], validate_data=psi_0.outputs['output_data']
    )

    hetero_nn_0.guest.task_parameters(runner_conf=guest_conf)
    hetero_nn_0.hosts[0].task_parameters(runner_conf=host_conf)

    hetero_nn_1 = HeteroNN(
        'hetero_nn_1',
        test_data=psi_0.outputs['output_data'],
        predict_model_input=hetero_nn_0.outputs['train_model_output']
    )

    evaluation_0 = Evaluation(
        'eval_0',
        runtime_parties=dict(guest=guest),
        metrics=['auc'],
        input_data=[hetero_nn_0.outputs['train_data_output'], hetero_nn_1.outputs['predict_data_output']]
    )

    pipeline.add_tasks([reader_0, psi_0, hetero_nn_0, hetero_nn_1, evaluation_0])
    pipeline.compile()
    pipeline.fit()

    result_summary = pipeline.get_task_info("eval_0").get_output_metric()[0]["data"]
    print(f"result_summary: {result_summary}")

if __name__ == "__main__":

    parser = argparse.ArgumentParser("PIPELINE DEMO")
    parser.add_argument("--config", type=str, default="../config.yaml",
                        help="config file")
    parser.add_argument("--namespace", type=str, default="",
                        help="namespace for data stored in FATE")
    args = parser.parse_args()
    main(config=args.config, namespace=args.namespace)
