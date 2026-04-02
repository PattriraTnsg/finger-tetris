# """
# hud.py
# ──────
# Heads-Up Display rendered with Pygame onto a sidebar Surface.
# Shows score, level, lines cleared, next piece preview, FPS,
# and an optional debug panel for gesture/finger data.
# """

from __future__ import annotations

import pygame
from typing import Optional, Tuple, Dict, Any

# ── palette (same dark theme as game_renderer) ───────────────────────────────
C = {
    "bg":          (15,  15,  25),   
    "panel":       (40,  40,  60),   
    "border":      (100, 100, 150),  
    "accent":      (0,   255, 200),  
    "text":        (255, 255, 255),  
    "text_dim":    (180, 180, 200),  
    "label":       (180, 180, 220),  
    "warning":     (255, 150,   0),
    "danger":      (255,  80,  80),
    # tetromino colours for next-piece preview
    "I": (0,   240, 240),
    "O": (240, 240,   0),
    "T": (160,   0, 240),
    "S": (0,   240,   0),
    "Z": (240,   0,   0),
    "J": (0,    0,  240),
    "L": (240, 160,   0),
}

PIECE_COLOUR_MAP = {
    1: "I", 2: "O", 3: "T", 4: "S", 5: "Z", 6: "J", 7: "L",
}


