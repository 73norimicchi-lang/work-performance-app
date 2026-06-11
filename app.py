import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="三方作業実績分析",
    page_icon="📊",
    layout="wide"
)

st.title("📊 三方作業実績分析")


@st.cache_data
def load_data(file):
    df = pd.read_excel(file, sheet_name="三方実績", header=1)
    # 空行・ヘッダー重複行を除去
    df = df.dropna(subset=["作業日"])
    df = df[df["作業日"] != "作業日"]
    # 作業日をExcelシリアル値→datetime変換
    df["作業日"] = pd.to_datetime("1899-12-30") + pd.to_timedelta(
        df["作業日"].astype(float), unit="D"
    )
    # 数値列を変換
    numeric_cols = [
        "歩留り", "通し歩留り", "投入m", "実投入m", "仕上がりm",
        "仕上がり枚数", "自部門ロスm", "他部門ロスm", "段取りロス", "スタートロス",
        "スタート回数",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


# ファイルアップロード
uploaded_file = st.file_uploader(
    "xlsm / xlsx ファイルをアップロード", type=["xlsm", "xlsx"]
)

if uploaded_file is None:
    st.info("ファイルをアップロードしてください")
    st.stop()

df = load_data(uploaded_file)

# サイドバー：フィルター
st.sidebar.header("フィルター")

調整員_all = sorted(df["調整員"].dropna().unique())
selected_調整員 = st.sidebar.multiselect("調整員", 調整員_all, default=調整員_all)

集積者_all = sorted(df["集積者"].dropna().unique())
selected_集積者 = st.sidebar.multiselect("集積者", 集積者_all, default=集積者_all)

号機_all = sorted(df["作業号機"].dropna().unique())
selected_号機 = st.sidebar.multiselect("作業号機", 号機_all, default=号機_all)

date_min = df["作業日"].min().date()
date_max = df["作業日"].max().date()
date_range = st.sidebar.date_input("期間", value=(date_min, date_max))

# フィルター適用
filtered_df = df[
    df["調整員"].isin(selected_調整員)
    & df["集積者"].isin(selected_集積者)
    & df["作業号機"].isin(selected_号機)
].copy()

if len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df["作業日"].dt.date >= date_range[0])
        & (filtered_df["作業日"].dt.date <= date_range[1])
    ]

if filtered_df.empty:
    st.warning("データがありません。フィルターを見直してください。")
    st.stop()

# ========== タブ ==========
tab1, tab2, tab3 = st.tabs(["📈 調整員別集計", "📦 集積者別集計", "📋 詳細データ"])

# ========== 調整員別集計 ==========
with tab1:
    agg = filtered_df.groupby("調整員").agg(
        通し歩留まり_avg=("通し歩留り", "mean"),
        歩留まり_avg=("歩留り", "mean"),
        段取りロス_avg=("段取りロス", "mean"),
        スタートロス_sum=("スタートロス", "sum"),
        スタート回数_sum=("スタート回数", "sum"),
        投入m_sum=("投入m", "sum"),
        仕上がりm_sum=("仕上がりm", "sum"),
        件数=("作業日", "count"),
    ).reset_index()
    # スタートロスの平均 = スタートロス合計 ÷ スタート回数合計（1回あたりm、0除算回避）
    agg["スタートロス_avg"] = agg["スタートロス_sum"] / agg["スタート回数_sum"].replace(0, pd.NA)

    # 縦棒グラフ：調整員別 通し歩留まり
    fig1 = px.bar(
        agg.sort_values("通し歩留まり_avg", ascending=False),
        x="調整員",
        y="通し歩留まり_avg",
        title="調整員別 通し歩留まり（平均）",
        color="通し歩留まり_avg",
        color_continuous_scale="RdYlGn",
        labels={"通し歩留まり_avg": "通し歩留まり"},
    )
    # バーに%表示の数値ラベルを付ける
    fig1.update_traces(texttemplate="%{y:.1%}", textposition="outside")
    fig1.update_layout(yaxis_tickformat=".1%", coloraxis_showscale=False)
    st.plotly_chart(fig1, use_container_width=True)

    # 縦棒グラフ：調整員別 段取りロス・スタートロス
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        name="段取りロス",
        x=agg["調整員"],
        y=agg["段取りロス_avg"],
        marker_color="#EF553B",
    ))
    fig2.add_trace(go.Bar(
        name="スタートロス(/回)",
        x=agg["調整員"],
        y=agg["スタートロス_avg"],
        marker_color="#FFA15A",
    ))
    # バーに数値ラベル（m）を付ける
    fig2.update_traces(texttemplate="%{y:.1f}", textposition="outside")
    fig2.update_layout(
        title="調整員別 段取りロス・スタートロス（平均）",
        barmode="group",
        yaxis_title="m",
    )
    st.plotly_chart(fig2, use_container_width=True)

    # 日別推移
    st.subheader("日別 通し歩留まり推移")
    trend = (
        filtered_df.groupby(["作業日", "調整員"])["通し歩留り"]
        .mean()
        .reset_index()
        .rename(columns={"通し歩留り": "通し歩留まり"})
    )
    fig3 = px.line(
        trend,
        x="作業日",
        y="通し歩留まり",
        color="調整員",
        title="調整員別 通し歩留まり 日別推移",
        markers=True,
    )
    fig3.update_layout(yaxis_tickformat=".1%")
    st.plotly_chart(fig3, use_container_width=True)

    # 集計テーブル
    st.subheader("集計テーブル")
    tbl = agg.copy()
    tbl["通し歩留まり"] = tbl["通し歩留まり_avg"].map("{:.1%}".format)
    tbl["歩留まり"] = tbl["歩留まり_avg"].map("{:.1%}".format)
    tbl["段取りロス(m)"] = tbl["段取りロス_avg"].apply(
        lambda x: f"{x:.1f}" if pd.notna(x) else "-"
    )
    tbl["スタートロス(m/回)"] = tbl["スタートロス_avg"].apply(
        lambda x: f"{x:.1f}" if pd.notna(x) else "-"
    )
    st.dataframe(
        tbl[["調整員", "通し歩留まり", "歩留まり", "段取りロス(m)", "スタートロス(m/回)", "件数"]],
        use_container_width=True,
        hide_index=True,
    )

