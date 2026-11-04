"""프로젝트 공통 그래프 색·스타일 (초록 계열).

노트북과 이후 모듈(visualisation.py 등)이 같은 색을 쓰도록 한곳에 모았습니다. 선택 근거와 검증 결과는
docs/프로젝트_안내_및_주제_검토.md 14.4절에 있습니다.
- 대표색(GREEN)은 한 시리즈만 그릴 때와 "내 것"을 나타낼 때 씁니다. 기준·비교 대상은 회색(MUTED)으로 둡니다.
- 시리즈가 여러 개일 때만 SERIES 순서대로 씁니다(최대 4개, 순서 고정). 5개 이상이면 그림을 나눕니다.
- 연속값(소리 크기·오류율 표)은 초록 한 가지 색의 밝기 차이로만 나타냅니다(CMAP_SPEC, CMAP_HEAT).

수업과의 관계
- [수업과 같음] 그림은 matplotlib으로 그린다. 파형(WAVEFORM)만 수업의 기본 파랑을 그대로 쓴다.
- [수업에 없음] 이 파일 전체. 수업은 matplotlib 내장 색 지도(`magma`, `Greens_r` 등)를 그림마다 직접 골랐고,
  여기서는 초록 계열 색 지도를 직접 만들어(`LinearSegmentedColormap.from_list`) 모든 그림이 같은 색을 쓰게 한다.
  `rcParams`(matplotlib의 전역 기본 설정 모음)를 한 번에 바꾸는 것도 수업에 없다.
"""
import matplotlib as mpl
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap

SURFACE = "#fcfcfb"      # 그림 바탕
INK = "#0b0b0b"          # 글자
INK_SECONDARY = "#52514e"
GRID = "#e4e3df"
MUTED = "#8a8985"        # 기준·비교 대상(회색)
NO_DATA = "#e7e7e4"      # 데이터가 없는 영역(예: 더 짧은 녹음의 뒤쪽)

GREEN = "#1a9f4c"        # 대표색
# 웹 앱(Streamlit) 브랜드 색. .streamlit/config.toml과 같은 값이며 tests/test_theme_config.py가 일치를 확인합니다(검토 문서 16.10).
PURPLE = "#6250d6"       # 틀린 단어·오류 표시(밑줄과 함께 씀, 빨강은 쓰지 않음). 바탕 #fcfcfb 위 글자 대비 5.6:1
LIME = "#c6f24e"         # 보조색(네온 라임). 바탕·형광 표시로만 쓰고 글자색으로 쓰지 않음(흰 바탕 대비가 낮음). 짙은 글자와는 11.5:1
BUTTON_GREEN = "#08833c"  # 주 버튼 바탕. 흰 글자 대비 4.86:1 (GREEN은 3.44:1이라 일반 글자에는 부족)
FOREST = "#112d18"       # 앱 글자색·어두운 카드 바탕. 바탕 대비 14.5:1
MINT = "#dff3e4"
WAVEFORM = "#1f77b4"     # 파형만 수업과 같은 matplotlib 기본 파랑을 씁니다(예외, 14.4절)
# 범주형 시리즈 순서. 초록 옆에 파랑을 둔 것은 초록·주황이 이웃하면 적록 색각 이상에서 구분이 안 되기 때문입니다.
# 인접 쌍 기준 validate_palette 통과(밝은/어두운 배경). 점·산점도처럼 모든 쌍이 이웃할 수 있는 그림은 초록+파랑 2개까지만.
SERIES = [GREEN, "#2a78d6", "#eb6834", "#6250d6"]

# 초록 한 가지 색(OKLCH 색상 150)의 밝기 사다리. OKLab 밝기가 단조롭게 변하는 것을 확인했습니다.
_LIGHT_SURFACE_RAMP = ["#e5ffe9", "#a9edb6", "#7cd591", "#54ba70", "#2f9f53", "#08833c", "#00662c", "#004a1e", "#112d18"]
_DARK_PANEL_RAMP = ["#000d03", "#00280d", "#00461c", "#00662c", "#05893e", "#40a85e", "#6ec683", "#9fe4ad", "#dafce0"]

CMAP_HEAT = LinearSegmentedColormap.from_list("songlingo_heat", _LIGHT_SURFACE_RAMP, N=256)  # 낮음=밝음 → 높음=어두움
CMAP_SPEC = LinearSegmentedColormap.from_list("songlingo_spec", _DARK_PANEL_RAMP, N=256)     # 낮음=어두움 → 높음=밝음 (스펙트로그램)


def _korean_font():
    """설치된 한글 글꼴 중 첫 번째를 돌려준다. 없으면 기본 글꼴(한글은 네모로 보임)."""
    installed = {f.name for f in font_manager.fontManager.ttflist}    # matplotlib이 찾은 글꼴 이름 집합
    # next(..., 기본값): 후보 중 설치된 첫 번째. macOS(AppleGothic) → Windows(Malgun Gothic) → 나눔고딕 순
    return next((n for n in ("AppleGothic", "Malgun Gothic", "NanumGothic") if n in installed), "DejaVu Sans")


def apply_style():
    """matplotlib 기본값을 프로젝트 설정으로 바꾼다. 그림을 그리기 전에 한 번 부른다.
    (rcParams는 전역 설정이라 한 번 바꾸면 이후 모든 그림에 적용된다. 여러 번 불러도 같은 값이므로 안전하다.)"""
    mpl.rcParams.update({
        "font.family": _korean_font(),
        "axes.unicode_minus": False,               # 한글 글꼴에서 음수 부호(−)가 네모로 깨지는 것을 막는다
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "text.color": INK,
        "axes.labelcolor": INK_SECONDARY,
        "axes.edgecolor": GRID,
        "xtick.color": INK_SECONDARY,
        "ytick.color": INK_SECONDARY,
        "axes.spines.top": False,                  # 그림 위·오른쪽 테두리선 제거
        "axes.spines.right": False,
        "axes.grid": False,                        # 격자선은 기본으로 끈다
        "grid.color": GRID,
        "axes.prop_cycle": mpl.cycler(color=SERIES),   # 선을 여러 개 그릴 때 쓰는 색의 순서
        "lines.linewidth": 1.5,
    })
