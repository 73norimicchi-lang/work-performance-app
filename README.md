# 三方作業実績分析アプリ

三方作業実績のExcelファイル（.xlsm / .xlsx）をアップロードして、
調整員別・集積者別の集計とグラフを自動表示するWebアプリ。

## 機能

- xlsm / xlsx ファイルのアップロード
- 調整員・集積者・号機・期間でのフィルタリング
- 調整員別集計（通し歩留まり、段取りロス、スタートロス、日別推移）
- 集積者別集計（通し歩留まり、歩留まり）
- 詳細データ一覧 + CSVダウンロード

## ローカルで動かす

```bash
pip install -r requirements.txt
streamlit run app.py
```

ブラウザで http://localhost:8501 を開く。

## デプロイ

[Streamlit Community Cloud](https://share.streamlit.io) でこのリポジトリを指定し、
`app.py` をメインファイルに設定してデプロイする。
