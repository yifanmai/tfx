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
"""TFX Artifact utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import os
import re

from typing import Dict, List, Text

from tfx.types.artifact import Artifact


def parse_artifact_dict(json_str: Text) -> Dict[Text, List[Artifact]]:
  """Parse a dict from key to list of Artifact from its json format."""
  tfx_artifacts = {}
  for k, l in json.loads(json_str).items():
    tfx_artifacts[k] = [Artifact.parse_from_json_dict(v) for v in l]
  return tfx_artifacts


def jsonify_artifact_dict(artifact_dict: Dict[Text, List[Artifact]]) -> Text:
  """Serialize a dict from key to list of Artifact into json format."""
  d = {}
  for k, l in artifact_dict.items():
    d[k] = [v.json_dict() for v in l]
  return json.dumps(d)


def get_single_instance(artifact_list: List[Artifact]) -> Artifact:
  """Get a single instance of Artifact from a list of length one.

  Args:
    artifact_list: A list of Artifact objects whose length must be one.

  Returns:
    The single Artifact object in artifact_list.

  Raises:
    ValueError: If length of artifact_list is not one.
  """
  if len(artifact_list) != 1:
    raise ValueError('expected list length of one but got {}'.format(
        len(artifact_list)))
  return artifact_list[0]


def get_single_uri(artifact_list: List[Artifact]) -> Text:
  """Get the uri of Artifact from a list of length one.

  Args:
    artifact_list: A list of Artifact objects whose length must be one.

  Returns:
    The uri of the single Artifact object in artifact_list.

  Raises:
    ValueError: If length of artifact_list is not one.
  """
  return get_single_instance(artifact_list).uri


def get_split_uri(artifact_list: List[Artifact], split: Text) -> Text:
  """Get the uri of Artifact with matching split from given list.

  Args:
    artifact_list: A list of Artifact objects whose length must be one.
    split: Name of split.

  Returns:
    The uri of Artifact object in artifact_list with matching split.

  Raises:
    ValueError: If number with matching split in artifact_list is not one.
  """
  matching_artifacts = []
  for artifact in artifact_list:
    split_names = decode_split_names(artifact.split_names)
    if split in split_names:
      matching_artifacts.append(artifact)
  if len(matching_artifacts) != 1:
    raise ValueError(
        ('Expected exactly one artifact with split %r, but found matching '
         'artifacts %s.') % (split, matching_artifacts))
  return os.path.join(matching_artifacts[0].uri, split)


def encode_split_names(splits: List[Text]) -> Text:
  for split in splits:
    if not re.match('^[A-Za-z0-9][A-Za-z0-9_-]*$', split):
      raise ValueError(
          ('Split names are expected to be alphanumeric (allowing dashes and '
           'underscores, provided they are not the first character); got %r '
           'instead.') % (split,))
  return ','.join(splits)


def decode_split_names(split_names: Text) -> List[Text]:
  if not split_names:
    return []
  return split_names.split(',')