def _load_font(size: int, bold: bool = False) -> pygame.font.Font:
    try:
        name = "couriernew" if not bold else "couriernewbold"
        return pygame.font.SysFont(name, size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


class HUD:
    # """
    # Sidebar HUD drawn with Pygame.

    # Parameters
    # ----------
    # surface : pygame.Surface  – sidebar surface (NOT the full window)
    # width   : int             – width of the sidebar in pixels
    # height  : int             – height of the sidebar in pixels
    # """

    # Layout constants
    MARGIN   = 14
    CELL_PX  = 22          # cell size used in next-piece preview

    def __init__(
        self,
        surface: pygame.Surface,
        width:  int = 180,
        height: int = 600,
    ) -> None:
        self.surface = surface
        self.width   = width
        self.height  = height

        # fonts
        self.font_title  = _load_font(16, bold=True)
        self.font_value  = _load_font(32, bold=True)
        self.font_label  = _load_font(13)
        self.font_debug  = _load_font(12)

        # animated score counter (smoothly increments)
        self._display_score = 0

    # ── public API ────────────────────────────────────────────────────────────

    def draw(
        self,
        score:       int,
        level:       int,
        lines:       int,
        fps:         float,
        next_piece,                    # piece.Piece or None
        game_over:   bool = False,
        paused:      bool = False,
        debug_info:  Optional[Dict[str, Any]] = None,
    ) -> None:
        """Render the full HUD onto self.surface."""
        self.surface.fill(C["bg"])

        # smooth score animation
        diff = score - self._display_score
        self._display_score += max(1, diff // 4) if diff > 0 else diff

        y = self.MARGIN

        y = self._draw_section("SCORE", str(self._display_score), y,
                               value_colour=C["accent"])
        y = self._draw_section("LEVEL", str(level), y)
        y = self._draw_section("LINES", str(lines), y)

        y += 8
        y = self._draw_next_piece(next_piece, y)

        y += 8
        y = self._draw_fps_bar(fps, y)

        y += 8
        y = self._draw_controls(y)

        if debug_info:
            y += 8
            y = self._draw_debug_panel(debug_info, y)

        if game_over:
            self._draw_overlay_text("GAME OVER", C["danger"],
                                    subtitle="Press R to restart")
        elif paused:
            self._draw_overlay_text("PAUSED", C["warning"],
                                    subtitle="Press P to resume")

    # ── private helpers ───────────────────────────────────────────────────────

    def _draw_section(
        self,
        label: str,
        value: str,
        y: int,
        value_colour: Tuple[int, int, int] = None,
    ) -> int:
        m  = self.MARGIN
        vc = value_colour or C["text"]

        # divider line
        pygame.draw.line(
            self.surface, C["border"],
            (m, y), (self.width - m, y), 1,
        )
        y += 6

        lbl_surf = self.font_label.render(label, True, C["label"])
        self.surface.blit(lbl_surf, (m, y))
        y += lbl_surf.get_height() + 2

        val_surf = self.font_value.render(value, True, vc)
        self.surface.blit(val_surf, (m, y))
        y += val_surf.get_height() + 10
        return y

    def _draw_next_piece(self, piece, y: int) -> int:
        m = self.MARGIN
        pygame.draw.line(
            self.surface, C["border"], (m, y), (self.width - m, y), 1,
        )
        y += 6

        lbl = self.font_label.render("NEXT", True, C["label"])
        self.surface.blit(lbl, (m, y))
        y += lbl.get_height() + 6

        # 4×2 preview box
        preview_w = 4 * self.CELL_PX
        preview_h = 3 * self.CELL_PX
        box_rect  = pygame.Rect(m, y, preview_w, preview_h)
        pygame.draw.rect(self.surface, C["panel"], box_rect)
        pygame.draw.rect(self.surface, C["border"], box_rect, 1)

        if piece is not None:
            colour_key = PIECE_COLOUR_MAP.get(piece.color_id, "I")
            colour     = C[colour_key]
            cells      = piece.get_cells()
            # normalise cells so they start at (0,0)
            min_r = min(r for r, c in cells)
            min_c = min(c for r, c in cells)

            for r, c in cells:
                nr = r - min_r
                nc = c - min_c
                px = m + nc * self.CELL_PX + 2
                py = y + nr * self.CELL_PX + 2
                sz = self.CELL_PX - 4
                pygame.draw.rect(self.surface, colour,
                                 (px, py, sz, sz))

        y += preview_h + 10
        return y

    def _draw_fps_bar(self, fps: float, y: int) -> int:
        m = self.MARGIN
        pygame.draw.line(
            self.surface, C["border"], (m, y), (self.width - m, y), 1,
        )
        y += 6

        colour = (
            C["accent"]  if fps >= 30 else
            C["warning"] if fps >= 15 else
            C["danger"]
        )

        lbl = self.font_label.render("FPS", True, C["label"])
        self.surface.blit(lbl, (m, y))

        val = self.font_label.render(f"{fps:.0f}", True, colour)
        self.surface.blit(val, (self.width - m - val.get_width(), y))
        y += lbl.get_height() + 4

        # bar
        bar_w  = self.width - m * 2
        bar_h  = 6
        filled = int(bar_w * min(fps / 60, 1.0))
        pygame.draw.rect(self.surface, C["panel"],  (m, y, bar_w, bar_h))
        pygame.draw.rect(self.surface, colour,      (m, y, filled, bar_h))
        pygame.draw.rect(self.surface, C["border"], (m, y, bar_w, bar_h), 1)
        y += bar_h + 10
        return y

    def _draw_debug_panel(self, info: Dict[str, Any], y: int) -> int:
        m = self.MARGIN
        pygame.draw.line(
            self.surface, C["border"], (m, y), (self.width - m, y), 1,
        )
        y += 6

        hdr = self.font_label.render("DEBUG", True, C["text_dim"])
        self.surface.blit(hdr, (m, y))
        y += hdr.get_height() + 4

        for key, val in info.items():
            line = f"{key}: {val}"
            surf = self.font_debug.render(line, True, C["text_dim"])
            if surf.get_width() > self.width - m * 2:
                line = line[: max(1, len(line) - 3)] + "…"
                surf = self.font_debug.render(line, True, C["text_dim"])
            self.surface.blit(surf, (m, y))
            y += surf.get_height() + 2

        return y + 4

    def _draw_controls(self, y: int) -> int:
        m = self.MARGIN
        pygame.draw.line(
            self.surface, C["border"], (m, y), (self.width - m, y), 1,
        )
        y += 6

        hdr = self.font_label.render("CONTROLS", True, C["label"])
        self.surface.blit(hdr, (m, y))
        y += hdr.get_height() + 5

        controls = [
            ("[P]",     "Pause / Resume"),
            ("[R]",     "Restart"),
            ("[Q]",     "Quit"),
            ("[←][→]",  "Move"),
            ("[↑]",     "Rotate"),
            ("[↓]",     "Soft drop"),
            ("[Space]", "Hard drop"),
        ]

        for key, desc in controls:
            key_surf  = self.font_debug.render(key,  True, C["accent"])
            desc_surf = self.font_debug.render(desc, True, C["text_dim"])
            self.surface.blit(key_surf,  (m, y))
            self.surface.blit(desc_surf, (m + 48, y))
            y += key_surf.get_height() + 3

        return y + 4

    def _draw_overlay_text(
        self,
        text:     str,
        colour:   Tuple[int, int, int],
        subtitle: str = "",
    ) -> None:
        font      = _load_font(20, bold=True)
        sub_font  = _load_font(11)
        surf      = font.render(text, True, colour)
        cx        = (self.width - surf.get_width())  // 2
        cy        = (self.height - surf.get_height()) // 2

        backing_h = surf.get_height() + (sub_font.get_height() + 6 if subtitle else 0) + 24
        backing   = pygame.Surface((self.width, backing_h))
        backing.set_alpha(200)
        backing.fill((5, 5, 15))
        self.surface.blit(backing, (0, cy - 12))
        self.surface.blit(surf, (cx, cy))

        if subtitle:
            sub_surf = sub_font.render(subtitle, True, C["text_dim"])
            scx = (self.width - sub_surf.get_width()) // 2
            self.surface.blit(sub_surf, (scx, cy + surf.get_height() + 6))