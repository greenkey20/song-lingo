"""연습: `pitch.to_word_axis`를 직접 구현해 보기 (이슈 #82, 검토 문서 16.18 6절 "학습 분담").

발표 뒤에 풀어 보는 연습용이다. 정답은 프로젝트의 `pitch.to_word_axis`(같은 함수)이고, 이 파일의 `my_to_word_axis`를 채운 뒤
    /opt/anaconda3/envs/voice-ai/bin/python "experiments/F0/to_word_axis_연습.py"
을 실행하면 정답 함수와 같은 결과가 나오는지 케이스별로 알려 준다(프로젝트 루트에서 실행).

## 문제
프레임마다 시각 times(초)와 값 values가 있다. 기준 문장의 단어 i마다 이 소리에서의 구간 spans[i] = (시작, 끝)(초) 또는 None이 주어진다.
단어 i의 구간 [s, e] 안에 있는 프레임 t를  x = i + (t - s) / (e - s)  로 옮겨서, **같은 단어가 같은 칸(i ~ i+1)** 에 놓이게 하라.

## 규칙(정답과 같아야 하는 것)
1. spans[i]가 None이면 그 단어는 비운다.
2. e - s < min_seconds(0.03초)이면 비운다(진행률 계산이 불안정하다).
3. 구간 안의 프레임은 values가 NaN이어도 **버리지 말고 NaN 그대로** 둔다(그래프에서 선이 끊겨야 하므로).
4. 단어와 단어 사이에 NaN을 **한 칸** 끼운다(x도 y도). 선이 단어 경계를 넘어 이어지지 않게 하려는 것이다. 비운 단어에는 끼우지 않는다.
5. 아무 단어도 그리지 않으면 빈 배열 두 개 (array([]), array([]))를 돌려준다.

## 손으로 먼저 해 보기
times = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5], values = [1, 2, nan, 4, 5, 6], spans = [(0.0, 0.2), None, (0.3, 0.5)]
- 단어 0: t = 0.0, 0.1, 0.2 → x = 0.0, 0.5, 1.0, y = 1, 2, nan, 그리고 구분 NaN
- 단어 2: t = 0.3, 0.4, 0.5 → x = 2 + (t - 0.3)/0.2 = 2.0, 2.5, 3.0, y = 4, 5, 6, 그리고 구분 NaN
→ x = [0, .5, 1, nan, 2, 2.5, 3, nan], y = [1, 2, nan, nan, 4, 5, 6, nan]

## 힌트
- `inside = (times >= s) & (times <= e)` 로 구간 안의 프레임을 고르는 불리언 마스크를 만든다(NumPy 마스크 인덱싱).
- 단어마다 만든 조각을 리스트에 모았다가 마지막에 `np.concatenate`로 합친다.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pitch  # noqa: E402  (정답 함수 pitch.to_word_axis와 비교하려고 불러온다)

MIN_SECONDS = 0.03


def my_to_word_axis(times, values, spans, min_seconds=MIN_SECONDS):
    """TODO: 위 문제를 푼다. 돌려주는 값은 (x, y) NumPy 배열 두 개."""
    times = np.asarray(times, dtype=float)
    values = np.asarray(values, dtype=float)
    # 여기에 직접 작성하세요.
    raise NotImplementedError("my_to_word_axis를 채워 보세요")


CASES = {
    "손으로 해 본 예": ([0.0, 0.1, 0.2, 0.3, 0.4, 0.5], [1, 2, np.nan, 4, 5, 6], [(0.0, 0.2), None, (0.3, 0.5)]),
    "무성음(NaN)이 단어 안에 있음": ([0.0, 0.1, 0.2], [1.0, np.nan, 3.0], [(0.0, 0.2)]),
    "단어 둘이 붙어 있음": ([0.0, 0.1, 0.2, 0.3], [1, 2, 3, 4], [(0.0, 0.1), (0.2, 0.3)]),
    "너무 짧은 단어(0.02초)": ([0.0, 0.01, 0.02], [1, 2, 3], [(0.0, 0.02), None]),
    "단어가 하나도 없음": ([0.0, 0.1], [1, 2], [None, None]),
}


def main():
    ok = True
    for name, (times, values, spans) in CASES.items():
        want_x, want_y = pitch.to_word_axis(times, values, spans)
        try:
            got_x, got_y = my_to_word_axis(times, values, spans)
            same = (np.allclose(got_x, want_x, equal_nan=True) and np.allclose(got_y, want_y, equal_nan=True)
                    and len(got_x) == len(want_x))
        except NotImplementedError:
            print(f"  (아직) {name}: my_to_word_axis를 채워 보세요")
            ok = False
            continue
        print(f"  {'통과' if same else '다름'} {name}")
        if not same:
            ok = False
            print(f"      정답 x={np.round(want_x, 3).tolist()}\n      내 x ={np.round(got_x, 3).tolist()}")
    print("모두 통과!" if ok else "아직 다 통과하지 못했어요.")


if __name__ == "__main__":
    main()
