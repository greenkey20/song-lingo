"""azure_pronunciation.parse_assessment 단위 테스트. 네트워크·키 없이 저장해 둔 JSON(Microsoft 문서의 예시 구조를 줄인 것)만 쓴다."""
import json
import os
import tempfile
import unittest
from pathlib import Path

import numpy as np

import recorder

import azure_pronunciation as ap


def hello_result(**override):
    """문서의 'hello' 예시(점수 5개 중 운율 없음). 두 번째 음소에서 기대한 음소(ɛ)보다 ə가 더 높게 들린 경우를 포함."""
    result = {
        "Id": "x", "RecognitionStatus": 0, "Offset": 7500000, "Duration": 13800000, "DisplayText": "Hello.",
        "NBest": [{
            "Confidence": 0.97, "Display": "Hello.",
            "PronunciationAssessment": {"AccuracyScore": 100, "FluencyScore": 100, "CompletenessScore": 100, "PronScore": 100},
            "Words": [{
                "Word": "hello", "Offset": 7500000, "Duration": 13800000,
                "PronunciationAssessment": {"AccuracyScore": 99.0, "ErrorType": "None"},
                "Syllables": [
                    {"Syllable": "hɛ", "PronunciationAssessment": {"AccuracyScore": 91.0}, "Offset": 7500000, "Duration": 4100000},
                    {"Syllable": "loʊ", "PronunciationAssessment": {"AccuracyScore": 100.0}, "Offset": 11700000, "Duration": 9600000}],
                "Phonemes": [
                    {"Phoneme": "h", "PronunciationAssessment": {"AccuracyScore": 98.0, "NBestPhonemes": [
                        {"Phoneme": "h", "Score": 100.0}, {"Phoneme": "oʊ", "Score": 52.0}]}, "Offset": 7500000, "Duration": 3500000},
                    {"Phoneme": "ɛ", "PronunciationAssessment": {"AccuracyScore": 47.0, "NBestPhonemes": [
                        {"Phoneme": "ə", "Score": 52.0}, {"Phoneme": "ɛ", "Score": 47.0}, {"Phoneme": "æ", "Score": 17.0}]},
                     "Offset": 11000000, "Duration": 700000}],
            }],
        }],
    }
    result.update(override)
    return result


