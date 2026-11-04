"""Netflix-Style Hero Movie Slider & Carousel for Cineverse AI.

Features:
- Dynamic 7-movie rotating banner with high-definition backdrops.
- Automatic rotation every 7 seconds with animated progress bars.
- Pause on hover, resume on mouse leave.
- Left and right navigation arrows.
- Clickable indicator bars to jump to any movie.
- Mobile touch swipe gestures.
- Action buttons: '▶ Play' (triggers video trailer) and 'ⓘ More Info' (triggers details modal).
"""

import streamlit as st
import json
from typing import Dict, Any, List

FEATURED_HERO_MOVIES: List[Dict[str, Any]] = [
    {
        "id": 10003,
        "title": "Interstellar",
        "tagline": "Mankind was born on Earth. It was never meant to die here.",
        "overview": "When Earth becomes uninhabitable in the future, a farmer and ex-NASA pilot, Joseph Cooper, is tasked to pilot a spacecraft with a team of researchers through a wormhole near Saturn in search of a new home for mankind.",
        "year": "2014",
        "runtime": "2h 49m",
        "rating": "8.7",
        "match_pct": "99% Match",
        "badge": "★ Intelligent Recommendation",
        "genres": ["Sci-Fi", "Adventure", "Drama"],
        "backdrop": "https://image.tmdb.org/t/p/original/xJHokMbljvjADYdit5fK5VQsXEG.jpg",
        "poster": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg"
    },
    {
        "id": 10001,
        "title": "Inception",
        "tagline": "Your mind is the scene of the crime.",
        "overview": "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O., but his tragic past may doom the project and his team to disaster.",
        "year": "2010",
        "runtime": "2h 28m",
        "rating": "8.8",
        "match_pct": "98% Match",
        "badge": "🔥 Trending #1 in Sci-Fi",
        "genres": ["Action", "Sci-Fi", "Thriller"],
        "backdrop": "https://image.tmdb.org/t/p/original/s3TBrRGB1iav7gFOCNx3H31MoES.jpg",
        "poster": "https://image.tmdb.org/t/p/w500/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg"
    },
    {
        "id": 10002,
        "title": "The Matrix",
        "tagline": "Welcome to the Real World.",
        "overview": "When a beautiful stranger leads computer hacker Neo to a forbidding underworld, he discovers the shocking truth--the life he knows is the elaborate deception of an evil cyber-intelligence.",
        "year": "1999",
        "runtime": "2h 16m",
        "rating": "8.7",
        "match_pct": "97% Match",
        "badge": "⚡ Cyberpunk Masterpiece",
        "genres": ["Sci-Fi", "Action"],
        "backdrop": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=2000&auto=format&fit=crop",
        "poster": "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg"
    },
    {
        "id": 10006,
        "title": "Dune",
        "tagline": "Beyond fear, destiny awaits.",
        "overview": "Paul Atreides leads nomadic tribes in a battle to control the desert planet Arrakis and its critical spice supply. Betrayal strikes as rival factions clash in an epic struggle across the sands.",
        "year": "2021",
        "runtime": "2h 35m",
        "rating": "8.0",
        "match_pct": "96% Match",
        "badge": "🏆 6 Academy Awards",
        "genres": ["Sci-Fi", "Adventure"],
        "backdrop": "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?q=80&w=2000&auto=format&fit=crop",
        "poster": "https://image.tmdb.org/t/p/w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg"
    },
    {
        "id": 10004,
        "title": "Arrival",
        "tagline": "Why are they here?",
        "overview": "A linguist works with the military to communicate with alien lifeforms after twelve mysterious spacecraft appear around the world, racing against time to prevent a planetary war.",
        "year": "2016",
        "runtime": "1h 56m",
        "rating": "7.9",
        "match_pct": "95% Match",
        "badge": "✨ AI Recommendation (Because you liked Interstellar)",
        "genres": ["Sci-Fi", "Mystery", "Drama"],
        "backdrop": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=2000&auto=format&fit=crop",
        "poster": "https://image.tmdb.org/t/p/w500/x2FJsf1ElAgr63Y3PNPtJrcmpoe.jpg"
    },
    {
        "id": 10005,
        "title": "The Dark Knight",
        "tagline": "Welcome to a world without rules.",
        "overview": "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.",
        "year": "2008",
        "runtime": "2h 32m",
        "rating": "9.0",
        "match_pct": "99% Match",
        "badge": "★ All-Time Highest Rated",
        "genres": ["Action", "Crime", "Drama"],
        "backdrop": "https://image.tmdb.org/t/p/original/nMKdUUepR0i5zn0y1T4CsSB5chy.jpg",
        "poster": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg"
    },
    {
        "id": 50,
        "title": "Star Wars: A New Hope",
        "tagline": "A long time ago in a galaxy far, far away...",
        "overview": "Luke Skywalker joins forces with a Jedi Knight, a cocky pilot, a Wookiee and two droids to save the galaxy from the Empire's world-destroying battle station, while also attempting to rescue Princess Leia.",
        "year": "1977",
        "runtime": "2h 01m",
        "rating": "8.6",
        "match_pct": "94% Match",
        "badge": "🌌 Galactic Epic Classic",
        "genres": ["Sci-Fi", "Adventure", "Fantasy"],
        "backdrop": "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?q=80&w=2000&auto=format&fit=crop",
        "poster": "https://image.tmdb.org/t/p/w500/6FfCtAuVAW8XJjZ7eWeLibRLWTw.jpg"
    }
]