# ========== 集積者別集計 ==========
with tab2:
    agg2 = filtered_df.groupby("集積者").agg(
        通し歩留まり_avg=("通し歩留り", "mean"),
        歩留まり_avg=("歩留り", "mean"),
        件数=("作業日", "count"),
    ).reset_index()

    fig4 = px.bar(
        agg2.sort_values("通し歩留まり_avg"),
        x="通し歩留まり_avg",
        y="集積者",
        orientation="h",
        title="集積者別 通し歩留まり（平均）",
        color="通し歩留まり_avg",
        color_continuous_scale="RdYlGn",
        labels={"通し歩留まり_avg": "通し歩留まり"},
    )
    # バーに%表示の数値ラベルを付ける
    fig4.update_traces(texttemplate="%{x:.1%}", textposition="outside")
    fig4.update_layout(xaxis_tickformat=".1%", coloraxis_showscale=False)
    st.plotly_chart(fig4, use_container_width=True)

    fig5 = px.bar(
        agg2.sort_values("歩留まり_avg"),
        x="歩留まり_avg",
        y="集積者",
        orientation="h",
        title="集積者別 歩留まり（平均）",
        color="歩留まり_avg",
        color_continuous_scale="RdYlGn",
        labels={"歩留まり_avg": "歩留まり"},
    )
    # バーに%表示の数値ラベルを付ける
    fig5.update_traces(texttemplate="%{x:.1%}", textposition="outside")
    fig5.update_layout(xaxis_tickformat=".1%", coloraxis_showscale=False)
    st.plotly_chart(fig5, use_container_width=True)

    st.subheader("集計テーブル")
    tbl2 = agg2.copy()
    tbl2["通し歩留まり"] = tbl2["通し歩留まり_avg"].map("{:.1%}".format)
    tbl2["歩留まり"] = tbl2["歩留まり_avg"].map("{:.1%}".format)
    st.dataframe(
        tbl2[["集積者", "通し歩留まり", "歩留まり", "件数"]],
        use_container_width=True,
        hide_index=True,
    )

# ========== 詳細データ ==========
with tab3:
    display_cols = [
        "作業日", "作業号機", "調整員", "集積者", "製袋形態",
        "投入m", "仕上がりm", "歩留り", "通し歩留り", "段取りロス", "スタートロス",
    ]
    show_cols = [c for c in display_cols if c in filtered_df.columns]
    show_df = filtered_df[show_cols].copy()
    show_df["作業日"] = show_df["作業日"].dt.strftime("%Y/%m/%d")
    show_df["歩留り"] = show_df["歩留り"].apply(
        lambda x: f"{x:.1%}" if pd.notna(x) else "-"
    )
    show_df["通し歩留り"] = show_df["通し歩留り"].apply(
        lambda x: f"{x:.1%}" if pd.notna(x) else "-"
    )

    st.dataframe(show_df, use_container_width=True, hide_index=True)

    # CSVダウンロード
    csv = filtered_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 CSVダウンロード",
        data=csv,
        file_name="三方実績_集計.csv",
        mime="text/csv",
    )