class Parse(unittest.TestCase):
    def test_scores_and_text(self):
        out = ap.parse_assessment(hello_result())
        self.assertEqual(out["text"], "Hello.")
        self.assertEqual(out["scores"], {"accuracy": 100.0, "fluency": 100.0, "completeness": 100.0, "prosody": None, "pronunciation": 100.0})
        self.assertFalse(out["locale_has_prosody"])                       # 운율 점수는 영어에서만, 없으면 None

    def test_word_times_are_seconds(self):
        w = ap.parse_assessment(hello_result())["words"][0]
        self.assertAlmostEqual(w["start"], 0.75)                           # 7500000 × 100 ns
        self.assertAlmostEqual(w["duration"], 1.38)
        self.assertEqual((w["word"], w["accuracy"], w["level"], w["error_type"]), ("hello", 99.0, "good", "None"))
        self.assertEqual([s["syllable"] for s in w["syllables"]], ["hɛ", "loʊ"])

    def test_phoneme_heard_only_when_it_differs(self):
        ph = ap.parse_assessment(hello_result())["words"][0]["phonemes"]
        self.assertIsNone(ph[0]["heard"])                                  # h는 기대한 음소가 1등
        self.assertEqual((ph[1]["phoneme"], ph[1]["heard"], ph[1]["accuracy"]), ("ɛ", "ə", 47.0))   # ɛ를 기대했는데 ə로 들림

    def test_weak_words_by_level_or_error(self):
        r = hello_result()
        words = r["NBest"][0]["Words"]
        words[0]["PronunciationAssessment"] = {"AccuracyScore": 55.0, "ErrorType": "Mispronunciation"}
        words.append({"Word": "world", "PronunciationAssessment": {"AccuracyScore": 90.0, "ErrorType": "Omission"}})
        words.append({"Word": "again", "PronunciationAssessment": {"AccuracyScore": 95.0, "ErrorType": "None"}})
        out = ap.parse_assessment(r)
        self.assertEqual([w["word"] for w in out["weak_words"]], ["hello", "world"])   # 점수가 낮거나(poor) 오류 종류가 있는 단어
        self.assertEqual(out["words"][2]["level"], "good")
        self.assertIsNone(out["words"][1]["start"])                                    # Offset이 없는 단어(빠진 단어)도 깨지지 않는다

    def test_prosody_scores_and_feedback(self):
        r = hello_result()
        r["NBest"][0]["PronunciationAssessment"]["ProsodyScore"] = 71.5
        r["NBest"][0]["Words"][0]["Feedback"] = {"Prosody": {"Break": {"ErrorTypes": ["UnexpectedBreak"]},
                                                              "Intonation": {"ErrorTypes": ["Monotone"]}}}
        out = ap.parse_assessment(r)
        self.assertEqual(out["scores"]["prosody"], 71.5)
        self.assertTrue(out["locale_has_prosody"])
        self.assertEqual(out["words"][0]["prosody"]["break"], ["UnexpectedBreak"])
        self.assertEqual(out["words"][0]["prosody"]["intonation"], ["Monotone"])
        self.assertEqual(ap.parse_assessment(hello_result())["words"][0]["prosody"],
                         {"break": [], "break_confidence": {"unexpected": None, "missing": None}, "intonation": []})   # 피드백이 없으면 빈 값

    def test_accepts_json_text_and_bytes(self):
        text = json.dumps(hello_result(), ensure_ascii=False)
        self.assertEqual(ap.parse_assessment(text)["text"], "Hello.")
        self.assertEqual(ap.parse_assessment(text.encode("utf-8"))["text"], "Hello.")

    def test_status_success_string(self):
        self.assertEqual(ap.parse_assessment(hello_result(RecognitionStatus="Success"))["text"], "Hello.")


class BreakConfidence(unittest.TestCase):
    def _with_break(self, unexpected=None, missing=None, error_types=None):
        r = hello_result()
        brk = {}
        if unexpected is not None:
            brk["UnexpectedBreak"] = {"Confidence": unexpected}
        if missing is not None:
            brk["MissingBreak"] = {"Confidence": missing}
        if error_types is not None:
            brk["ErrorTypes"] = error_types
        r["NBest"][0]["Words"][0]["Feedback"] = {"Prosody": {"Break": brk}}
        return ap.parse_assessment(r)["words"][0]["prosody"]

    def test_confidence_above_threshold_becomes_break_kind(self):
        # 공식 문서의 권장 임계값 0.75: 0.75보다 크면 쉼 오류로 본다(0.75 자체는 아님)
        self.assertEqual(self._with_break(unexpected=0.83, missing=0.01)["break"], ["UnexpectedBreak"])
        self.assertEqual(self._with_break(unexpected=0.1, missing=0.9)["break"], ["MissingBreak"])
        self.assertEqual(self._with_break(unexpected=0.75, missing=0.75)["break"], [])
        self.assertEqual(self._with_break(unexpected=0.83)["break_confidence"], {"unexpected": 0.83, "missing": None})

    def test_error_types_in_json_are_kept_without_duplicates(self):
        self.assertEqual(self._with_break(unexpected=0.9, error_types=["UnexpectedBreak"])["break"], ["UnexpectedBreak"])


