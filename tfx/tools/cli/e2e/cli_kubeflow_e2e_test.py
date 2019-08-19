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
"""E2E Kubeflow tests for CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import codecs
import locale
import logging
import os
import sys

from click import testing as click_testing
import tensorflow as tf

from tfx.orchestration.kubeflow import test_utils
from tfx.tools.cli.cli_main import cli_group


class CliKubeflowE2eTest(test_utils.BaseKubeflowTest):

  def setUp(self):
    super(CliKubeflowE2eTest, self).setUp()

    # Change the encoding for Click since Python 3 is configured to use ASCII as
    # encoding for the environment.
    if codecs.lookup(locale.getpreferredencoding()).name == 'ascii':
      os.environ['LANG'] = 'en_US.utf-8'

    # Initialize CLI runner.
    self.runner = click_testing.CliRunner()

    # Testdata path.
    self._testdata_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'testdata')

    # Kubeflow home
    self._old_kubeflow_home = os.environ.get('KUBEFLOW_HOME')
    os.environ['KUBEFLOW_HOME'] = self._test_dir

  def tearDown(self):
    super(CliKubeflowE2eTest, self).tearDown()
    if self._old_kubeflow_home:
      os.environ['KUBEFLOW_HOME'] = self._old_kubeflow_home

  def testPipelineCreateAutoDetect(self):
    pipeline_path = os.path.join(self._testdata_dir,
                                 'test_pipeline_kubeflow_1.py')
    pipeline_name = 'chicago_taxi_pipeline_kubeflow_1'
    handler_pipeline_path = os.path.join(self._kubeflow_home, pipeline_name)
    result = self.runner.invoke(cli_group, [
        'pipeline', 'create', '--engine', 'auto', '--pipeline_path',
        pipeline_path
    ])
    self.assertIn('CLI', result.output)
    self.assertIn('Creating pipeline', result.output)
    self.assertIn('Detected Kubeflow', result.output)
    self.assertTrue(
        tf.io.gfile.exists(
            os.path.join(handler_pipeline_path, 'pipeline_args.json')))
    self.assertIn('Pipeline "{}" created successfully.'.format(pipeline_name),
                  result.output)


if __name__ == '__main__':
  logging.basicConfig(stream=sys.stdout, level=logging.INFO)
  tf.test.main()
