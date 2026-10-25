# 微積分の体系的解説

高校数学を前提に、運動と図形から微分・積分を導き、計算、別解、応用へ進む日本語の教科書です。大学数学や物理の履修は前提にしません。

## 構成

1. 運動と面積
2. 極限と微分
3. 微分の応用
4. 積分
5. 積分の計算
6. 置換積分
7. 部分積分
8. 定積分の対称性
9. 積分の応用
10. 積分と数列
11. 置換と図形
12. 近似と広義積分
13. 総合演習

解答、公式、用語索引、参考資料を巻末に置いています。章・節・小節の見出しは短い標準的な表現とし、詳しい説明は本文に置きます。

原稿は「章フォルダ → 番号付きの節フォルダ → 小節ファイル」に分け、親ファイルから `\input` で読み込みます。すべての読み込みパスはリポジトリのルートを起点とします。

## コンパイル

日本語に対応したTeX Liveと原ノ味フォントを用意し、ルートで次を実行します。

```sh
latexmk -lualatex -interaction=nonstopmode -halt-on-error main.tex
```

OverleafではLuaLaTeXを選び、`main.tex`をメイン文書にします。PDFやビルド中間物はGit履歴に含めません。数式の表記と語彙は `python3 scripts/verify-math-style.py` で検査できます。

## 利用条件

原稿・図版はCC0 1.0です。第三者のソフトウェアやフォントには、それぞれのライセンスが適用されます。詳細は `LICENSE` を参照してください。

## PDFの公開

- 本棚: https://mas256.github.io/math-textbooks/
- 教科書の公開ページ: https://mas256.github.io/Integral/
- 正式版一覧: https://github.com/mas256/Integral/releases

mainへの原稿の更新で **Build** がLuaLaTeXを実行します。PDFの参照・文字・フォント・A4寸法を検査し、成功した成果物だけを **Deploy Pages** が最新版PDFとして公開します。失敗したビルドでは公開済みPDFを維持します。開発ビルドごとのTagやReleaseは作りません。

正式版はActionsの **Release** をmainから実行し、`v0.1.0` のような新しい版番号を指定します。PDFとSHA-256を検証してからReleaseを公開します。初回公開後は正式版とlatestを同じ公開処理で配信し、本棚は `catalog.json` から版番号・更新日時・PDF名を取得します。

正式版PDFは `微積分の体系的解説-vMAJOR.MINOR.PATCH.pdf`、開発中PDFは `latest-微積分の体系的解説-vMAJOR.MINOR.PATCH.pdf` です。latestには現在の正式版番号を付け、内容のSHA-256をURLに含めてキャッシュを区別します。更新日時はReleaseの公開日時と成功ビルドの日時であり、Pagesの再配信では変更しません。

公開ページの書名、PDFファイル名、本棚の書名は正式版PDFに埋め込まれたタイトルから生成します。書名を変更するときは原稿の `\\hypersetup{pdftitle={...}}` を変更し、新しい正式版を公開してください。本文の紹介と著者は `book.yml` から取得します。