class PronScoreFormula(unittest.TestCase):
    """Azure 공식 종합 점수 공식이 실제 결과(11-05, 사용자 호출 5건)의 PronScore와 맞는지."""
    CASES = [  # (정확도, 유창성, 완성도, 운율, Azure가 돌려준 종합)
        (91.0, 99.0, 100.0, 88.3, 93.3),   # 첫 호출 s01_take1
        (81, 90, 71, 81, 79),              # ① 정상
        (32, 77, 14, 69, 41),              # ② 단어 생략
        (45, 49, 14, 66, 38),              # ③ 끊어 읽기
        (56, 88, 43, 74, 61),              # ④ 틀린 발음
    ]

    def test_reading_formula_with_prosody_matches_azure(self):
        for acc, flu, comp, pros, pron in self.CASES:
            self.assertAlmostEqual(ap.expected_pron_score(acc, flu, comp, pros), pron, delta=0.5, msg=(acc, flu, comp, pros))

    def test_lowest_score_has_the_biggest_weight(self):
        self.assertAlmostEqual(ap.expected_pron_score(100, 100, 0, 100), 60.0)       # 한 항목이 0이면 종합은 평균(75)이 아니라 60: 가장 낮은 점수의 가중치가 0.4
        self.assertAlmostEqual(ap.expected_pron_score(90, 90, 90), 90.0)             # 운율 없으면 셋의 가중 평균

    def test_without_prosody(self):
        self.assertAlmostEqual(ap.expected_pron_score(80, 100, 60), 0.6 * 60 + 0.2 * 80 + 0.2 * 100)


class Failures(unittest.TestCase):
    def test_no_match_status(self):
        with self.assertRaises(ap.AssessmentError) as cm:
            ap.parse_assessment({"RecognitionStatus": "NoMatch"})
        self.assertIn("NoMatch", str(cm.exception))

    def test_missing_nbest_and_assessment(self):
        with self.assertRaises(ap.AssessmentError):
            ap.parse_assessment({"RecognitionStatus": 0, "NBest": []})
        with self.assertRaises(ap.AssessmentError):
            ap.parse_assessment({"RecognitionStatus": 0, "NBest": [{"Words": []}]})        # 평가를 켜지 않고 요청한 경우

    def test_not_an_object(self):
        with self.assertRaises(ap.AssessmentError):
            ap.parse_assessment("[1, 2]")

    def test_error_is_a_value_error(self):
        self.assertTrue(issubclass(ap.AssessmentError, ValueError))


