# 🎯 ロト6統計分析プロジェクト（loto6-analysis）

> ⚠️ **免責事項 / 면책 사항**
>
> 🇯🇵 本プロジェクトは、日本の宝くじ「ロト6」の過去当せんデータを統計的に分析・可視化することのみを目的とした学術的なオープンソースプロジェクトです。**当せん番号の予測・推奨機能は一切含まれていません。** 本分析結果は統計的傾向の可視化に過ぎず、将来の当せんを保証するものではありません。宝くじの購入は自己責任で行ってください。
>
> 🇰🇷 이 프로젝트는 일본 복권 「로또6」의 과거 당첨 데이터를 통계적으로 분석·시각화하는 것만을 목적으로 하는 학술적 오픈소스 프로젝트입니다. **당첨 번호 예측·추천 기능은 전혀 포함되어 있지 않습니다.** 본 분석 결과는 통계적 경향의 시각화일 뿐이며, 향후 당첨을 보장하지 않습니다. 복권 구매는 본인 책임 하에 진행하시기 바랍니다.

---

## 📌 概要 / 개요

`loto6-analysis`는 日本のロト6の第1回〜最新回の当せんデータを2つの公開ソースから収集し、番号出現頻度・組合傾向・当せん金推移を統計的に分析してStreamlit ダッシュボードで可視化するプロジェクトです。GitHub Actionsで月1回自動更新し、Google Analytics 4で利用状況をトラッキングします。

- **予測・推奨機能なし**：統計分析および可視化のみを提供します。
- **ライセンス**: MIT License（本リポジトリのコードのみ。データソースのライセンスは下記参照）

---

## 🗂️ データソース

### SOURCE A — みずほ銀行公式CSV（自動収集）

- URL: [`https://www.mizuhobank.co.jp/retail/takarakuji/loto/loto6/csv/loto6.csv`](https://www.mizuhobank.co.jp/retail/takarakuji/loto/loto6/csv/loto6.csv)
- 内容: 回号・抽せん日・抽せん場所（当せん番号・当せん金は含まない）
- ライセンス: 公開データ、`src/fetch_data.py` により直接ダウンロードのみ

### SOURCE B — KYO's LOTO6（⚠️ 手動ダウンロード必須）

- URL: [`https://loto6.thekyo.jp/download/index`](https://loto6.thekyo.jp/download/index)
- 内容: 回号・当せん番号1〜6・ボーナス数字・当せん金全等級
- **ライセンス制約: 個人利用のみ許可。商用利用・Web上での再配布は禁止されています。**
- このリポジトリには**このCSVファイルを一切含めていません**（`.gitignore` で除外済み）。

> 🇯🇵 **重要**: 当せん番号・当せん金を含む分析を実行するには、上記URLから **手動で1回CSVをダウンロード**し、`data/raw/loto6_numbers.csv` として保存してください。このファイルは絶対にコミット・公開しないでください。
>
> 🇰🇷 **중요**: 당첨번호·당첨금이 포함된 분석을 실행하려면, 위 URL에서 **직접 1회 CSV를 다운로드**하여 `data/raw/loto6_numbers.csv`로 저장해야 합니다. 이 파일은 절대 커밋하거나 공개하지 마세요.

---

## 🗺️ プロジェクト構成

```
loto6-analysis/
├── .github/workflows/update_data.yml
├── src/
│   ├── fetch_data.py
│   ├── merge_data.py
│   ├── analyze.py
│   └── visualize.py
├── app.py
├── data/
│   ├── raw/
│   │   ├── loto6_mizuho.csv
│   │   ├── loto6_numbers.csv   # ⚠️ 手動配置・.gitignore対象
│   │   └── loto6_all.csv
│   ├── analysis/*.csv
│   └── last_updated.txt
├── charts/*.html / *.png
├── requirements.txt
├── .gitignore / .env.example
└── LICENSE (MIT)
```

---

## ⚙️ セットアップ / 설치

```bash
git clone https://github.com/bumssi12-ship-it/loto6-analysis
cd loto6-analysis
cp .env.example .env
pip install -r requirements.txt
python src/fetch_data.py
# https://loto6.thekyo.jp/download/index から手動ダウンロード → data/raw/loto6_numbers.csv
python src/merge_data.py
python src/analyze.py
python src/visualize.py
streamlit run app.py
```

---

## ☁️ Streamlit Cloudへのデプロイ

1. [share.streamlit.io](https://share.streamlit.io) にアクセスし GitHub 連携
2. Repository: `bumssi12-ship-it/loto6-analysis`、Branch: `main`、Main file: `app.py`
3. Secretsに `GA4_MEASUREMENT_ID`、`GA4_API_SECRET` を追加
4. Deploy

> `loto6_numbers.csv` はリポジトリに含まれないため、事前生成済みの `data/analysis/`・`charts/` をコミットしておく必要があります。

---

## 🤖 GitHub Actions（自動更新）

毎月1日 09:00 JSTに SOURCE A を自動収集・分析・チャート生成しコミットします。Repository Secretsに `GA4_MEASUREMENT_ID`、`GA4_API_SECRET` を登録してください。

---

## 🔒 セキュリティとライセンス

- `.env`、`data/raw/loto6_numbers.csv` は `.gitignore` により除外済みです。
- 本リポジトリのソースコードは **MIT License** です。
- SOURCE B（KYO's LOTO6）のデータは各利用者が個人利用の範囲でダウンロード・保管してください。
