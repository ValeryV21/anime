import streamlit as st
import requests
import json
import os
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
DATA_FILE = "anime_list.json"
JIKAN_BASE = "https://api.jikan.moe/v4"

STATUS_OPTIONS = ["Plan to Watch", "Watching", "Completed", "On Hold", "Dropped"]
STATUS_EMOJI = {
    "Plan to Watch": "📋",
    "Watching": "▶️",
    "Completed": "✅",
    "On Hold": "⏸️",
    "Dropped": "🗑️",
}
STATUS_COLORS = {
    "Plan to Watch": "#5B8DEF",
    "Watching": "#F0A500",
    "Completed": "#2ECC71",
    "On Hold": "#9B59B6",
    "Dropped": "#E74C3C",
}

st.set_page_config(
    page_title="Anime Tracker",
    page_icon="🎌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Dark anime-themed palette */
  :root {
    --bg: #0f0f1a;
    --card: #1a1a2e;
    --accent: #e94560;
    --accent2: #533483;
    --text: #eaeaea;
    --muted: #888;
  }

  .stApp { background-color: var(--bg); color: var(--text); }

  /* Hero header */
  .hero {
    text-align: center;
    padding: 2rem 0 1rem;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 16px;
    margin-bottom: 2rem;
    border: 1px solid #e9456033;
  }
  .hero h1 { font-size: 3rem; margin: 0; letter-spacing: 2px; }
  .hero p  { color: #aaa; margin: 0.3rem 0 0; font-size: 1.1rem; }

  /* Anime search card */
  .anime-card {
    background: var(--card);
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 1rem;
    display: flex;
    gap: 1rem;
    align-items: flex-start;
    transition: border-color 0.2s;
  }
  .anime-card:hover { border-color: var(--accent); }
  .anime-card img { border-radius: 8px; width: 80px; height: 115px; object-fit: cover; }
  .anime-card .info { flex: 1; }
  .anime-card .title { font-weight: 700; font-size: 1rem; color: var(--text); }
  .anime-card .meta  { color: var(--muted); font-size: 0.8rem; margin-top: 0.25rem; }
  .anime-card .score { color: #F0A500; font-weight: 700; }
  .anime-card .synopsis {
    font-size: 0.78rem; color: #bbb; margin-top: 0.4rem;
    display: -webkit-box; -webkit-line-clamp: 3;
    -webkit-box-orient: vertical; overflow: hidden;
  }

  /* Status badge */
  .badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
    margin-top: 0.3rem;
  }

  /* My list card */
  .list-card {
    background: var(--card);
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.75rem;
    display: flex;
    gap: 1rem;
    align-items: center;
  }
  .list-card img { border-radius: 6px; width: 55px; height: 78px; object-fit: cover; }
  .list-card .info { flex: 1; }
  .list-card .title { font-weight: 700; }
  .list-card .meta  { color: var(--muted); font-size: 0.8rem; }

  /* Stats bar */
  .stat-box {
    background: var(--card);
    border-radius: 12px;
    border: 1px solid #2a2a4a;
    padding: 1.2rem;
    text-align: center;
  }
  .stat-box .num  { font-size: 2rem; font-weight: 800; color: var(--accent); }
  .stat-box .label{ color: var(--muted); font-size: 0.85rem; margin-top: 0.2rem; }

  /* Hide default Streamlit chrome */
  #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Persistence helpers ────────────────────────────────────────────────────────
def load_list() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_list(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── Jikan API helpers ──────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def search_anime(query: str, page: int = 1):
    try:
        r = requests.get(
            f"{JIKAN_BASE}/anime",
            params={"q": query, "page": page, "limit": 12, "sfw": True},
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("data", [])
    except Exception as e:
        st.error(f"API error: {e}")
        return []

@st.cache_data(ttl=3600, show_spinner=False)
def get_top_anime():
    try:
        r = requests.get(f"{JIKAN_BASE}/top/anime", params={"limit": 12}, timeout=10)
        r.raise_for_status()
        return r.json().get("data", [])
    except Exception:
        return []

def anime_to_entry(a: dict, status: str) -> dict:
    return {
        "mal_id":    a["mal_id"],
        "title":     a["title"],
        "title_en":  a.get("title_english") or a["title"],
        "image":     a["images"]["jpg"]["image_url"],
        "score":     a.get("score"),
        "episodes":  a.get("episodes"),
        "status_mal":a.get("status"),
        "genres":    [g["name"] for g in (a.get("genres") or [])],
        "synopsis":  (a.get("synopsis") or "")[:300],
        "url":       a.get("url", ""),
        "my_status": status,
        "added_on":  datetime.now().strftime("%Y-%m-%d"),
        "progress":  0,
        "notes":     "",
    }

# ── Init session state ────────────────────────────────────────────────────────
if "anime_list" not in st.session_state:
    st.session_state.anime_list = load_list()
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Search"

# ── Hero header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🎌 Anime Tracker</h1>
  <p>Search, track and remember every anime you've watched</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar — stats & filters ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 My Stats")
    al = st.session_state.anime_list
    total = len(al)
    completed = sum(1 for v in al.values() if v["my_status"] == "Completed")
    watching  = sum(1 for v in al.values() if v["my_status"] == "Watching")
    plan      = sum(1 for v in al.values() if v["my_status"] == "Plan to Watch")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="stat-box"><div class="num">{total}</div><div class="label">Total</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-box" style="margin-top:.6rem"><div class="num">{watching}</div><div class="label">Watching</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-box"><div class="num">{completed}</div><div class="label">Completed</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-box" style="margin-top:.6rem"><div class="num">{plan}</div><div class="label">Plan to Watch</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## 🔍 Filter My List")
    filter_status = st.selectbox("Status", ["All"] + STATUS_OPTIONS)
    filter_search = st.text_input("Search my list", placeholder="Title…")

    st.markdown("---")
    if st.button("🗑️ Clear All Data", use_container_width=True):
        st.session_state.anime_list = {}
        save_list({})
        st.success("List cleared.")
        st.rerun()

# ── Main tabs ──────────────────────────────────────────────────────────────────
tab_search, tab_list, tab_top = st.tabs(["🔍 Search Anime", "📋 My List", "🏆 Top Anime"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — SEARCH
# ══════════════════════════════════════════════════════════════════════════════
with tab_search:
    col_q, col_btn = st.columns([5, 1])
    with col_q:
        query = st.text_input("", placeholder="Search for any anime…", label_visibility="collapsed",
                              value=st.session_state.search_query)
    with col_btn:
        do_search = st.button("Search", use_container_width=True, type="primary")

    if do_search and query.strip():
        st.session_state.search_query = query.strip()
        with st.spinner("Searching…"):
            st.session_state.search_results = search_anime(query.strip())

    results = st.session_state.search_results
    if results:
        st.markdown(f"**{len(results)} results** for *{st.session_state.search_query}*")
        for anime in results:
            mid  = str(anime["mal_id"])
            img  = anime["images"]["jpg"]["image_url"]
            title = anime.get("title", "Unknown")
            score = anime.get("score") or "N/A"
            eps   = anime.get("episodes") or "?"
            status_mal = anime.get("status", "")
            genres = ", ".join(g["name"] for g in (anime.get("genres") or [])[:3])
            synopsis = (anime.get("synopsis") or "No synopsis available.")[:260]
            in_list = mid in st.session_state.anime_list

            with st.container():
                st.markdown(f"""
                <div class="anime-card">
                  <img src="{img}" onerror="this.src='https://via.placeholder.com/80x115?text=No+Image'"/>
                  <div class="info">
                    <div class="title">{title}</div>
                    <div class="meta">
                      <span class="score">⭐ {score}</span> &nbsp;·&nbsp;
                      📺 {eps} eps &nbsp;·&nbsp; {status_mal} &nbsp;·&nbsp; {genres}
                    </div>
                    <div class="synopsis">{synopsis}</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                c1, c2, c3 = st.columns([3, 2, 1])
                with c1:
                    sel_status = st.selectbox(
                        "Status", STATUS_OPTIONS,
                        key=f"sel_{mid}",
                        index=STATUS_OPTIONS.index(st.session_state.anime_list[mid]["my_status"]) if in_list else 0,
                        label_visibility="collapsed",
                    )
                with c2:
                    if in_list:
                        if st.button("✏️ Update", key=f"upd_{mid}", use_container_width=True):
                            st.session_state.anime_list[mid]["my_status"] = sel_status
                            save_list(st.session_state.anime_list)
                            st.success(f"Updated to **{sel_status}**")
                            st.rerun()
                    else:
                        if st.button("➕ Add to List", key=f"add_{mid}", use_container_width=True, type="primary"):
                            st.session_state.anime_list[mid] = anime_to_entry(anime, sel_status)
                            save_list(st.session_state.anime_list)
                            st.success(f"**{title}** added!")
                            st.rerun()
                with c3:
                    if in_list:
                        st.markdown(f"<span class='badge' style='background:{STATUS_COLORS[st.session_state.anime_list[mid][\"my_status\"]]}22;color:{STATUS_COLORS[st.session_state.anime_list[mid][\"my_status\"]]}'>In List ✓</span>", unsafe_allow_html=True)

                st.markdown("<hr style='border-color:#2a2a4a;margin:.5rem 0'>", unsafe_allow_html=True)
    elif st.session_state.search_query:
        st.info("No results found. Try a different query.")
    else:
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:#666">
          <div style="font-size:4rem">🔍</div>
          <p>Search for any anime above to get started.</p>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MY LIST
# ══════════════════════════════════════════════════════════════════════════════
with tab_list:
    al = st.session_state.anime_list

    # Apply sidebar filters
    items = list(al.values())
    if filter_status != "All":
        items = [i for i in items if i["my_status"] == filter_status]
    if filter_search:
        items = [i for i in items if filter_search.lower() in i["title"].lower()]

    # Group by status
    if not items:
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:#666">
          <div style="font-size:4rem">📭</div>
          <p>Your list is empty. Search for anime and add them!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        grouped: dict[str, list] = {s: [] for s in STATUS_OPTIONS}
        for item in items:
            grouped[item["my_status"]].append(item)

        for status in STATUS_OPTIONS:
            group = grouped[status]
            if not group:
                continue
            emoji = STATUS_EMOJI[status]
            color = STATUS_COLORS[status]
            st.markdown(f"<h3 style='color:{color};margin-top:1.5rem'>{emoji} {status} <span style='font-size:1rem;color:#888'>({len(group)})</span></h3>", unsafe_allow_html=True)

            for item in group:
                mid = str(item["mal_id"])
                score = item.get("score") or "N/A"
                eps   = item.get("episodes") or "?"
                genres = ", ".join(item.get("genres", [])[:3])

                with st.container():
                    col_img, col_info, col_actions = st.columns([1, 5, 2])
                    with col_img:
                        st.image(item["image"], width=65)
                    with col_info:
                        st.markdown(f"**{item['title']}**")
                        st.caption(f"⭐ {score} · 📺 {eps} eps · {genres}")
                        if item.get("notes"):
                            st.caption(f"📝 {item['notes']}")
                        # Progress for watching
                        if item["my_status"] == "Watching" and item.get("episodes"):
                            progress_key = f"prog_{mid}"
                            prog = st.slider(
                                f"Episode progress (/{eps})",
                                0, int(item["episodes"]) if item["episodes"] else 1,
                                item.get("progress", 0),
                                key=progress_key,
                            )
                            if prog != item.get("progress", 0):
                                st.session_state.anime_list[mid]["progress"] = prog
                                save_list(st.session_state.anime_list)

                    with col_actions:
                        new_status = st.selectbox(
                            "Status", STATUS_OPTIONS,
                            index=STATUS_OPTIONS.index(item["my_status"]),
                            key=f"lst_sel_{mid}",
                            label_visibility="collapsed",
                        )
                        c_upd, c_del = st.columns(2)
                        with c_upd:
                            if st.button("Save", key=f"lst_upd_{mid}", use_container_width=True):
                                st.session_state.anime_list[mid]["my_status"] = new_status
                                save_list(st.session_state.anime_list)
                                st.rerun()
                        with c_del:
                            if st.button("🗑️", key=f"lst_del_{mid}", use_container_width=True):
                                del st.session_state.anime_list[mid]
                                save_list(st.session_state.anime_list)
                                st.rerun()

                        # Notes
                        notes = st.text_input("Notes", value=item.get("notes",""), key=f"notes_{mid}",
                                              placeholder="Add notes…", label_visibility="collapsed")
                        if notes != item.get("notes",""):
                            st.session_state.anime_list[mid]["notes"] = notes
                            save_list(st.session_state.anime_list)

                    st.markdown("<hr style='border-color:#2a2a4a;margin:.3rem 0'>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — TOP ANIME
# ══════════════════════════════════════════════════════════════════════════════
with tab_top:
    st.markdown("### 🏆 Top Anime (MyAnimeList)")
    with st.spinner("Loading top anime…"):
        top = get_top_anime()

    if top:
        cols = st.columns(3)
        for i, anime in enumerate(top):
            mid   = str(anime["mal_id"])
            img   = anime["images"]["jpg"]["image_url"]
            title = anime.get("title", "Unknown")
            score = anime.get("score") or "N/A"
            eps   = anime.get("episodes") or "?"
            in_list = mid in st.session_state.anime_list

            with cols[i % 3]:
                st.image(img, use_container_width=True)
                st.markdown(f"**#{i+1} {title}**")
                st.caption(f"⭐ {score} · 📺 {eps} eps")
                if in_list:
                    cur = st.session_state.anime_list[mid]["my_status"]
                    st.markdown(f"<span class='badge' style='background:{STATUS_COLORS[cur]}22;color:{STATUS_COLORS[cur]}'>{STATUS_EMOJI[cur]} {cur}</span>", unsafe_allow_html=True)
                else:
                    if st.button("➕ Add", key=f"top_add_{mid}", use_container_width=True):
                        st.session_state.anime_list[mid] = anime_to_entry(anime, "Plan to Watch")
                        save_list(st.session_state.anime_list)
                        st.success(f"Added **{title}**!")
                        st.rerun()
                st.markdown("---")
    else:
        st.warning("Could not load top anime. Check your connection.")
