"""movies.py — MovieSearch Pro with Login & Watched/Unwatched tracking"""

import hashlib
import json
import tkinter as tk
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

# Paths & constants

DATA_DIR    = Path(__file__).parent
MOVIES_FILE = DATA_DIR / "movies_db.json"
USERS_FILE  = DATA_DIR / "users.json"

SORT_KEYS       = ["Title", "Year", "Genre"]
WATCHED_FILTERS = ["All", "Watched", "Unwatched"]


# Seed data

_SEED_DATA: list[tuple[str, str, int]] = [
    ("Project Hail Mary",                        "Sci-Fi",   2026),
    ("Dune: Part Three",                         "Sci-Fi",   2026),
    ("Star Wars: The Mandalorian & Grogu",       "Sci-Fi",   2026),
    ("Disclosure Day",                           "Sci-Fi",   2026),
    ("The Odyssey",                              "Sci-Fi",   2026),
    ("Masters of the Universe",                  "Sci-Fi",   2026),
    ("The Super Mario Galaxy Movie",             "Sci-Fi",   2026),
    ("Backrooms",                                "Sci-Fi",   2026),
    ("Propeller",                                "Sci-Fi",   2026),
    ("The Mummy",                                "Horror",   2026),
    ("28 Years Later: The Bone Temple",          "Horror",   2026),
    ("Insidious: Out of the Further",            "Horror",   2026),
    ("Scary Movie 6",                            "Horror",   2026),
    ("Newborn",                                  "Horror",   2026),
    ("Silent Friend",                            "Horror",   2026),
    ("The Stranger",                             "Horror",   2026),
    ("An Enemy Within",                          "Horror",   2026),
    ("Spider-Man: Brand New Day",                "Action",   2026),
    ("Mortal Kombat II",                         "Action",   2026),
    ("Street Fighter",                           "Action",   2026),
    ("The Hunger Games: Sunrise on the Reaping", "Action",   2026),
    ("Cliffhanger",                              "Action",   2026),
    ("Coyote vs. Acme",                          "Action",   2026),
    ("Godzilla Minus Zero",                      "Action",   2026),
    ("Legend of the White Dragon",               "Action",   2026),
    ("Archangel",                                "Action",   2026),
    ("Mutiny",                                   "Action",   2026),
    ("I Love Boosters",                          "Comedy",   2026),
    ("The Devil Wears Prada 2",                  "Comedy",   2026),
    ("Corporate Retreat",                        "Comedy",   2026),
    ("Couples Weekend",                          "Comedy",   2026),
    ("Spa Weekend",                              "Comedy",   2026),
    ("Power Ballad",                             "Comedy",   2026),
    ("Fantasy Life",                             "Comedy",   2026),
    ("Hokum",                                    "Comedy",   2026),
    ("Deep Water",                               "Thriller", 2026),
    ("Obsession",                                "Thriller", 2026),
    ("In the Grey",                              "Thriller", 2026),
    ("Is God Is",                                "Thriller", 2026),
    ("The Brink of War",                         "Thriller", 2026),
    ("One-Way Night Coach",                      "Thriller", 2026),
    ("Forge",                                    "Thriller", 2026),
    ("Pressure",                                 "Thriller", 2026),
    ("Magic Hour",                               "Thriller", 2026),
]


# Domain: Movie

@dataclass
class Movie:
    """Represents a single movie entry."""

    title: str
    genre: str
    year: int

    def matches(self, query: str, genre_filter: str) -> bool:
        genre_ok = genre_filter == "All" or self.genre == genre_filter
        query_ok = not query or (
            query in self.title.lower() or query in self.genre.lower()
        )
        return genre_ok and query_ok

    def display_text(self) -> str:
        return f"{self.title} ({self.year}) — {self.genre}"

    def __str__(self) -> str:
        return self.display_text()


# Domain: MovieDatabase

