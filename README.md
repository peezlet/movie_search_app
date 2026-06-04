# movie_search_app
# 🎬 MovieSearch Pro

A desktop movie library app built with Python and Tkinter. Users can log in, browse a catalogue of 2026 films, search and filter by genre, and track what they've watched — all stored locally with no external dependencies.

---

## Features

- **User accounts** — register and log in with password hashing (SHA-256); each user has their own watched list
- **Movie catalogue** — 45 seed films across Sci-Fi, Horror, Action, Comedy, and Thriller
- **Search & filter** — live search by title or genre, filter by genre tab, sort by Title / Year / Genre
- **Watched tracking** — mark films as watched or unwatched; toggle inline from the list; filter to show only watched or only unwatched
- **Add & delete** — add custom movies with title, genre, and year validation; delete with confirmation
- **Persistent storage** — all data saved locally to JSON files (`movies_db.json`, `users.json`)
- **Dark UI** — custom dark theme built entirely with Tkinter (no external UI libraries)

---

## Screenshots

<img width="389" height="515" alt="image" src="https://github.com/user-attachments/assets/88b96249-c461-44bf-874e-dabbf3e232d8" />


---

## Getting Started

### Requirements

- Python 3.10 or higher
- No third-party libraries needed — uses only the Python standard library (`tkinter`, `hashlib`, `json`, `dataclasses`, `pathlib`)

### Run the app

```bash
git clone https://github.com/your-username/movie-search-app.git
cd movie-search-app
python movies.py
```

### First use

1. Click **"No account? Register →"** to create a user account
2. Log in with your credentials
3. Browse, search, and start marking movies as watched

---

## Project Structure

```
movie-search-app/
├── movies.py          # Main application — all logic and UI
├── movies_db.json     # Auto-generated: movie catalogue (created on first run)
├── users.json         # Auto-generated: user accounts and watched lists
└── README.md
```

---

## How It Works

The app is structured using object-oriented Python with clear separation of concerns:

| Class | Role |
|---|---|
| `Movie` | Dataclass representing a single film |
| `MovieDatabase` | Manages the film collection; handles search, sort, add, delete, and JSON persistence |
| `UserStore` | Manages user accounts; handles registration, authentication, and per-user watched lists |
| `Application` | Top-level controller; manages screen transitions between login and main view |
| `LoginScreen` | Tkinter frame for login and registration |
| `MainScreen` | Tkinter frame for the full movie browser |
| `SearchBar`, `GenreTabBar`, etc. | Reusable UI component classes |

---

## Technical Highlights

- **No external libraries** — built entirely on Python's standard library
- **SHA-256 password hashing** via `hashlib` — passwords are never stored in plain text
- **Dataclass + JSON serialisation** — `Movie` objects are stored and loaded using `dataclasses.asdict()`
- **Component-based UI** — reusable widget classes (`SearchBar`, `_TabBar` subclasses, `MovieListBox`) keep the UI code modular
- **Live search** — list refreshes on every keystroke via `<KeyRelease>` binding

---

## Possible Extensions

- Add movie ratings (1–5 stars) per user
- Export watched list to CSV
- Pull live movie data from a public API (e.g. TMDB)
- Port the UI to a web frontend using Flask or FastAPI

---

## Author

Enyimpa Dzah — [linkedin.com/in/enyimpa-dzah](https://www.linkedin.com/in/enyimpa-dzah/)
