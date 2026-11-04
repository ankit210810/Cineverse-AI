"""Movie Carousel Component for Cineverse AI.

Renders horizontal scrolling Netflix/Duckshow-style movie carousels with:
- Drag-to-scroll & mousewheel horizontal movement
- Floating left/right navigation arrows
- Card hover elevation with center glowing yellow Play button, top-right plus button, tags, and title
- Real-time yellow horizontal progress indicator bar matching user's video
"""

from typing import Dict, List, Any, Optional
import html
from ui.components import render_html
from services.poster_service import get_movie_poster_url
from services.user_service import is_in_watchlist

FALLBACK_POSTER = "https://image.tmdb.org/t/p/w500/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg"


def render_movie_carousel(
    title_prefix: str,
    highlight_word: str,
    movies: List[Dict[str, Any]],
    user_id: int,
    carousel_id: str,
    view_all_link: str = "?nav=movies"
) -> None:
    """Renders a full-width horizontal scrolling movie carousel with progress tracking."""
    if not movies:
        return

    cards_html = []
    for idx, m in enumerate(movies):
        mid = m.get("movie_id") or m.get("id", 10003)
        raw_title = m.get("title", "Untitled")
        title_clean = raw_title.split("(")[0].strip()
        escaped_title = html.escape(title_clean)
        
        poster_url = get_movie_poster_url(mid, raw_title)
        if not poster_url:
            poster_url = m.get("poster") or FALLBACK_POSTER

        year = m.get("release_year") or m.get("year", "2024")
        genres = m.get("genres_list") or m.get("genres", ["Cinema"])
        if isinstance(genres, str):
            genres = [g.strip() for g in genres.split("|") if g.strip()]
        
        genre_badge = html.escape((genres[0] if genres else "Cinema").upper())
        quality_badge = "4K ULTRA" if idx % 2 == 0 else "HD"

        raw_rating = m.get("avg_rating") or m.get("rating", 4.5)
        try:
            rating_str = f"{float(raw_rating):.1f}"
        except (ValueError, TypeError):
            rating_str = "4.5"

        in_wl = is_in_watchlist(user_id, mid)
        wl_icon = "✓" if in_wl else "+"
        wl_title = "Remove from My List" if in_wl else "Add to My List"

        card_markup = f"""
            <div class="carousel-card" data-movie-id="{mid}">
                <div class="card-poster-bg" style="background-image: url('{poster_url}');"></div>
                <div class="card-glass-overlay">
                    <div class="card-top-actions">
                        <a href="?toggle_wl={mid}" target="_self" class="card-btn-plus" title="{wl_title}">{wl_icon}</a>
                    </div>
                    <div class="card-center-play-wrap">
                        <a href="?play={mid}" target="_self" class="card-btn-play" title="Play Demo of {escaped_title}">
                            <span class="card-play-triangle">▶</span>
                        </a>
                    </div>
                    <div class="card-bottom-info">
                        <div class="card-tags">
                            <span class="card-tag">{genre_badge}</span>
                            <span class="card-tag">{quality_badge}</span>
                        </div>
                        <a href="?info={mid}" target="_self" class="card-title-link">
                            <div class="card-movie-title" title="{escaped_title}">{escaped_title}</div>
                        </a>
                        <div class="card-movie-sub">{year} • {genre_badge} • ★ {rating_str}</div>
                    </div>
                </div>
            </div>
        """
        cards_html.append(card_markup)

    all_cards = "\n".join(cards_html)

    markup = f"""
        <div class="carousel-section-container" id="section-{carousel_id}">
            <div class="carousel-section-header">
                <h2 class="carousel-section-title">
                    {html.escape(title_prefix)} <span class="carousel-title-highlight">{html.escape(highlight_word)}</span>
                </h2>
                <a href="{view_all_link}" target="_self" class="carousel-view-all">VIEW ALL &gt;</a>
            </div>
            <div class="movie-carousel-wrapper" id="{carousel_id}">
                <button class="carousel-arrow carousel-arrow-prev" aria-label="Scroll Left">❮</button>
                <div class="movie-carousel-track">
                    {all_cards}
                </div>
                <button class="carousel-arrow carousel-arrow-next" aria-label="Scroll Right">❯</button>
                <div class="carousel-progress-track">
                    <div class="carousel-progress-bar"></div>
                </div>
            </div>
        </div>
    """
    render_html(markup)