class MovieDatabase:
    """Manages the movie collection with JSON persistence."""

    GENRES = ["All", "Sci-Fi", "Horror", "Action", "Comedy", "Thriller"]

    def __init__(self, db_file: Path = MOVIES_FILE):
        self._db_file = db_file
        self._movies: list[Movie] = self._load()

    def _load(self) -> list[Movie]:
        if self._db_file.exists():
            try:
                return [Movie(**d) for d in json.loads(self._db_file.read_text("utf-8"))]
            except Exception:
                pass
        return [Movie(t, g, y) for t, g, y in _SEED_DATA]

    def save(self) -> None:
        self._db_file.write_text(
            json.dumps([asdict(m) for m in self._movies], indent=2), "utf-8"
        )

    def search(
        self, query: str, genre_filter: str, sort_by: str = "Title"
    ) -> list[Movie]:
        q = query.strip().lower()
        results = [m for m in self._movies if m.matches(q, genre_filter)]
        key_fn = {
            "Title": lambda m: m.title.lower(),
            "Year":  lambda m: m.year,
            "Genre": lambda m: m.genre.lower(),
        }.get(sort_by, lambda m: m.title.lower())
        return sorted(results, key=key_fn)

    def title_exists(self, title: str) -> bool:
        return any(m.title.lower() == title.lower() for m in self._movies)

    def total(self) -> int:
        return len(self._movies)

    def add(self, title: str, genre: str, year: int) -> Movie:
        movie = Movie(title, genre, year)
        self._movies.append(movie)
        self.save()
        return movie

    def remove(self, movie: Movie) -> bool:
        try:
            self._movies.remove(movie)
            self.save()
            return True
        except ValueError:
            return False


# Domain: UserStore

class UserStore:
    """Handles user accounts: registration, authentication, and watched lists."""

    def __init__(self, users_file: Path = USERS_FILE):
        self._file = users_file
        # Schema: { username: { "password": sha256_hex, "watched": [title, ...] } }
        self._data: dict = self._load()

    def _load(self) -> dict:
        if self._file.exists():
            try:
                return json.loads(self._file.read_text("utf-8"))
            except Exception:
                pass
        return {}

    def _save(self) -> None:
        self._file.write_text(json.dumps(self._data, indent=2), "utf-8")

    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username: str, password: str) -> bool:
        user = self._data.get(username.lower())
        return bool(user and user["password"] == self._hash(password))

    def register(self, username: str, password: str, confirm: str) -> tuple[bool, str]:
        if len(username) < 3:
            return False, "Username must be at least 3 characters."
        if len(password) < 4:
            return False, "Password must be at least 4 characters."
        if password != confirm:
            return False, "Passwords do not match."
        if username.lower() in self._data:
            return False, "Username already taken."
        self._data[username.lower()] = {
            "password": self._hash(password),
            "watched": [],
        }
        self._save()
        return True, "Account created!"

    def get_watched(self, username: str) -> set[str]:
        return set(self._data.get(username.lower(), {}).get("watched", []))

    def is_watched(self, username: str, title: str) -> bool:
        return title in self.get_watched(username)

    def toggle_watched(self, username: str, title: str) -> bool:
        """Toggle watched status. Returns the new state (True = now watched)."""
        key = username.lower()
        if key not in self._data:
            return False
        watched: list = self._data[key]["watched"]
        if title in watched:
            watched.remove(title)
            new_state = False
        else:
            watched.append(title)
            new_state = True
        self._save()
        return new_state


# Theme

class Theme:
    ACCENT      = "#e94560"
    BG          = "#1a1a2e"
    PANEL       = "#16213e"
    FG          = "#eaeaea"
    MUTED       = "#888888"
    DARK        = "#333333"
    GREEN       = "#2e7d32"
    GREEN_LIGHT = "#4caf50"
    BLUE        = "#1565c0"
    FONT        = ("Arial", 11)
    FONT_SMALL  = ("Arial",  9)
    FONT_LARGE  = ("Arial", 13)
    FONT_TITLE  = ("Arial", 16, "bold")
    FONT_HEADER = ("Arial", 12, "bold")
    FONT_BOLD   = ("Arial", 11, "bold")


# Reusable widgets