class Level(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual([ap.level(x) for x in (100, 80, 79.9, 60, 59.9, 0)], ["good", "good", "fair", "fair", "poor", "poor"])
        self.assertIsNone(ap.level(None))


def make_wav(seconds, sr=16000, amp=0.5):
    """테스트용 임시 wav(스테레오 PCM16)를 만들어 (임시 폴더, 경로)를 돌려준다."""
    d = tempfile.TemporaryDirectory()
    t = np.arange(int(seconds * sr)) / sr
    x = (amp * np.sin(2 * np.pi * 440 * t)).astype("float32")
    path = recorder.save_wav(Path(d.name) / "x.wav", np.stack([x, x], 1), sr)
    return d, path


class Assess(unittest.TestCase):
    def setUp(self):
        self.d, self.wav = make_wav(1.0)
        self.calls = []

        def fake(pcm, ref, locale, key, region, prosody):
            self.calls.append(dict(n=len(pcm), ref=ref, locale=locale, key=key, region=region, prosody=prosody))
            return json.dumps(hello_result())
        self.fake = fake

    def tearDown(self):
        self.d.cleanup()

    def test_pcm16_bytes_is_raw_16k_mono_int16(self):
        pcm, seconds = ap.pcm16_bytes(self.wav)
        self.assertEqual(len(pcm), 16000 * 2)                      # 1초 × 16000 샘플 × 2바이트(머리글 없음)
        self.assertAlmostEqual(seconds, 1.0)
        peak = int(np.abs(np.frombuffer(pcm, dtype="<i2")).max())
        self.assertAlmostEqual(peak / 32767, 0.5, delta=0.01)      # 진폭 0.5 → 정수로 되돌려도 같은 크기

    def test_pcm16_bytes_accepts_bytes(self):
        pcm, _ = ap.pcm16_bytes(Path(self.wav).read_bytes())
        self.assertEqual(len(pcm), 32000)

    def test_assess_returns_parsed_result_with_locale(self):
        out = ap.assess(self.wav, " Hello. ", key="k", region="r", recognize=self.fake)
        self.assertEqual(out["scores"]["pronunciation"], 100.0)
        self.assertEqual((out["locale"], out["seconds"]), ("en-US", 1.0))
        c = self.calls[0]
        self.assertEqual((c["ref"], c["key"], c["region"], c["n"]), ("Hello.", "k", "r", 32000))   # 문장 앞뒤 공백은 지워서 보냄

    def test_prosody_only_for_en_us_unless_set(self):
        ap.assess(self.wav, "x", "en-US", key="k", region="r", recognize=self.fake)
        ap.assess(self.wav, "x", "ja-JP", key="k", region="r", recognize=self.fake)
        ap.assess(self.wav, "x", "ja-JP", key="k", region="r", prosody=True, recognize=self.fake)
        self.assertEqual([c["prosody"] for c in self.calls], [True, False, True])

    def test_missing_key_stops_before_any_call(self):
        saved = {k: os.environ.pop(k, None) for k in (ap.KEY_ENV, ap.REGION_ENV)}
        try:
            with self.assertRaises(ap.NotConfigured) as cm:
                ap.assess(self.wav, "x", recognize=self.fake)
            self.assertIn(ap.KEY_ENV, str(cm.exception))
            self.assertEqual(self.calls, [])                        # 키가 없으면 녹음을 보내지 않는다
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v

    def test_keys_from_environment(self):
        saved = {k: os.environ.get(k) for k in (ap.KEY_ENV, ap.REGION_ENV)}
        os.environ[ap.KEY_ENV], os.environ[ap.REGION_ENV] = "envkey", "koreacentral"
        try:
            ap.assess(self.wav, "x", recognize=self.fake)
            self.assertEqual((self.calls[0]["key"], self.calls[0]["region"]), ("envkey", "koreacentral"))
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_empty_reference_and_too_long_are_not_sent(self):
        with self.assertRaises(ValueError):
            ap.assess(self.wav, "  ", key="k", region="r", recognize=self.fake)
        d, long_wav = make_wav(31)
        try:
            with self.assertRaises(ap.AssessmentError):
                ap.assess(long_wav, "x", key="k", region="r", recognize=self.fake)
        finally:
            d.cleanup()
        self.assertEqual(self.calls, [])

    def test_azure_failure_propagates_as_assessment_error(self):
        def failing(*a):
            raise ap.AssessmentError("Azure 요청이 취소됐어요(Error): 인증 실패")
        with self.assertRaises(ap.AssessmentError):
            ap.assess(self.wav, "x", key="k", region="r", recognize=failing)

    def test_request_config_asks_for_ipa_and_nbest(self):
        # SDK가 있는 환경(앱)에서만: 요청 설정 JSON에 IPA·음소 후보 5개·빠짐 계산이 실제로 들어가는지. 네트워크는 쓰지 않는다.
        try:
            import azure.cognitiveservices.speech as speechsdk
        except ImportError:
            self.skipTest("azure SDK 없음(voice-ai)")
        cfg = json.loads(ap._pronunciation_config(speechsdk, "hello", prosody=True).to_json())
        self.assertEqual((cfg["phonemeAlphabet"], cfg["nbestPhonemeCount"], cfg["enableMiscue"], cfg["referenceText"]), ("IPA", 5, True, "hello"))
        self.assertEqual((cfg["gradingSystem"], cfg["granularity"]), ("HundredMark", "Phoneme"))

    def test_sdk_is_importable_in_app_env_or_clear_message(self):
        # SDK가 없는 환경(voice-ai)에서는 실제 호출 함수가 NotConfigured로 안내해야 한다. 있으면(앱 환경) 이 검사는 통과로 본다.
        try:
            import azure.cognitiveservices.speech  # noqa: F401
        except ImportError:
            with self.assertRaises(ap.NotConfigured):
                ap._azure_recognize(b"", "x", "en-US", "k", "r", False)


if __name__ == "__main__":
    unittest.main()
