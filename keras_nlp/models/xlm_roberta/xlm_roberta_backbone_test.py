# Copyright 2023 The KerasNLP Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import numpy as np
import pytest
import tensorflow as tf

from keras_nlp.backend import keras
from keras_nlp.backend import ops
from keras_nlp.models.xlm_roberta.xlm_roberta_backbone import XLMRobertaBackbone
from keras_nlp.tests.test_case import TestCase


class XLMRobertaBackboneTest(TestCase):
    def setUp(self):
        self.backbone = XLMRobertaBackbone(
            vocabulary_size=10,
            num_layers=2,
            num_heads=2,
            hidden_dim=2,
            intermediate_dim=4,
            max_sequence_length=5,
        )
        self.input_batch = {
            "token_ids": np.ones((2, 5), dtype="int32"),
            "padding_mask": np.ones((2, 5), dtype="int32"),
        }
        self.input_dataset = tf.data.Dataset.from_tensor_slices(
            self.input_batch
        ).batch(2)

    def test_valid_call_xlm_roberta(self):
        self.backbone(self.input_batch)

    def test_token_embedding(self):
        output = self.backbone.token_embedding(self.input_batch["token_ids"])
        self.assertEqual(output.shape, (2, 5, 2))

    def test_name(self):
        # Check default name passed through
        self.assertRegexpMatches(self.backbone.name, "xlm_roberta_backbone")

    def test_variable_sequence_length_call_xlm_roberta(self):
        for seq_length in (2, 3, 4):
            input_data = {
                "token_ids": np.ones((2, seq_length), dtype="int32"),
                "padding_mask": np.ones((2, seq_length), dtype="int32"),
            }
            output = self.backbone(input_data)
            self.assertAllEqual(
                ops.shape(output),
                (2, seq_length, self.backbone.hidden_dim),
            )

    def test_predict(self):
        self.backbone.predict(self.input_batch)
        self.backbone.predict(self.input_dataset)

    def test_serialization(self):
        new_backbone = keras.saving.deserialize_keras_object(
            keras.saving.serialize_keras_object(self.backbone)
        )
        self.assertEqual(new_backbone.get_config(), self.backbone.get_config())

    @pytest.mark.large  # Saving is slow, so mark these large.
    def test_saved_model(self):
        model_output = self.backbone(self.input_batch)
        path = os.path.join(self.get_temp_dir(), "model.keras")
        self.backbone.save(path, save_format="keras_v3")
        restored_model = keras.models.load_model(path)

        # Check we got the real object back.
        self.assertIsInstance(restored_model, XLMRobertaBackbone)

        # Check that output matches.
        restored_output = restored_model(self.input_batch)
        self.assertAllClose(model_output, restored_output)


@pytest.mark.tpu
@pytest.mark.usefixtures("tpu_test_class")
class XLMRobertaBackboneTPUTest(TestCase):
    def setUp(self):
        with self.tpu_strategy.scope():
            self.backbone = XLMRobertaBackbone(
                vocabulary_size=1000,
                num_layers=2,
                num_heads=2,
                hidden_dim=64,
                intermediate_dim=128,
                max_sequence_length=128,
            )
        self.input_batch = {
            "token_ids": np.ones((8, 128), dtype="int32"),
            "padding_mask": np.ones((8, 128), dtype="int32"),
        }
        self.input_dataset = tf.data.Dataset.from_tensor_slices(
            self.input_batch
        ).batch(2)

    def test_predict(self):
        self.backbone.compile()
        self.backbone.predict(self.input_dataset)
