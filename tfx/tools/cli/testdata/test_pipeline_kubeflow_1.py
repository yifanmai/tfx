# Copyright 2019 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Test pipeline for Kubeflow."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from tfx.orchestration.kubeflow import kubeflow_e2e_test
from tfx.orchestration.kubeflow import test_utils
from tfx.orchestration.kubeflow.kubeflow_dag_runner import KubeflowDagRunner


def _create_pipeline():
  pipeline_name = 'chicago_taxi_pipeline_kubeflow_1'
  components = kubeflow_e2e_test._create_e2e_components(  # pylint: disable=protected-access
      test_utils._pipeline_root(pipeline_name),  # pylint: disable=protected-access
      test_utils._data_root,  # pylint: disable=protected-access
      test_utils._taxi_module_file)  # pylint: disable=protected-access
  pipeline = test_utils._create_pipeline(pipeline_name, components)  # pylint: disable=protected-access
  return pipeline


_ = KubeflowDagRunner().run(_create_pipeline())
