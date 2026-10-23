#!/usr/bin/env python3
"""原稿の数式表記と語彙を検査する.

使い方: python3 scripts/verify-math-style.py [ファイル ...]
引数がなければ, リポジトリ内のすべての .tex を検査する.
誤り(ERROR)が1つでもあれば終了コード1を返す. 語彙の注意(WARN)は終了コードに影響しない.

検査する規則
- インライン数式は main.tex の \\everymath{\\displaystyle} で displaystyle になる.
  本文に \\displaystyle, \\textstyle, \\dfrac, \\tfrac を書かない.
- 独立した数式は \\[ … \\] か align* で組む. $$ と, ラベルのない番号付き環境は使わない.
  (本文から \\eqref で参照する式だけは equation とラベルで組んでよい.)
- 分数は \\frac で書き, 入れ子の分数は外側・内側とも \\cfrac にする.
- 数式中で / による除算を使わない.
- 句読点は「,」「.」. 本文に「、」「。」を使わない.
- 読点の直後にインライン数式が来るときは ,\\,$…$ とする.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN_CMDS = {
    r"\displaystyle": "インライン数式は既定で displaystyle なので書かない",
    r"\textstyle": "textstyle は使わない",
    r"\dfrac": "\\frac で書く(既定で displaystyle)",
    r"\tfrac": "tfrac は使わない",
}

VOCAB = [
    (re.compile(r"[一二三四五六七八九]つ"), "数を表す「〜つ」は算用数字で書く(2つ・3つ)"),
    (re.compile(r"(?<![a-zA-Z])零(?!点|ベクトル|行列)"), "「零」は「0」と書く"),
    (re.compile(r"非零"), "「非零」は「0でない」と書く"),
    (re.compile(r"(?<!に)従って"), "接続詞は「したがって」と書く"),
    (re.compile(r"[一二三]項(?!式|定理|係数|分布|間)"), "項の数は算用数字で書く(2項)"),
]


def strip_comments(line: str) -> str:
    out = []
    i = 0
    while i < len(line):
        c = line[i]
        if c == "\\" and i + 1 < len(line):
            out.append(line[i : i + 2])
            i += 2
            continue
        if c == "%":
            break
        out.append(c)
        i += 1
    return "".join(out)


def read_group(s: str, i: int) -> tuple[str, int]:
    """s[i] から始まる引数1つ(波括弧または1トークン)を読む."""
    while i < len(s) and s[i] in " \t\n":
        i += 1
    if i >= len(s):
        return "", i
    if s[i] == "{":
        depth = 0
        j = i
        while j < len(s):
            if s[j] == "\\":
                j += 2
                continue
            if s[j] == "{":
                depth += 1
            elif s[j] == "}":
                depth -= 1
                if depth == 0:
                    return s[i + 1 : j], j + 1
            j += 1
        return s[i + 1 :], len(s)
    if s[i] == "\\":
        m = re.match(r"\\([A-Za-z]+|.)", s[i:])
        return m.group(0), i + len(m.group(0))
    return s[i], i + 1


FRAC_RE = re.compile(r"\\(c?frac)(?![A-Za-z])")


def check_fractions(text: str):
    """(位置, メッセージ) を返す."""
    issues = []
    for m in FRAC_RE.finditer(text):
        kind = m.group(1)
        a, j = read_group(text, m.end())
        b, _ = read_group(text, j)
        inner = FRAC_RE.search(a) or FRAC_RE.search(b)
        if kind == "frac" and inner:
            issues.append((m.start(), "入れ子の分数は外側・内側とも \\cfrac にする"))
        if kind == "cfrac":
            inner_plain = re.search(r"\\frac(?![A-Za-z])", a) or re.search(r"\\frac(?![A-Za-z])", b)
            if inner_plain:
                issues.append((m.start(), "\\cfrac の中の分数も \\cfrac にする"))
    return issues


MATH_ENVS = ("align", "align*", "equation", "equation*", "gather", "gather*", "multline", "multline*")


def math_spans(text: str):
    """数式モードの範囲 [start, end) を大まかに求める."""
    spans = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith("\\[", i):
            j = text.find("\\]", i + 2)
            j = n if j < 0 else j
            spans.append((i + 2, j))
            i = j + 2
            continue
        if text.startswith("\\begin{", i):
            m = re.match(r"\\begin\{([^}]*)\}", text[i:])
            env = m.group(1)
            if env in MATH_ENVS:
                end = text.find("\\end{%s}" % env, i)
                end = n if end < 0 else end
                spans.append((i + len(m.group(0)), end))
                i = end + 1
                continue
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == "$":
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == "$":
                    break
                j += 1
            spans.append((i + 1, j))
            i = j + 1
            continue
        i += 1
    return spans


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def check_file(path: Path):
    errors, warns = [], []
    raw = path.read_text(encoding="utf-8")
    text = "\n".join(strip_comments(l) for l in raw.split("\n"))
    rel = path.relative_to(ROOT)
    is_main = rel.name == "main.tex"

    def err(pos, msg):
        errors.append(f"{rel}:{line_of(text, pos)}: {msg}")

    def warn(pos, msg):
        warns.append(f"{rel}:{line_of(text, pos)}: {msg}")

    if not is_main:
        for cmd, msg in FORBIDDEN_CMDS.items():
            for m in re.finditer(re.escape(cmd) + r"(?![A-Za-z])", text):
                err(m.start(), f"{cmd}: {msg}")
    for m in re.finditer(r"\$\$", text):
        err(m.start(), "$$ ではなく \\[ … \\] を使う")
    for m in re.finditer(r"\\begin\{(equation|align|gather|multline)\}", text):
        env = m.group(1)
        end = text.find("\\end{%s}" % env, m.end())
        body = text[m.end() : end if end > 0 else len(text)]
        if env != "equation" or "\\label" not in body:
            err(m.start(), f"番号付き環境 {env}: 参照しない式は \\[ … \\] か align* で組む")
    for pos, msg in check_fractions(text):
        err(pos, msg)
    spans = math_spans(text)
    for a, b in spans:
        seg = text[a:b]
        for m in re.finditer(r"/", seg):
            err(a + m.start(), "数式中で / による除算を使わない")
    for m in re.finditer(r"[、。]", text):
        err(m.start(), "句読点は「,」「.」を使う")
    # 読点の直後のインライン数式
    in_math = [False] * (len(text) + 1)
    for a, b in spans:
        for k in range(max(a - 1, 0), min(b + 1, len(text))):
            in_math[k] = True
    for m in re.finditer("\uff0c\\$", text):
        if not in_math[m.start()]:
            err(m.start(), "読点の直後のインライン数式は \uff0c\\,$…$ と書く")
    for rx, msg in VOCAB:
        for m in rx.finditer(text):
            if in_math[m.start()]:
                continue
            warn(m.start(), f"「{m.group(0)}」: {msg}")
    return errors, warns


def main(argv):
    if argv:
        files = [Path(a).resolve() for a in argv]
    else:
        out = subprocess.run(["git", "ls-files", "-z", "*.tex"], cwd=ROOT, capture_output=True, check=True)
        files = [ROOT / p for p in out.stdout.decode().split("\0") if p]
    all_err, all_warn = [], []
    for f in files:
        e, w = check_file(f)
        all_err += e
        all_warn += w
    for w in all_warn:
        print("WARN  " + w)
    for e in all_err:
        print("ERROR " + e)
    print(f"検査ファイル {len(files)}, 誤り {len(all_err)}, 注意 {len(all_warn)}")
    return 1 if all_err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
