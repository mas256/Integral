# 積分の体系的解説

高校数学を出発点に、積分の意味、計算方法、定積分の応用、近似と広義積分までをつないで説明する日本語の教科書です。

- 第1版原稿（2026年10月）
- 全12章、例題75題、演習102題と全解答、図19点
- A4・161ページの完成PDFはGit履歴には含めず、正式版Releaseで配布する方針です。

## 原稿の構成

`main.tex`から前付、12章、解答、公式参照表、用語索引、参考資料を読み込みます。章本文は`chapters/`、解答は`answers/`にあります。

## コンパイル

LuaLaTeXと日本語対応のTeX Live環境を使います。`texlive-lang-japanese`、`texlive-luatex`相当のパッケージと原ノ味フォントが必要です。

```sh
latexmk -lualatex -interaction=nonstopmode -halt-on-error main.tex
```

OverleafではLuaLaTeXを選び、`main.tex`をメイン文書にしてください。

## 利用条件

本書の著者による原稿・図版はCC0 1.0で提供します。TeX Live、原ノ味フォントなど第三者のソフトウェア・フォントには各々のライセンスが適用され、本書のCC0には含まれません。詳細は`LICENSE`と各配布元を確認してください。