class SearchBar(tk.Frame):
    """Search entry + Search / Clear buttons."""

    def __init__(self, parent, on_search, on_clear, **kwargs):
        super().__init__(parent, bg=Theme.BG, **kwargs)
        self._on_search = on_search
        self._on_clear  = on_clear
        self._build()

    def _build(self):
        self.entry = tk.Entry(
            self, font=Theme.FONT_LARGE, width=22,
            bg=Theme.PANEL, fg=Theme.FG,
            insertbackground=Theme.FG, relief="flat", bd=6,
        )
        self.entry.pack(side=tk.LEFT, padx=(0, 5))
        self.entry.bind("<KeyRelease>", lambda _: self._on_search())

        tk.Button(
            self, text="Search", command=self._on_search,
            bg=Theme.ACCENT, fg="white", font=Theme.FONT,
            relief="flat", padx=8,
        ).pack(side=tk.LEFT, padx=(0, 4))

        tk.Button(
            self, text="Clear", command=self._on_clear,
            bg="#444", fg="white", font=Theme.FONT,
            relief="flat", padx=8,
        ).pack(side=tk.LEFT)

    def get_query(self) -> str:
        return self.entry.get()

    def clear(self):
        self.entry.delete(0, tk.END)


class _TabBar(tk.Frame):
    """Generic row of toggle buttons — base class for all filter/sort bars."""

    def __init__(self, parent, label: str, options: list[str],
                 on_select, active_color: str, **kwargs):
        super().__init__(parent, bg=Theme.BG, **kwargs)
        self._on_select    = on_select
        self._active       = options[0]
        self._active_color = active_color
        self._buttons: dict[str, tk.Button] = {}
        self._build(label, options)

    def _build(self, label: str, options: list[str]):
        if label:
            tk.Label(
                self, text=label, font=Theme.FONT_SMALL,
                bg=Theme.BG, fg=Theme.MUTED,
            ).pack(side=tk.LEFT, padx=(0, 4))
        for opt in options:
            btn = tk.Button(
                self, text=opt, font=("Arial", 9),
                bg=self._active_color if opt == self._active else Theme.DARK,
                fg="white", relief="flat", padx=9, pady=3,
                command=lambda o=opt: self._select(o),
            )
            btn.pack(side=tk.LEFT, padx=2)
            self._buttons[opt] = btn

    def _select(self, opt: str):
        self._active = opt
        for o, btn in self._buttons.items():
            btn.config(bg=self._active_color if o == opt else Theme.DARK)
        self._on_select(opt)

    def active(self) -> str:
        return self._active


class GenreTabBar(_TabBar):
    def __init__(self, parent, genres: list[str], on_select, **kwargs):
        super().__init__(parent, label="Genre:", options=genres,
                         on_select=on_select, active_color=Theme.ACCENT, **kwargs)

    def active_genre(self) -> str:
        return self.active()


class WatchedFilterBar(_TabBar):
    def __init__(self, parent, on_filter, **kwargs):
        super().__init__(parent, label="Show:", options=WATCHED_FILTERS,
                         on_select=on_filter, active_color=Theme.GREEN, **kwargs)

    def active_filter(self) -> str:
        return self.active()


class SortBar(_TabBar):
    def __init__(self, parent, on_sort, **kwargs):
        super().__init__(parent, label="Sort:", options=SORT_KEYS,
                         on_select=on_sort, active_color=Theme.BLUE, **kwargs)

    def active_sort(self) -> str:
        return self.active()


