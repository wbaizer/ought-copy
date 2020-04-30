from http import HTTPStatus

import numpy as np
import pandas as pd
import pytest
import scipy.stats  # type: ignore

import ergo


class TestForetold:
    def test_foretold_sampling(self):
        foretold = ergo.Foretold()
        # https://www.foretold.io/c/f45577e4-f1b0-4bba-8cf6-63944e63d70c/m/cf86da3f-c257-4787-b526-3ef3cb670cb4
        # Distribution is mm(10 to 20, 200 to 210), a mixture model with most mass split between
        # 10 - 20 and 200 - 210.
        dist = foretold.get_question("cf86da3f-c257-4787-b526-3ef3cb670cb4")
        assert dist.quantile(0.25) < 100
        assert dist.quantile(0.75) > 100

        num_samples = 20000
        samples = ergo.run(
            lambda: ergo.tag(dist.sample_community(), "sample"), num_samples=num_samples
        )
        # Probability mass is split evenly between both modes of the distribution, so approximately half of the
        # samples should be lower than 100
        assert np.count_nonzero(samples > 100) == pytest.approx(num_samples / 2, 0.1)

    def test_foretold_multiple_questions(self):
        foretold = ergo.Foretold()
        # https://www.foretold.io/c/f45577e4-f1b0-4bba-8cf6-63944e63d70c/m/cf86da3f-c257-4787-b526-3ef3cb670cb4

        ids = [
            "cf86da3f-c257-4787-b526-3ef3cb670cb4",
            "77936da2-a581-48c7-add1-8a4ebc647c8c",
            "9b0b01fb-f439-4bbe-8722-f57034ffc96e",
        ]
        has_community_prediction_list = [True, True, False]
        questions = foretold.get_questions(ids)
        for id, question, has_community_prediction in zip(
            ids, questions, has_community_prediction_list
        ):
            assert question is not None
            assert question.id == id
            assert question.community_prediction_available == has_community_prediction

    def test_foretold_multiple_questions_error(self):
        foretold = ergo.Foretold()
        with pytest.raises(NotImplementedError):
            ids = ["cf86da3f-c257-4787-b526-3ef3cb670cb4"] * 1000
            foretold.get_questions(ids)

    def test_cdf_from_samples_numpy(self):
        samples = np.random.normal(loc=0, scale=1, size=1000)
        cdf = ergo.foretold.ForetoldCdf.from_samples(samples, length=100)
        xs = np.array(cdf.xs)
        ys = np.array(cdf.ys)
        true_ys = scipy.stats.norm.cdf(xs, loc=0, scale=1)
        assert len(cdf.xs) == 100
        assert len(cdf.ys) == 100
        assert type(cdf.xs[0]) == float
        assert type(cdf.ys[0]) == float
        # Check that `xs` is sorted as expected by Foretold.
        assert np.all(np.diff(xs) >= 0)
        assert np.all(0 <= ys) and np.all(ys <= 1)
        assert np.all(np.abs(true_ys - ys) < 0.1)

    def test_cdf_from_samples_pandas(self):
        df = pd.DataFrame({"samples": np.random.normal(loc=0, scale=1, size=100)})
        cdf = ergo.foretold.ForetoldCdf.from_samples(df["samples"], length=50)
        assert len(cdf.xs) == 50
        assert len(cdf.ys) == 50
        assert type(cdf.xs[0]) == float
        assert type(cdf.ys[0]) == float

    def test_measurement_query(self):
        cdf = ergo.foretold.ForetoldCdf([0.0, 1.0, 2.0], [1.0, 2.0, 3.0])
        query = ergo.foretold._measurement_query(
            "cf86da3f-c257-4787-b526-3ef3cb670cb4", cdf
        )
        assert type(query) == str

    @pytest.mark.skip(reason="API token required")
    def test_create_measurement(self):
        foretold = ergo.Foretold(token="")
        question = foretold.get_question("cf86da3f-c257-4787-b526-3ef3cb670cb4")
        samples = np.random.normal(loc=150, scale=5, size=1000)
        r = question.submit_from_samples(samples, length=20)
        assert r.status_code == HTTPStatus.OK
