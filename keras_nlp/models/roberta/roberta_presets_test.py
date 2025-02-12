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

import pytest
from absl.testing import parameterized

from keras_nlp.backend import ops
from keras_nlp.models.roberta.roberta_backbone import RobertaBackbone
from keras_nlp.models.roberta.roberta_classifier import RobertaClassifier
from keras_nlp.models.roberta.roberta_masked_lm import RobertaMaskedLM
from keras_nlp.models.roberta.roberta_preprocessor import RobertaPreprocessor
from keras_nlp.models.roberta.roberta_tokenizer import RobertaTokenizer
from keras_nlp.tests.test_case import TestCase


@pytest.mark.large
class RobertaPresetSmokeTest(TestCase):
    """
    A smoke test for RoBERTa presets we run continuously.

    This only tests the smallest weights we have available. Run with:
    `pytest keras_nlp/models/roberta/roberta_presets_test.py --run_large`
    """

    def test_tokenizer_output(self):
        tokenizer = RobertaTokenizer.from_preset(
            "roberta_base_en",
        )
        outputs = tokenizer("The quick brown fox.")
        expected_outputs = [133, 2119, 6219, 23602, 4]
        self.assertAllEqual(outputs, expected_outputs)

    def test_preprocessor_output(self):
        preprocessor = RobertaPreprocessor.from_preset(
            "roberta_base_en",
            sequence_length=4,
        )
        outputs = preprocessor("The quick brown fox.")["token_ids"]
        expected_outputs = [0, 133, 2119, 2]
        self.assertAllEqual(outputs, expected_outputs)

    @parameterized.named_parameters(
        ("preset_weights", True), ("random_weights", False)
    )
    def test_backbone_output(self, load_weights):
        input_data = {
            "token_ids": ops.array([[0, 133, 2119, 2]]),
            "padding_mask": ops.array([[1, 1, 1, 1]]),
        }
        model = RobertaBackbone.from_preset(
            "roberta_base_en", load_weights=load_weights
        )
        outputs = model(input_data)
        if load_weights:
            outputs = outputs[0, 0, :5]
            expected = [-0.051, 0.100, -0.010, -0.097, 0.059]
            self.assertAllClose(outputs, expected, atol=0.01, rtol=0.01)

    @parameterized.named_parameters(
        ("preset_weights", True), ("random_weights", False)
    )
    def test_classifier_output(self, load_weights):
        input_data = ["Let's rock!"]
        model = RobertaClassifier.from_preset(
            "roberta_base_en", num_classes=2, load_weights=load_weights
        )
        # Never assert output values, as the head weights are random.
        model.predict(input_data)

    @parameterized.named_parameters(
        ("load_weights", True), ("no_load_weights", False)
    )
    def test_classifier_output_without_preprocessing(self, load_weights):
        input_data = {
            "token_ids": ops.array([[101, 1996, 4248, 102]]),
            "padding_mask": ops.array([[1, 1, 1, 1]]),
        }
        model = RobertaClassifier.from_preset(
            "roberta_base_en",
            num_classes=2,
            load_weights=load_weights,
            preprocessor=None,
        )
        # Never assert output values, as the head weights are random.
        model.predict(input_data)

    @parameterized.named_parameters(
        ("preset_weights", True), ("random_weights", False)
    )
    def test_masked_lm_output(self, load_weights):
        input_data = ["Let's rock!"]
        model = RobertaMaskedLM.from_preset(
            "roberta_base_en", load_weights=load_weights
        )
        # Never assert output values, as the head weights are random.
        model.predict(input_data)

    @parameterized.named_parameters(
        ("load_weights", True), ("no_load_weights", False)
    )
    def test_masked_lm_output_without_preprocessing(self, load_weights):
        input_data = {
            "token_ids": ops.array([[101, 1996, 4248, 102]]),
            "padding_mask": ops.array([[1, 1, 1, 1]]),
            "mask_positions": ops.array([[0, 0]]),
        }
        model = RobertaMaskedLM.from_preset(
            "roberta_base_en",
            load_weights=load_weights,
            preprocessor=None,
        )
        # Never assert output values, as the head weights are random.
        model.predict(input_data)

    @parameterized.named_parameters(
        ("roberta_tokenizer", RobertaTokenizer),
        ("roberta_preprocessor", RobertaPreprocessor),
        ("roberta", RobertaBackbone),
        ("roberta_classifier", RobertaClassifier),
        ("roberta_masked_lm", RobertaMaskedLM),
    )
    def test_preset_docstring(self, cls):
        """Check we did our docstring formatting correctly."""
        for name in cls.presets:
            self.assertRegex(cls.from_preset.__doc__, name)

    @parameterized.named_parameters(
        ("roberta_tokenizer", RobertaTokenizer, {}),
        ("roberta_preprocessor", RobertaPreprocessor, {}),
        ("roberta", RobertaBackbone, {}),
        ("roberta_classifier", RobertaClassifier, {"num_classes": 2}),
        ("roberta_masked_lm", RobertaMaskedLM, {}),
    )
    def test_unknown_preset_error(self, cls, kwargs):
        # Not a preset name
        with self.assertRaises(ValueError):
            cls.from_preset("roberta_base_en_clowntown", **kwargs)


