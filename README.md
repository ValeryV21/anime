# 🎌 Anime Tracker

A dark-themed Streamlit app to **search, track, and manage** your anime watchlist — powered by the free [Jikan API](https://jikan.moe/) (MyAnimeList wrapper, no API key needed).

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔍 Global Search | Search any anime by name via Jikan / MAL |
| 📋 My List | Add anime with status: Plan to Watch, Watching, Completed, On Hold, Dropped |
| 🏆 Top Anime | Browse MAL's all-time top 12 anime |
| 💾 Persistent Memory | Your list is saved to `anime_list.json` on disk |
| 📺 Episode Progress | Track how many episodes you've watched |
| 📝 Notes | Add personal notes to any anime |
| 🔎 Sidebar Filters | Filter your list by status or title |
| 📊 Stats | Quick overview of your totals in the sidebar |

---

## 🚀 Running Locally

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/anime-tracker.git
cd anime-tracker
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
streamlit run app.py
```

The app opens at **http://localhost:8501**.

---

## ☁️ Deploy to Streamlit Community Cloud (free)

1. Push this repo to GitHub (public or private).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app** → select your repo → set `app.py` as the main file.
4. Click **Deploy** — that's it!

> **Note:** On Streamlit Cloud the `anime_list.json` file resets when the app restarts. For persistent cloud storage, consider replacing the JSON file with a free [Supabase](https://supabase.com) or [MongoDB Atlas](https://www.mongodb.com/atlas) database. See the bottom of this README for instructions.

---

## 📁 Project Structure

```
anime-tracker/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── .gitignore          # Excludes anime_list.json & secrets
└── README.md
```

---

## 🗄️ Persistent Cloud Storage (Optional)

If you want your list to survive Streamlit Cloud restarts, swap the JSON file for **Supabase**:

1. Create a free project at [supabase.com](https://supabase.com).
2. Run this SQL in the Supabase SQL editor:
```sql
create table anime_list (
  mal_id text primary key,
  data jsonb not null
);
```
3. Add your Supabase URL and anon key to `.streamlit/secrets.toml`:
```toml
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "your-anon-key"
```
4. Replace `load_list()` / `save_list()` in `app.py` with Supabase client calls.

---

## 📡 API

This app uses the [Jikan REST API v4](https://docs.api.jikan.moe/) — a free, unofficial MyAnimeList API. **No API key required.**

Rate limit: 3 req/sec, 60 req/min (handled automatically by the app's caching).

---

## License

MIT
