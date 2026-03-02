from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
INDEX_FILE = REPORTS_DIR / "index.html"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


def _discover_images(figures_dir: Path) -> list[Path]:
		if not figures_dir.exists():
				return []
		files = [
				path for path in figures_dir.rglob("*")
				if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
		]
		return sorted(files, key=lambda item: str(item.relative_to(REPORTS_DIR)).lower())


def _render_html(image_paths: list[Path]) -> str:
		generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

		if image_paths:
				cards = []
				for image_path in image_paths:
						relative_path = image_path.relative_to(REPORTS_DIR).as_posix()
						title = image_path.stem.replace("_", " ")
						cards.append(
								"""
								<article class=\"card\">
									<a href=\"{href}\" target=\"_blank\" rel=\"noopener noreferrer\">
										<img src=\"{src}\" alt=\"{alt}\" loading=\"lazy\" />
									</a>
									<div class=\"meta\">
										<h3>{title}</h3>
										<p>{path}</p>
									</div>
								</article>
								""".format(
										href=escape(relative_path, quote=True),
										src=escape(relative_path, quote=True),
										alt=escape(title, quote=True),
										title=escape(title),
										path=escape(relative_path),
								).strip()
						)
				gallery_html = "\n".join(cards)
		else:
				gallery_html = "<p class=\"empty\">У папці reports/figures ще немає зображень.</p>"

		return f"""<!doctype html>
<html lang=\"uk\">
	<head>
		<meta charset=\"utf-8\" />
		<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
		<title>Open Data AI Analytics — Reports</title>
		<style>
			:root {{
				color-scheme: light dark;
				--bg: #0b1020;
				--card: #141b34;
				--text: #e8ecff;
				--muted: #aab3d3;
				--accent: #8db2ff;
			}}
			@media (prefers-color-scheme: light) {{
				:root {{
					--bg: #f6f8ff;
					--card: #ffffff;
					--text: #1b2440;
					--muted: #4d5a86;
					--accent: #3159d1;
				}}
			}}
			* {{ box-sizing: border-box; }}
			body {{
				margin: 0;
				font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
				background: var(--bg);
				color: var(--text);
			}}
			.wrap {{
				max-width: 1100px;
				margin: 0 auto;
				padding: 24px;
			}}
			h1 {{ margin: 0 0 8px; }}
			.subtitle {{ color: var(--muted); margin: 0 0 20px; }}
			.gallery {{
				display: grid;
				grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
				gap: 16px;
			}}
			.card {{
				background: var(--card);
				border-radius: 12px;
				overflow: hidden;
				border: 1px solid color-mix(in srgb, var(--accent) 25%, transparent);
			}}
			.card img {{
				display: block;
				width: 100%;
				aspect-ratio: 16/10;
				object-fit: cover;
			}}
			.meta {{ padding: 12px; }}
			.meta h3 {{ margin: 0 0 6px; font-size: 16px; }}
			.meta p {{ margin: 0; color: var(--muted); font-size: 13px; word-break: break-word; }}
			.empty {{
				background: var(--card);
				border-radius: 12px;
				padding: 20px;
				color: var(--muted);
			}}
			.footer {{ margin-top: 18px; color: var(--muted); font-size: 12px; }}
		</style>
	</head>
	<body>
		<main class=\"wrap\">
			<h1>Звіти Open Data AI Analytics</h1>
			<p class=\"subtitle\">Автоматично згенерована галерея візуалізацій із reports/figures.</p>
			<section class=\"gallery\">{gallery_html}</section>
			<p class=\"footer\">Оновлено: {generated_at}</p>
		</main>
	</body>
</html>
"""


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    image_paths = _discover_images(FIGURES_DIR)
    html = _render_html(image_paths)
    INDEX_FILE.write_text(html, encoding="utf-8")
    print(f"Generated {INDEX_FILE} with {len(image_paths)} images")


if __name__ == "__main__":
	main()