class MovieListBox(tk.Frame):
    """Scrollable listbox that displays Movie entries with watched indicators."""

    def __init__(self, parent, on_delete, on_select=None, **kwargs):
        super().__init__(parent, bg=Theme.BG, **kwargs)
        self._on_delete = on_delete
        self._on_select = on_select
        self._index_map: list[Movie] = []
        self._build()

    def _build(self):
        scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.listbox = tk.Listbox(
            self, width=58, height=10, font=Theme.FONT,
            bg=Theme.PANEL, fg=Theme.FG,
            selectbackground=Theme.ACCENT, selectforeground="white",
            relief="flat", bd=0, activestyle="none",
            yscrollcommand=scrollbar.set,
        )
        scrollbar.config(command=self.listbox.yview)
        self.listbox.pack(side=tk.LEFT)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.listbox.bind("<Delete>", lambda _: self._on_delete())
        if self._on_select:
            self.listbox.bind("<<ListboxSelect>>", lambda _: self._on_select())

    def populate(self, movies: list[Movie], watched_set: set[str]):
        self.listbox.delete(0, tk.END)
        self._index_map = list(movies)
        if movies:
            for i, m in enumerate(movies):
                prefix = "✓  " if m.title in watched_set else "    "
                self.listbox.insert(tk.END, prefix + m.display_text())
                if m.title in watched_set:
                    self.listbox.itemconfig(i, fg=Theme.GREEN_LIGHT)
        else:
            self.listbox.insert(tk.END, "  No movies found.")

    def selected_movie(self) -> Movie | None:
        sel = self.listbox.curselection()
        if not sel:
            return None
        idx = sel[0]
        return self._index_map[idx] if idx < len(self._index_map) else None


class AddMovieForm(tk.Frame):
    """Form for adding a new movie."""

    def __init__(self, parent, genres: list[str], on_add, **kwargs):
        super().__init__(parent, bg=Theme.BG, **kwargs)
        self._on_add = on_add
        self._genres = genres
        self._build()

    def _form_row(self, label_text: str, widget_factory):
        row = tk.Frame(self, bg=Theme.BG)
        row.pack(pady=3)
        tk.Label(
            row, text=label_text, font=Theme.FONT,
            bg=Theme.BG, fg=Theme.FG, width=7, anchor="e",
        ).pack(side=tk.LEFT, padx=(0, 6))
        widget = widget_factory(row)
        widget.pack(side=tk.LEFT)
        return widget

    def _build(self):
        self.title_entry = self._form_row(
            "Title:",
            lambda p: tk.Entry(
                p, font=Theme.FONT, width=26,
                bg=Theme.PANEL, fg=Theme.FG,
                insertbackground=Theme.FG, relief="flat", bd=6,
            ),
        )
        self.title_entry.bind("<Return>", lambda _: self._on_add())

        self.genre_var = tk.StringVar(value=self._genres[1])
        self.genre_menu = self._form_row(
            "Genre:",
            lambda p: tk.OptionMenu(p, self.genre_var, *self._genres[1:]),
        )
        self.genre_menu.config(
            bg=Theme.PANEL, fg=Theme.FG,
            activebackground=Theme.ACCENT,
            highlightthickness=0, relief="flat", font=Theme.FONT,
        )

        self.year_entry = self._form_row(
            "Year:",
            lambda p: tk.Entry(
                p, font=Theme.FONT, width=10,
                bg=Theme.PANEL, fg=Theme.FG,
                insertbackground=Theme.FG, relief="flat", bd=6,
            ),
        )
        self.year_entry.insert(0, str(datetime.now().year))
        self.year_entry.bind("<Return>", lambda _: self._on_add())

    def get_values(self) -> tuple[str, str, str]:
        return (
            self.title_entry.get().strip(),
            self.genre_var.get(),
            self.year_entry.get().strip(),
        )

    def clear(self):
        self.title_entry.delete(0, tk.END)
        self.year_entry.delete(0, tk.END)
        self.year_entry.insert(0, str(datetime.now().year))


# Screen: Login / Register

