import itertools
import pandas as pd
import streamlit as st

# スマホで最も負荷が少なく安定する centered に設定
st.set_page_config(page_title="WIN5 買い目ツクール", page_icon="🏇", layout="centered")

# スマホのフリーズを防ぐため、最小限の軽量スタイルのみに調整
st.markdown(
    """
    <style>
    .main-title {
        font-size: 1.4rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.4rem;
    }
    .metric-box {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 15px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #d9534f;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-title">🏇 WIN5 買い目ツクール (スマホ最適化)</div>',
    unsafe_allow_html=True,
)

# --- サイドバー：絞り込み条件設定 ---
st.sidebar.header("⚙️ 絞り込み条件")

st.sidebar.subheader("1. 人気の和の範囲")
col_s1, col_s2 = st.sidebar.columns(2)
with col_s1:
  sum_min = st.number_input(
      "下限", min_value=5, max_value=50, value=11, step=1, key="sum_min"
  )
with col_s2:
  sum_max = st.number_input(
      "上限", min_value=5, max_value=50, value=19, step=1, key="sum_max"
  )

if sum_min > sum_max:
  effective_min, effective_max = sum_max, sum_min
else:
  effective_min, effective_max = sum_min, sum_max

st.sidebar.subheader("2. 出現制限")
max_rank1 = st.sidebar.slider("1番人気の登場回数 上限", 0, 5, 3, step=1)
max_rank12 = st.sidebar.slider(
    "1・2番人気の合計登場回数 上限", 0, 5, 4, step=1
)
max_under5 = st.sidebar.slider("5番人気以下の登場回数 上限", 0, 5, 2, step=1)

enable_jockey_filter = st.sidebar.checkbox(
    "同一騎手の複数勝利（重複）を排除する", value=True
)

st.sidebar.markdown("---")

# --- メイン入力エリア ---
st.subheader("📝 各レースの候補馬")

races_data = {}
race_names = ["WIN1", "WIN2", "WIN3", "WIN4", "WIN5"]

tabs = st.tabs(race_names)

for i, r_name in enumerate(race_names):
  with tabs[i]:
    candidates = []
    for c_idx in range(1, 6):
      cols = st.columns([1, 1, 1.5])
      with cols[0]:
        b_num = st.number_input(
            f"馬_{r_name}_{c_idx}",
            min_value=0,
            max_value=18,
            value=(1 if c_idx == 1 and i == 0 else 0),
            key=f"{r_name}_umaban_{c_idx}",
        )
      with cols[1]:
        n_rank = st.number_input(
            f"人_{r_name}_{c_idx}",
            min_value=0,
            max_value=18,
            value=(1 if c_idx == 1 and i == 0 else 0),
            key=f"{r_name}_ninki_{c_idx}",
        )
      with cols[2]:
        jockey = st.text_input(
            f"騎_{r_name}_{c_idx}",
            value="",
            key=f"{r_name}_jockey_{c_idx}",
            placeholder="騎手名",
        )

      if b_num > 0 and n_rank > 0:
        candidates.append(
            {"umaban": int(b_num), "ninki": int(n_rank), "jockey": jockey.strip()}
        )

    races_data[r_name] = candidates

# --- データ処理 ---
processed_races = [races_data[r_name] for r_name in race_names]

if any(len(r) == 0 for r in processed_races):
  all_combinations = []
else:
  all_combinations = list(itertools.product(*processed_races))

filtered_results = []
for combo in all_combinations:
  ninki_list = [item["ninki"] for item in combo]
  jockey_list = [item["jockey"] for item in combo if item["jockey"] != ""]

  sum_ninki = sum(ninki_list)
  if not (effective_min <= sum_ninki <= effective_max):
    continue
  if ninki_list.count(1) > max_rank1:
    continue
  if sum(1 for n in ninki_list if n <= 2) > max_rank12:
    continue
  if sum(1 for n in ninki_list if n >= 5) > max_under5:
    continue
  if enable_jockey_filter and len(jockey_list) != len(set(jockey_list)):
    continue

  filtered_results.append(combo)

# --- 結果表示（スマホで重くなるカラー装飾を完全に排除） ---
st.markdown("---")
total_points = len(filtered_results)
total_all = len(all_combinations)

st.markdown(
    f"""
    <div class="metric-box">
        <div style="font-size: 0.85rem; color: #555;">現在の総買い目数</div>
        <div class="metric-value">{total_points}点 <span style="font-size: 1rem; color: #666;">/ {total_all}点</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

if total_points == 0:
  st.warning("条件に一致する買い目がありません。")
else:
  display_data = []
  text_lines = []
  for idx, combo in enumerate(filtered_results, 1):
    display_data.append({
        "No": f"#{idx}",
        "WIN1": combo[0]["umaban"],
        "WIN2": combo[1]["umaban"],
        "WIN3": combo[2]["umaban"],
        "WIN4": combo[3]["umaban"],
        "WIN5": combo[4]["umaban"],
    })
    combo_str = "-".join([str(item["umaban"]) for item in combo])
    text_lines.append(f"＃{idx:02d} {combo_str}")

  export_text = "\n".join(text_lines)

  st.download_button(
      label="📄 テキストファイル (.txt) で保存",
      data=export_text,
      file_name="win5_kaime.txt",
      mime="text/plain",
  )

  st.text_area("コピペ用エリア", value=export_text, height=140)

  df_display = pd.DataFrame(display_data)
  # スマホでクラッシュする原因になる重いスタイリングを外し、通常の軽量なテーブル表示にする
  st.dataframe(df_display, use_container_width=True, hide_index=True)
