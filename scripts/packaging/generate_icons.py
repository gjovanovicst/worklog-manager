"""Generate Worklog Manager branding assets for installers."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

PROJECT_ROOT = Path(__file__).resolve().parents[2]
IMAGES_DIR = PROJECT_ROOT / "images"
OUTPUT_BASENAME = "worklog-manager-tray"

SIZES = [512, 256, 128, 64, 32, 16]


def _draw_watch_face(image: Image.Image, size: int) -> None:
    draw = ImageDraw.Draw(image)
    center = size / 2
    outer_radius = size * 0.48
    inner_radius = outer_radius * 0.82

    # Outer bezel with subtle shadow
    bezel_bounds = [
        center - outer_radius,
        center - outer_radius,
        center + outer_radius,
        center + outer_radius,
    ]
    draw.ellipse(bezel_bounds, fill=(26, 38, 56, 255))

    shadow = Image.new("RGBA", image.size)
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse(
        [
            center - outer_radius,
            center - outer_radius,
            center + outer_radius,
            center + outer_radius,
        ],
        fill=(0, 0, 0, 60),
    )
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(radius=max(1, size // 48))))

    # Inner face base color
    face_bounds = [
        center - inner_radius,
        center - inner_radius,
        center + inner_radius,
        center + inner_radius,
    ]
    draw.ellipse(face_bounds, fill=(62, 84, 118, 255))

    # Radial gradient for depth
    gradient = Image.new("RGBA", image.size, (0, 0, 0, 0))
    gradient_draw = ImageDraw.Draw(gradient)
    steps = int(max(8, inner_radius))
    for i in range(steps):
        ratio = i / steps
        shade = int(30 + 60 * (1 - ratio))
        alpha = int(90 * (1 - ratio))
        radius = inner_radius * (1 - ratio * 0.9)
        gradient_draw.ellipse(
            [
                center - radius,
                center - radius,
                center + radius,
                center + radius,
            ],
            outline=(shade, shade + 10, shade + 25, alpha),
            width=2,
        )
    gradient = gradient.filter(ImageFilter.GaussianBlur(radius=max(1, size // 32)))
    image.alpha_composite(gradient)

    # Face highlight sheen
    highlight = Image.new("RGBA", image.size, (0, 0, 0, 0))
    highlight_draw = ImageDraw.Draw(highlight)
    highlight_draw.ellipse(face_bounds, fill=(255, 255, 255, 40))
    highlight = highlight.filter(ImageFilter.GaussianBlur(radius=max(1, size // 28)))
    image.alpha_composite(highlight)

    # Trim highlight to create top-left sheen
    mask = Image.new("L", image.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.pieslice(
        [
            center - inner_radius,
            center - inner_radius,
            center + inner_radius,
            center + inner_radius,
        ],
        start=210,
        end=30,
        fill=255,
    )
    sheen = Image.new("RGBA", image.size, (0, 0, 0, 0))
    sheen_draw = ImageDraw.Draw(sheen)
    sheen_draw.pieslice(
        [
            center - inner_radius,
            center - inner_radius,
            center + inner_radius,
            center + inner_radius,
        ],
        start=210,
        end=30,
        fill=(120, 150, 210, 80),
    )
    sheen = sheen.filter(ImageFilter.GaussianBlur(radius=max(1, size // 28)))
    image.alpha_composite(Image.composite(sheen, Image.new("RGBA", sheen.size), mask))

    # Hour and minute hands (forming an "L" shape)
    hand_color = (230, 238, 255, 255)
    line_width = max(2, int(size // 32))
    hour_length = inner_radius * 0.55
    minute_length = inner_radius * 0.68

    # Hour hand - vertical
    draw.line(
        [
            (center, center - hour_length),
            (center, center + line_width * 0.4),
        ],
        fill=hand_color,
        width=line_width,
        joint="curve",
    )

    # Minute hand - horizontal towards right
    draw.line(
        [
            (center, center),
            (center + minute_length, center),
        ],
        fill=hand_color,
        width=line_width,
        joint="curve",
    )

    # Center cap
    cap_radius = max(2, int(size * 0.035))
    draw.ellipse(
        [
            center - cap_radius,
            center - cap_radius,
            center + cap_radius,
            center + cap_radius,
        ],
        fill=(214, 224, 242, 255),
    )


def _create_icon(size: int) -> Image.Image:
    base_color = (32, 49, 77)
    accent_color = (74, 105, 176)

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    _draw_watch_face(img, size)
    return img


def generate() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    base_icon = _create_icon(SIZES[0])
    png_path = IMAGES_DIR / f"{OUTPUT_BASENAME}.png"
    base_icon.save(png_path)

    ico_path = IMAGES_DIR / f"{OUTPUT_BASENAME}.ico"
    base_icon.save(ico_path, sizes=[(size, size) for size in SIZES])

    icns_path = IMAGES_DIR / f"{OUTPUT_BASENAME}.icns"
    try:
        base_icon.save(icns_path, format="ICNS", sizes=[(size, size) for size in SIZES])
    except ValueError:
        print(
            "Unable to write ICNS file with current Pillow build. "
            "Convert the generated PNGs with macOS iconutil instead."
        )

    for size in SIZES:
        icon = _create_icon(size)
        icon.save(IMAGES_DIR / f"{OUTPUT_BASENAME}-{size}.png")


if __name__ == "__main__":
    generate()