class LoginScreen(tk.Frame):
    """Combined login and registration screen."""

    def __init__(self, parent, users: UserStore, on_login, **kwargs):
        super().__init__(parent, bg=Theme.BG, **kwargs)
        self._users    = users
        self._on_login = on_login
        self._mode     = "login"   # "login" | "register"
        self._build()


    def _build(self):
        # Header
        tk.Label(
            self, text="🎬 MovieSearch Pro",
            font=Theme.FONT_TITLE, bg=Theme.BG, fg=Theme.ACCENT,
        ).pack(pady=(36, 4))
        tk.Label(
            self, text="Your personal 2026 movie library",
            font=Theme.FONT_SMALL, bg=Theme.BG, fg=Theme.MUTED,
        ).pack()

        # Mode title
        self._title_lbl = tk.Label(
            self, text="Sign In",
            font=Theme.FONT_HEADER, bg=Theme.BG, fg=Theme.FG,
        )
        self._title_lbl.pack(pady=(22, 4))

        # Inline error message
        self._error_lbl = tk.Label(
            self, text="", font=Theme.FONT_SMALL,
            bg=Theme.BG, fg=Theme.ACCENT,
        )
        self._error_lbl.pack(pady=(0, 4))

        # Form (grid layout so confirm row can appear/disappear cleanly)
        form = tk.Frame(self, bg=Theme.BG)
        form.pack()

        def _entry(row_idx: int, show: str = "") -> tk.Entry:
            e = tk.Entry(
                form, font=Theme.FONT, width=22,
                bg=Theme.PANEL, fg=Theme.FG,
                insertbackground=Theme.FG, relief="flat", bd=6,
                show=show,
            )
            e.grid(row=row_idx, column=1, pady=5)
            return e

        def _label(row_idx: int, text: str) -> tk.Label:
            l = tk.Label(
                form, text=text, font=Theme.FONT,
                bg=Theme.BG, fg=Theme.FG, width=10, anchor="e",
            )
            l.grid(row=row_idx, column=0, pady=5, padx=(0, 8))
            return l

        _label(0, "Username:")
        self._user_entry = _entry(0)
        self._user_entry.bind("<Return>", lambda _: self._pass_entry.focus())

        _label(1, "Password:")
        self._pass_entry = _entry(1, show="*")
        self._pass_entry.bind("<Return>", lambda _: self._submit())

        # Confirm row — hidden in login mode
        self._confirm_lbl = _label(2, "Confirm:")
        self._confirm_entry = _entry(2, show="*")
        self._confirm_entry.bind("<Return>", lambda _: self._submit())
        self._confirm_lbl.grid_remove()
        self._confirm_entry.grid_remove()

        # Submit button
        self._submit_btn = tk.Button(
            self, text="Login", command=self._submit,
            bg=Theme.ACCENT, fg="white", font=Theme.FONT_BOLD,
            relief="flat", padx=24, pady=7,
        )
        self._submit_btn.pack(pady=14)

        # Mode-switch link
        self._switch_lbl = tk.Label(
            self, text="No account? Register →",
            font=Theme.FONT_SMALL, bg=Theme.BG, fg=Theme.MUTED, cursor="hand2",
        )
        self._switch_lbl.pack()
        self._switch_lbl.bind("<Button-1>", lambda _: self._switch_mode())

        self._user_entry.focus()


    def _switch_mode(self):
        self._mode = "register" if self._mode == "login" else "login"
        self._error_lbl.config(text="")
        if self._mode == "register":
            self._title_lbl.config(text="Create Account")
            self._submit_btn.config(text="Register")
            self._switch_lbl.config(text="Have an account? Sign In →")
            self._confirm_lbl.grid()
            self._confirm_entry.grid()
        else:
            self._title_lbl.config(text="Sign In")
            self._submit_btn.config(text="Login")
            self._switch_lbl.config(text="No account? Register →")
            self._confirm_lbl.grid_remove()
            self._confirm_entry.grid_remove()

    def _submit(self):
        username = self._user_entry.get().strip()
        password = self._pass_entry.get()
        self._error_lbl.config(text="")

        if not username or not password:
            self._error_lbl.config(text="Please fill in all fields.")
            return

        if self._mode == "login":
            if self._users.authenticate(username, password):
                self._on_login(username)
            else:
                self._error_lbl.config(text="Invalid username or password.")
        else:
            confirm = self._confirm_entry.get()
            ok, msg = self._users.register(username, password, confirm)
            if ok:
                self._on_login(username)
            else:
                self._error_lbl.config(text=msg)


# Screen: Main movie browser