@pytest.mark.extra_large
class RobertaPresetFullTest(TestCase):
    """
    Test the full enumeration of our preset.

    This tests every RoBERTa preset and is only run manually.
    Run with:
    `pytest keras_nlp/models/roberta/roberta_presets_test.py --run_extra_large`
    """

    @parameterized.named_parameters(
        ("preset_weights", True), ("random_weights", False)
    )
    def test_load_roberta(self, load_weights):
        for preset in RobertaBackbone.presets:
            model = RobertaBackbone.from_preset(
                preset, load_weights=load_weights
            )
            input_data = {
                "token_ids": ops.random.uniform(
                    shape=(1, 512), dtype="int64", maxval=model.vocabulary_size
                ),
                "padding_mask": ops.array([1] * 512, shape=(1, 512)),
            }
            model(input_data)

    @parameterized.named_parameters(
        ("preset_weights", True), ("random_weights", False)
    )
    def test_load_roberta_classifier(self, load_weights):
        for preset in RobertaClassifier.presets:
            classifier = RobertaClassifier.from_preset(
                preset, num_classes=4, load_weights=load_weights
            )
            input_data = ["The quick brown fox."]
            classifier.predict(input_data)

    @parameterized.named_parameters(
        ("load_weights", True), ("no_load_weights", False)
    )
    def test_load_roberta_classifier_without_preprocessing(self, load_weights):
        for preset in RobertaClassifier.presets:
            classifier = RobertaClassifier.from_preset(
                preset,
                num_classes=2,
                preprocessor=None,
                load_weights=load_weights,
            )
            input_data = {
                "token_ids": ops.random.uniform(
                    shape=(1, 512),
                    dtype="int64",
                    maxval=classifier.backbone.vocabulary_size,
                ),
                "padding_mask": ops.array([1] * 512, shape=(1, 512)),
            }
            classifier.predict(input_data)

    @parameterized.named_parameters(
        ("preset_weights", True), ("random_weights", False)
    )
    def test_load_roberta_masked_lm(self, load_weights):
        for preset in RobertaMaskedLM.presets:
            classifier = RobertaMaskedLM.from_preset(
                preset, load_weights=load_weights
            )
            input_data = ["The quick brown fox."]
            classifier.predict(input_data)

    @parameterized.named_parameters(
        ("load_weights", True), ("no_load_weights", False)
    )
    def test_load_roberta_masked_lm_without_preprocessing(self, load_weights):
        for preset in RobertaMaskedLM.presets:
            classifier = RobertaMaskedLM.from_preset(
                preset,
                preprocessor=None,
                load_weights=load_weights,
            )
            input_data = {
                "token_ids": ops.random.uniform(
                    shape=(1, 512),
                    dtype="int64",
                    maxval=classifier.backbone.vocabulary_size,
                ),
                "padding_mask": ops.array([1] * 512, shape=(1, 512)),
                "mask_positions": ops.array([1] * 128, shape=(1, 128)),
            }
            classifier.predict(input_data)

    def test_load_tokenizers(self):
        for preset in RobertaTokenizer.presets:
            tokenizer = RobertaTokenizer.from_preset(preset)
            tokenizer("The quick brown fox.")

    def test_load_preprocessors(self):
        for preset in RobertaPreprocessor.presets:
            preprocessor = RobertaPreprocessor.from_preset(preset)
            preprocessor("The quick brown fox.")