def render_netflix_hero_slider():
    """Renders the interactive Netflix-style hero slider with auto-rotation, pause on hover, and full controls."""
    slides_json = json.dumps(FEATURED_HERO_MOVIES).replace("'", "&#39;")

    slider_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            -webkit-font-smoothing: antialiased;
        }}
        html, body {{
            background: transparent;
            overflow: hidden;
            width: 100%;
            height: 100%;
        }}
        
        .slider-wrapper {{
            position: relative;
            width: 100%;
            height: 480px;
            border-radius: 20px;
            overflow: hidden;
            background: #070510;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.7), 0 0 30px rgba(139, 44, 245, 0.15);
            user-select: none;
        }}
        
        /* Slides Container */
        .slide-item {{
            position: absolute;
            inset: 0;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.8s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
        }}
        
        .slide-item.active {{
            opacity: 1;
            pointer-events: auto;
            z-index: 2;
        }}
        
        /* Background Backdrop Image with Ken-Burns scale effect */
        .slide-bg {{
            position: absolute;
            inset: 0;
            background-size: cover;
            background-position: center 25%;
            transform: scale(1.0);
            transition: transform 7s ease-out;
        }}
        
        .slide-item.active .slide-bg {{
            transform: scale(1.05);
        }}
        
        /* Cinematic Dark Gradient Masks (Left for text readability, Bottom for shelf blend) */
        .slide-overlay {{
            position: absolute;
            inset: 0;
            background: 
                linear-gradient(90deg, rgba(7, 5, 16, 0.98) 0%, rgba(7, 5, 16, 0.88) 32%, rgba(7, 5, 16, 0.45) 60%, transparent 100%),
                linear-gradient(0deg, rgba(7, 5, 16, 1) 0%, rgba(7, 5, 16, 0.7) 18%, transparent 50%),
                linear-gradient(180deg, rgba(7, 5, 16, 0.5) 0%, transparent 25%);
            z-index: 1;
        }}
        
        /* Left Content Block */
        .slide-content {{
            position: relative;
            z-index: 3;
            max-width: 620px;
            padding: 40px 48px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        
        /* Badge */
        .hero-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            align-self: flex-start;
            background: rgba(139, 44, 245, 0.28);
            border: 1px solid rgba(192, 38, 255, 0.5);
            color: #E2B5FF;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.4px;
            text-transform: uppercase;
            box-shadow: 0 0 16px rgba(139, 44, 245, 0.4);
            backdrop-filter: blur(8px);
        }}
        
        /* Title */
        .hero-title {{
            font-size: 2.85rem;
            font-weight: 900;
            color: #FFFFFF;
            line-height: 1.1;
            letter-spacing: -0.8px;
            text-shadow: 0 4px 24px rgba(0, 0, 0, 0.85);
        }}
        
        /* Metadata Row */
        .hero-meta-row {{
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
            font-size: 0.86rem;
            margin-top: 2px;
        }}
        
        .meta-match {{
            color: #46D369;
            font-weight: 800;
        }}
        
        .meta-rating {{
            color: #FFD500;
            font-weight: 700;
            background: rgba(255, 213, 0, 0.15);
            padding: 2px 7px;
            border-radius: 6px;
            border: 1px solid rgba(255, 213, 0, 0.35);
        }}
        
        .meta-year, .meta-runtime {{
            color: #C0C0D4;
            font-weight: 500;
        }}
        
        .meta-genres {{
            color: #9D44F7;
            font-weight: 600;
            background: rgba(157, 68, 247, 0.15);
            padding: 2px 8px;
            border-radius: 6px;
            border: 1px solid rgba(157, 68, 247, 0.3);
        }}
        
        /* Overview Synopsis */
        .hero-overview {{
            color: #D8D8E8;
            font-size: 0.94rem;
            line-height: 1.5;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-shadow: 0 2px 8px rgba(0, 0, 0, 0.8);
            margin-top: 4px;
        }}
        
        /* Buttons Row */
        .hero-btn-row {{
            display: flex;
            align-items: center;
            gap: 14px;
            margin-top: 10px;
        }}
        
        .btn-play {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: #FFFFFF;
            color: #000000;
            padding: 9px 24px;
            border-radius: 5px;
            font-size: 1rem;
            font-weight: 800;
            text-decoration: none;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
            border: none;
        }}
        
        .btn-play:hover {{
            background: rgba(255, 255, 255, 0.85);
            color: #000000;
            transform: scale(1.03);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.7);
        }}
        
        .btn-info {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: rgba(109, 109, 110, 0.7);
            color: #FFFFFF;
            padding: 9px 22px;
            border-radius: 5px;
            font-size: 1rem;
            font-weight: 700;
            text-decoration: none;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.18);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
        }}
        
        .btn-info:hover {{
            background: rgba(109, 109, 110, 0.45);
            color: #FFFFFF;
            border-color: rgba(255, 255, 255, 0.35);
            transform: scale(1.02);
        }}

        /* Maturity rating badge (e.g. U/A 16+) matching Netflix */
        .hero-maturity-badge {{
            position: absolute;
            right: 0;
            bottom: 40px;
            background: rgba(51, 51, 51, 0.65);
            backdrop-filter: blur(8px);
            border-left: 3.5px solid #E5E5E5;
            color: #E5E5E5;
            padding: 4px 18px 4px 12px;
            font-size: 0.9rem;
            font-weight: 700;
            letter-spacing: 0.6px;
            z-index: 5;
            user-select: none;
        }}
        
        /* Navigation Arrows */
        .hero-arrow {{
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            z-index: 10;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: rgba(14, 10, 28, 0.65);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.18);
            color: #FFFFFF;
            font-size: 1.3rem;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            opacity: 0.6;
        }}
        
        .slider-wrapper:hover .hero-arrow {{
            opacity: 1;
        }}
        
        .hero-arrow:hover {{
            background: rgba(157, 68, 247, 0.85);
            border-color: #C026FF;
            box-shadow: 0 0 20px rgba(157, 68, 247, 0.8);
            transform: translateY(-50%) scale(1.12);
        }}
        
        .arrow-prev {{
            left: 18px;
        }}
        
        .arrow-next {{
            right: 18px;
        }}
        
        /* Bottom Pagination Progress Bars */
        .hero-indicators {{
            position: absolute;
            bottom: 22px;
            right: 48px;
            z-index: 10;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .indicator-item {{
            width: 28px;
            height: 4px;
            background: rgba(255, 255, 255, 0.25);
            border-radius: 3px;
            cursor: pointer;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }}
        
        .indicator-item:hover {{
            background: rgba(255, 255, 255, 0.5);
            width: 34px;
        }}
        
        .indicator-item.active {{
            width: 42px;
            background: rgba(255, 255, 255, 0.35);
        }}
        
        .indicator-fill {{
            position: absolute;
            top: 0;
            left: 0;
            height: 100%;
            width: 0%;
            background: #9D44F7;
            box-shadow: 0 0 10px #C026FF;
            border-radius: 3px;
        }}
        
        .indicator-item.active .indicator-fill {{
            width: 100%;
            transition: width 2s linear;
        }}
        
        @media (max-width: 768px) {{
            .slider-wrapper {{
                height: 420px;
            }}
            .slide-content {{
                padding: 24px;
            }}
            .hero-title {{
                font-size: 1.9rem;
            }}
            .hero-overview {{
                -webkit-line-clamp: 2;
                font-size: 0.85rem;
            }}
            .hero-arrow {{
                width: 36px;
                height: 36px;
                font-size: 1rem;
            }}
            .hero-indicators {{
                right: 24px;
                bottom: 16px;
            }}
        }}
    </style>
    </head>
    <body>
    <div class="slider-wrapper" id="cineverseSlider">
        <!-- Slides will be rendered here -->
        <div id="slidesContainer"></div>
        
        <!-- Left & Right Controls -->
        <button class="hero-arrow arrow-prev" id="btnPrev" aria-label="Previous Slide">❮</button>
        <button class="hero-arrow arrow-next" id="btnNext" aria-label="Next Slide">❯</button>
        
        <!-- Bottom Pagination Indicators -->
        <div class="hero-indicators" id="indicatorsContainer"></div>
    </div>

    <script>
    (function() {{
        const movies = {slides_json};
        let currentIndex = 0;
        let slideTimer = null;
        const DURATION = 2000;
        let isPaused = false;
        
        const slidesContainer = document.getElementById('slidesContainer');
        const indicatorsContainer = document.getElementById('indicatorsContainer');
        const sliderWrapper = document.getElementById('cineverseSlider');
        
        // Build Slides HTML
        movies.forEach((m, idx) => {{
            const slide = document.createElement('div');
            slide.className = 'slide-item' + (idx === 0 ? ' active' : '');
            slide.id = 'slide-' + idx;
            
            slide.innerHTML = `
                <div class="slide-bg" style="background-image: url('${{m.backdrop}}');"></div>
                <div class="slide-overlay"></div>
                <div class="slide-content">
                    <div class="hero-badge"><span>★</span> ${{m.badge}}</div>
                    <h1 class="hero-title">${{m.title}}</h1>
                    <div class="hero-meta-row">
                        <span class="meta-match">${{m.match_pct}}</span>
                        <span class="meta-rating">★ ${{m.rating}}</span>
                        <span class="meta-year">${{m.year}}</span>
                        <span class="meta-runtime">${{m.runtime}}</span>
                        <span class="meta-genres">${{m.genres.join(' • ')}}</span>
                    </div>
                    <p class="hero-overview">${{m.overview}}</p>
                    <div class="hero-btn-row">
                        <a href="?play=${{m.id}}" target="_parent" class="btn-play">
                            <span>▶</span> Play
                        </a>
                        <a href="?info=${{m.id}}" target="_parent" class="btn-info">
                            <span>ⓘ</span> More Info
                        </a>
                    </div>
                </div>
                <div class="hero-maturity-badge">U/A 16+</div>
            `;
            slidesContainer.appendChild(slide);
            
            // Build indicator
            const ind = document.createElement('div');
            ind.className = 'indicator-item' + (idx === 0 ? ' active' : '');
            ind.id = 'ind-' + idx;
            ind.innerHTML = '<div class="indicator-fill" id="fill-' + idx + '"></div>';
            ind.addEventListener('click', () => {{
                goToSlide(idx);
            }});
            indicatorsContainer.appendChild(ind);
        }});
        
        function updateSlides(newIndex) {{
            const currentSlide = document.getElementById('slide-' + currentIndex);
            const nextSlide = document.getElementById('slide-' + newIndex);
            const currentInd = document.getElementById('ind-' + currentIndex);
            const nextInd = document.getElementById('ind-' + newIndex);
            
            if (currentSlide) currentSlide.classList.remove('active');
            if (nextSlide) nextSlide.classList.add('active');
            
            if (currentInd) {{
                currentInd.classList.remove('active');
                const fill = document.getElementById('fill-' + currentIndex);
                if (fill) fill.style.width = '0%';
            }}
            if (nextInd) {{
                nextInd.classList.add('active');
                const fill = document.getElementById('fill-' + newIndex);
                if (fill && !isPaused) {{
                    fill.style.width = '0%';
                    setTimeout(() => {{
                        fill.style.width = '100%';
                    }}, 20);
                }}
            }}
            currentIndex = newIndex;
        }}
        
        function nextSlide() {{
            const nextIdx = (currentIndex + 1) % movies.length;
            updateSlides(nextIdx);
        }}
        
        function prevSlide() {{
            const prevIdx = (currentIndex - 1 + movies.length) % movies.length;
            updateSlides(prevIdx);
        }}
        
        function goToSlide(idx) {{
            if (idx === currentIndex) return;
            resetTimer();
            updateSlides(idx);
        }}
        
        function startTimer() {{
            clearInterval(slideTimer);
            const fill = document.getElementById('fill-' + currentIndex);
            if (fill) fill.style.width = '100%';
            slideTimer = setInterval(() => {{
                nextSlide();
            }}, DURATION);
        }}
        
        function pauseTimer() {{
            isPaused = true;
            clearInterval(slideTimer);
            const fill = document.getElementById('fill-' + currentIndex);
            if (fill) {{
                const computedWidth = window.getComputedStyle(fill).width;
                fill.style.transition = 'none';
                fill.style.width = computedWidth;
            }}
        }}
        
        function resumeTimer() {{
            isPaused = false;
            const fill = document.getElementById('fill-' + currentIndex);
            if (fill) {{
                fill.style.transition = 'width 2s linear';
                fill.style.width = '100%';
            }}
            startTimer();
        }}
        
        function resetTimer() {{
            clearInterval(slideTimer);
            startTimer();
        }}
        
        // Control listeners
        document.getElementById('btnNext').addEventListener('click', (e) => {{
            e.stopPropagation();
            resetTimer();
            nextSlide();
        }});
        
        document.getElementById('btnPrev').addEventListener('click', (e) => {{
            e.stopPropagation();
            resetTimer();
            prevSlide();
        }});
        
        // Pause on Hover
        sliderWrapper.addEventListener('mouseenter', pauseTimer);
        sliderWrapper.addEventListener('mouseleave', resumeTimer);
        
        // Mobile Touch Swiping
        let touchStartX = 0;
        let touchEndX = 0;
        
        sliderWrapper.addEventListener('touchstart', (e) => {{
            touchStartX = e.changedTouches[0].screenX;
        }}, {{ passive: true }});
        
        sliderWrapper.addEventListener('touchend', (e) => {{
            touchEndX = e.changedTouches[0].screenX;
            const diffX = touchStartX - touchEndX;
            if (Math.abs(diffX) > 40) {{
                resetTimer();
                if (diffX > 0) {{
                    nextSlide();
                }} else {{
                    prevSlide();
                }}
            }}
        }}, {{ passive: true }});
        
        // Bridge cursor movement to parent document
        window.addEventListener('mousemove', (e) => {{
            try {{
                if (window.parent && window.frameElement) {{
                    const rect = window.frameElement.getBoundingClientRect();
                    const evt = new MouseEvent('mousemove', {{
                        clientX: e.clientX + rect.left,
                        clientY: e.clientY + rect.top,
                        bubbles: true
                    }});
                    window.parent.dispatchEvent(evt);
                }}
            }} catch(err) {{}}
        }}, {{ passive: true }});

        // Initial timer kickoff
        setTimeout(startTimer, 100);
    }})();
    </script>
    </body>
    </html>
    """

    st.components.v1.html(slider_html, height=485, scrolling=False)