class MainScreen(tk.Frame):
    """Full movie browser — shown after successful login."""

    def __init__(
        self,
        parent,
        db: MovieDatabase,
        users: UserStore,
        username: str,
        on_logout,
        **kwargs,
    ):
        super().__init__(parent, bg=Theme.BG, **kwargs)
        self.db         = db
        self.users      = users
        self.username   = username
        self._on_logout = on_logout
        self._build_ui()
        self._refresh_list()


    # Build

    def _build_ui(self):
        self._build_header()
        self._build_search_bar()
        self._build_genre_tabs()
        self._build_watched_filter()
        self._build_sort_bar()
        self._build_count_label()
        self._build_movie_list()
        self._build_action_buttons()
        self._build_divider()
        self._build_add_form()

    def _build_header(self):
        top = tk.Frame(self, bg=Theme.BG)
        top.pack(fill=tk.X, padx=16, pady=(14, 0))

        tk.Label(
            top, text="🎬 MovieSearch Pro",
            font=Theme.FONT_TITLE, bg=Theme.BG, fg=Theme.ACCENT,
        ).pack(side=tk.LEFT)

        tk.Button(
            top, text="Logout", command=self._logout,
            bg=Theme.DARK, fg=Theme.MUTED, font=Theme.FONT_SMALL,
            relief="flat", padx=8, pady=3,
        ).pack(side=tk.RIGHT)

        tk.Label(
            top, text=f"👤 {self.username}",
            font=Theme.FONT_SMALL, bg=Theme.BG, fg=Theme.MUTED,
        ).pack(side=tk.RIGHT, padx=(0, 10))

        self._subtitle_lbl = tk.Label(
            self, font=Theme.FONT_SMALL, bg=Theme.BG, fg=Theme.MUTED,
        )
        self._subtitle_lbl.pack()
        self._update_subtitle()

    def _update_subtitle(self):
        watched_n = len(self.users.get_watched(self.username))
        total_n   = self.db.total()
        self._subtitle_lbl.config(
            text=(
                f"2026 Edition  •  {total_n} Films  •  "
                f"✓ {watched_n} Watched  •  ○ {total_n - watched_n} Unwatched"
            )
        )

    def _build_search_bar(self):
        self.search_bar = SearchBar(
            self, on_search=self._refresh_list, on_clear=self._clear_search,
        )
        self.search_bar.pack(pady=8)

    def _build_genre_tabs(self):
        self.genre_tabs = GenreTabBar(
            self, genres=MovieDatabase.GENRES,
            on_select=lambda _: self._refresh_list(),
        )
        self.genre_tabs.pack(pady=(2, 0))

    def _build_watched_filter(self):
        self.watched_bar = WatchedFilterBar(
            self, on_filter=lambda _: self._refresh_list(),
        )
        self.watched_bar.pack(pady=(4, 0))

    def _build_sort_bar(self):
        self.sort_bar = SortBar(
            self, on_sort=lambda _: self._refresh_list(),
        )
        self.sort_bar.pack(pady=(4, 0))

    def _build_count_label(self):
        self.count_label = tk.Label(
            self, text="", font=Theme.FONT_SMALL, bg=Theme.BG, fg=Theme.MUTED,
        )
        self.count_label.pack(pady=(4, 0))

    def _build_movie_list(self):
        self.movie_list = MovieListBox(
            self,
            on_delete=self._delete_movie,
            on_select=self._on_list_select,
        )
        self.movie_list.pack(padx=20, pady=(2, 2))

    def _build_action_buttons(self):
        row = tk.Frame(self, bg=Theme.BG)
        row.pack(pady=6)

        self._watch_btn = tk.Button(
            row, text="✓  Mark as Watched",
            command=self._toggle_watched,
            bg=Theme.GREEN, fg="white", font=Theme.FONT,
            relief="flat", padx=10, pady=4,
        )
        self._watch_btn.pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            row, text="🗑  Delete Selected",
            command=self._delete_movie,
            bg=Theme.DARK, fg=Theme.FG, font=Theme.FONT,
            relief="flat", padx=10, pady=4,
        ).pack(side=tk.LEFT)

    def _build_divider(self):
        tk.Frame(self, height=1, bg=Theme.ACCENT).pack(fill=tk.X, padx=20, pady=6)
        tk.Label(
            self, text="Add a New Movie",
            font=Theme.FONT_HEADER, bg=Theme.BG, fg=Theme.FG,
        ).pack()

    def _build_add_form(self):
        self.add_form = AddMovieForm(
            self, genres=MovieDatabase.GENRES, on_add=self._add_movie,
        )
        self.add_form.pack(pady=4)
        tk.Button(
            self, text="＋  Add Movie",
            command=self._add_movie,
            bg=Theme.ACCENT, fg="white", font=Theme.FONT_BOLD,
            relief="flat", padx=12, pady=6,
        ).pack(pady=8)


    # Refresh helpers

    def _refresh_list(self):
        query    = self.search_bar.get_query()
        genre    = self.genre_tabs.active_genre()
        sort     = self.sort_bar.active_sort()
        w_filter = self.watched_bar.active_filter()

        movies      = self.db.search(query, genre, sort_by=sort)
        watched_set = self.users.get_watched(self.username)

        if w_filter == "Watched":
            movies = [m for m in movies if m.title in watched_set]
        elif w_filter == "Unwatched":
            movies = [m for m in movies if m.title not in watched_set]

        self.movie_list.populate(movies, watched_set)

        n = len(movies)
        self.count_label.config(text=f"{n} movie{'s' if n != 1 else ''} found")
        self._update_subtitle()
        self._update_watch_btn()

    def _on_list_select(self):
        self._update_watch_btn()

    def _update_watch_btn(self):
        movie = self.movie_list.selected_movie()
        if movie and self.users.is_watched(self.username, movie.title):
            self._watch_btn.config(text="✗  Remove from Watched", bg=Theme.ACCENT)
        else:
            self._watch_btn.config(text="✓  Mark as Watched", bg=Theme.GREEN)


    # Event handlers

    def _clear_search(self):
        self.search_bar.clear()
        self._refresh_list()

    def _toggle_watched(self):
        movie = self.movie_list.selected_movie()
        if not movie:
            messagebox.showwarning("No Selection", "Please select a movie first.")
            return
        self.users.toggle_watched(self.username, movie.title)
        self._refresh_list()

    def _add_movie(self):
        title, genre, year_str = self.add_form.get_values()
        if not title or not year_str:
            messagebox.showwarning("Missing Fields", "Please fill in the title and year.")
            return
        if not year_str.isdigit() or not (1888 <= int(year_str) <= 2100):
            messagebox.showwarning("Invalid Year",
                                   "Please enter a valid 4-digit year (1888–2100).")
            return
        if self.db.title_exists(title):
            messagebox.showwarning("Duplicate", f'"{title}" is already in the list.')
            return
        self.db.add(title, genre, int(year_str))
        self.add_form.clear()
        self._refresh_list()
        messagebox.showinfo("Added", f'"{title}" has been added!')

    def _delete_movie(self):
        movie = self.movie_list.selected_movie()
        if not movie:
            messagebox.showwarning("No Selection", "Please select a movie to delete.")
            return
        if messagebox.askyesno("Confirm", f'Delete "{movie.title}"?'):
            self.db.remove(movie)
            self._refresh_list()

    def _logout(self):
        self._on_logout()


# Application controller

class Application:
    """Top-level controller: manages screen transitions and shared state."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MovieSearch Pro  •  2026 Library")
        self.root.configure(bg=Theme.BG)
        self.root.resizable(False, False)

        self.db    = MovieDatabase()
        self.users = UserStore()
        self._frame: tk.Frame | None = None

        self._show_login()

    def run(self):
        self.root.mainloop()

    def _show_login(self):
        if self._frame:
            self._frame.destroy()
        self.root.geometry("520x440")
        self._frame = LoginScreen(self.root, self.users, on_login=self._on_login)
        self._frame.pack(fill=tk.BOTH, expand=True)

    def _show_main(self, username: str):
        if self._frame:
            self._frame.destroy()
        self.root.geometry("520x830")
        self._frame = MainScreen(
            self.root, self.db, self.users, username,
            on_logout=self._show_login,
        )
        self._frame.pack(fill=tk.BOTH, expand=True)

    def _on_login(self, username: str):
        self._show_main(username)


if __name__ == "__main__":
    Application().run()