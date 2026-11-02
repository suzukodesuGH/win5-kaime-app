import itertools
import pandas as pd
import streamlit as st

# ページの設定
st.set_page_config(page_title="WIN5 買い目ツクール", page_icon="🏇", layout="wide")

# スタイル設定
st.markdown(
    """
    <style>
    .main-title {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .metric-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #d9534f;
    }
    .metric-label {
        font-size: 1rem;
        color: #555;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-title">🏇 WIN5 買い目ツクール</div>', unsafe_allow_html=True
)

# --- サイドバー：絞り込み条件設定 ---
st.sidebar.header("⚙️ 絞り込み条件設定")

# ① 人気の和の範囲指定（デフォルト 11〜19）
st.sidebar.subheader("1. 人気の和")
sum_range = st.sidebar.slider(
    "許容する人気の和の範囲", 5, 50, (11, 19), step=1
)

# ② 1番人気の登場回数上限
st.sidebar.subheader("2. 上位人気の出現制限")
max_rank1 = st.sidebar.slider(
    "1番人気の登場回数 上限", 0, 5, 3, step=1, help="5レース中の最大数"
)

# ③ 1・2番人気の登場回数上限
max_rank12 = st.sidebar.slider(
    "1・2番人気の合計登場回数 上限", 0, 5, 4, step=1, help="5レース中の最大数"
)

# ④ 5番人気以下の登場回数上限
st.sidebar.subheader("3. 下位人気（穴馬）の制限")
max_under5 = st.sidebar.slider(
    "5番人気以下の登場回数 上限", 0, 5, 2, step=1, help="デフォルトは2回以下"
)

# ⑤ 騎手の重複排除
st.sidebar.subheader("4. 騎手フィルター")
enable_jockey_filter = st.sidebar.checkbox(
    "同一騎手の複数勝利（重複）を排除する",
    value=True,
    help=(
        "騎手名が入力されている場合、同じ騎手が複数レースで選ばれている買い目を除外します（空欄は対象外）。"
    ),
)

st.sidebar.markdown("---")

# --- メイン入力エリア ---
st.subheader("📝 各レースの候補馬")

races_data = {}
race_names = ["WIN1", "WIN2", "WIN3", "WIN4", "WIN5"]

tabs = st.tabs(race_names)

for i, r_name in enumerate(race_names):
  with tabs[i]:
    st.markdown(f"**{r_name} の候補馬設定**")
    candidates = []

    for c_idx in range(1, 6):
      cols = st.columns([1.2, 1.2, 1.5, 4])
      with cols[0]:
        # 馬1のみデフォルト1、馬2〜5は0(未入力)
        default_umaban = 1 if c_idx == 1 else 0
        b_num = st.number_input(
            f"馬番 #{c_idx}",
            min_value=0,
            max_value=18,
            value=default_umaban,
            key=f"{r_name}_umaban_{c_idx}",
            help="太字の項目（馬番）",
        )
      with cols[1]:
        # 馬1のみデフォルト1、馬2〜5は0
        default_ninki = 1 if c_idx == 1 else 0
        n_rank = st.number_input(
            f"人気 #{c_idx}",
            min_value=0,
            max_value=18,
            value=default_ninki,
            key=f"{r_name}_ninki_{c_idx}",
            help="人気順",
        )
      with cols[2]:
        # 騎手名（プレースホルダーなし）
        jockey = st.text_input(
            f"騎手 #{c_idx}", value="", key=f"{r_name}_jockey_{c_idx}"
        )

      if b_num > 0 and n_rank > 0:
        candidates.append(
            {"umaban": int(b_num), "ninki": int(n_rank), "jockey": jockey.strip()}
        )

    races_data[r_name] = candidates

# --- データ処理とフィルタリングの実行 ---
processed_races = []
for r_name in race_names:
  valid_cands = races_data[r_name]
  processed_races.append(valid_cands)

# 簡易サマリー用のデータを集計（馬番のみのリスト）
summary_texts = {}
for r_name in race_names:
  cands = races_data[r_name]
  nums = [str(c["umaban"]) for c in cands]
  summary_texts[r_name] = ", ".join(nums) if nums else "なし"

# サイドバーに常時サマリーを表示
st.sidebar.subheader("📋 選択馬サマリー")
for r_name in race_names:
  st.sidebar.text(f"{r_name}：{summary_texts[r_name]}")

# 全組み合わせの生成 (直積)
if any(len(r) == 0 for r in processed_races):
  all_combinations = []
else:
  all_combinations = list(itertools.product(*processed_races))

# フィルタリング判定
filtered_results = []

for combo in all_combinations:
  ninki_list = [item["ninki"] for item in combo]
  jockey_list = [item["jockey"] for item in combo if item["jockey"] != ""]

  # 判定1: 人気の和
  sum_ninki = sum(ninki_list)
  if not (sum_range[0] <= sum_ninki <= sum_range[1]):
    continue

  # 判定2: 1番人気の登場回数上限
  count_rank1 = ninki_list.count(1)
  if count_rank1 > max_rank1:
    continue

  # 判定3: 1・2番人気の登場回数上限
  count_rank12 = sum(1 for n in ninki_list if n <= 2)
  if count_rank12 > max_rank12:
    continue

  # 判定4: 5番人気以下の登場回数上限
  count_under5 = sum(1 for n in ninki_list if n >= 5)
  if count_under5 > max_under5:
    continue

  # 判定5: 騎手の重複チェック
  if enable_jockey_filter:
    if len(jockey_list) != len(set(jockey_list)):
      continue

  filtered_results.append(combo)

# --- 画面の切り替え（タブ） ---
st.markdown("---")
view_tab1, view_tab2 = st.tabs(["買い目・点数", "全組み合わせ・検証"])

with view_tab1:
  total_points = len(filtered_results)
  total_all = len(all_combinations)

  st.markdown(
      f"""
        <div class="metric-box">
            <div class="metric-label">現在の総買い目数</div>
            <div class="metric-value">
                {total_points}点<span style="font-size: 1.4rem; font-weight: normal; color: #666;"> / {total_all}点</span>
            </div>
        </div>
        """,
      unsafe_allow_html=True,
  )

  st.subheader("買い目一覧")

  if total_points == 0:
    st.warning(
        "条件に一致する買い目がありません。入力内容や絞り込み条件を見直してください。"
    )
  else:
    # 1. 表用データの構築
    display_data = []
    # 2. テキスト・コピペ用データの構築 (＃01 1-5-8-4-11 形式)
    text_lines = []

    for idx, combo in enumerate(filtered_results, 1):
      display_data.append({
          "点数": f"#{idx}",
          "WIN1": f"{combo[0]['umaban']}",
          "WIN2": f"{combo[1]['umaban']}",
          "WIN3": f"{combo[2]['umaban']}",
          "WIN4": f"{combo[3]['umaban']}",
          "WIN5": f"{combo[4]['umaban']}",
      })

      # コピペ用文字列：＃01 1-5-8-4-11
      combo_str = "-".join([str(item["umaban"]) for item in combo])
      text_lines.append(f"＃{idx:02d} {combo_str}")

    df_display = pd.DataFrame(display_data)

    # 一括コピー用テキスト＆ダウンロードエリア
    export_text = "\n".join(text_lines)

    col1, col2 = st.columns([3, 1])
    with col1:
      st.download_button(
          label="📄 買い目をテキストファイル (.txt) で保存",
          data=export_text,
          file_name="win5_kaime.txt",
          mime="text/plain",
      )

    with st.expander("📋 一括コピペ用テキスト表示", expanded=False):
      st.text_area("全選択（Ctrl+A / Cmd+A）してコピーできます", value=export_text, height=200)

    st.dataframe(df_display, use_container_width=True, hide_index=True)

with view_tab2:
  st.subheader("全組み合わせ・検証")
  st.info(
      "ここでは全総当たりの組み合わせに対する「人気の和」や、各フィルターを通過したかを確認できます。（除外されたFALSEは赤字表示）"
  )

  if len(all_combinations) == 0:
    st.warning("各レースに少なくとも1頭以上の候補を入力してください。")
  else:
    full_data = []
    for idx, combo in enumerate(all_combinations, 1):
      ninki_list = [item["ninki"] for item in combo]
      jockey_list = [item["jockey"] for item in combo if item["jockey"] != ""]
      sum_n = sum(ninki_list)

      passed = True
      if not (sum_range[0] <= sum_n <= sum_range[1]):
        passed = False
      if ninki_list.count(1) > max_rank1:
        passed = False
      if sum(1 for n in ninki_list if n <= 2) > max_rank12:
        passed = False
      if sum(1 for n in ninki_list if n >= 5) > max_under5:
        passed = False
      if enable_jockey_filter and len(jockey_list) != len(set(jockey_list)):
        passed = False

      def format_cell(item):
        j_str = f"/{item['jockey']}" if item["jockey"] else ""
        return f"{item['umaban']}({item['ninki']}人気{j_str})"

      full_data.append({
          "No": idx,
          "WIN1": format_cell(combo[0]),
          "WIN2": format_cell(combo[1]),
          "WIN3": format_cell(combo[2]),
          "WIN4": format_cell(combo[3]),
          "WIN5": format_cell(combo[4]),
          "人気の和": sum_n,
          "判定": "TRUE" if passed else "FALSE",
      })

    df_full = pd.DataFrame(full_data)

    def highlight_status(val):
      if val == "FALSE":
        return "color: #d9534f; font-weight: bold;"
      elif val == "TRUE":
        return "color: #2ca02c; font-weight: bold;"
      return ""

    styled_df = df_full.style.map(highlight_status, subset=["判定"])

    st.dataframe(styled_df, use_container_width=True, hide_index=True)