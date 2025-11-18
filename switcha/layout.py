from typing import NamedTuple

from fans.bunch import bunch


class Rect(NamedTuple):
    
    left: float
    top: float
    width: float
    height: float


def layout_grids(
        n_rows,
        n_cols,
        screen_width,
        screen_height,
        *,
        screen_margin_ratio=0.1,
        gap=30,
        title_height=40,
):
    aspect_ratio = screen_width / screen_height

    # first calculate grid width and derive grid height
    grid_width = (
        screen_width * (1.0 - 2 * screen_margin_ratio)
        - (n_cols + 1) * gap
    ) / n_cols
    grid_height = grid_width / aspect_ratio + title_height

    panel_height = grid_height * n_rows + gap * (n_rows + 1)
    if panel_height > screen_height * (1.0 - 2 * screen_margin_ratio):
        # re-calculate grid height first and derive grid width
        grid_height = (
            screen_height * (1.0 - 2 * screen_margin_ratio)
            - (n_rows + 1) * gap
        ) / n_rows
        grid_width = (grid_height - title_height) * aspect_ratio

    # calculate panel
    panel_width = grid_width * n_cols + gap * (n_cols + 1)
    panel_height = grid_height * n_rows + gap * (n_rows + 1)

    screen_margin_horz = (screen_width - panel_width) / 2
    screen_margin_vert = (screen_height - panel_height) / 2

    panel_rect = Rect(screen_margin_horz, screen_margin_vert, panel_width, panel_height)

    # calculate grids
    grids = []
    for i_row in range(n_rows):
        for i_col in range(n_cols):
            x = panel_rect.left + gap + (grid_width + gap) * i_col
            y = panel_rect.top + gap + (grid_height + gap) * i_row

            grid = Rect(x, y, grid_width, grid_height)
            thumb = Rect(x, y, grid_width, grid_height - title_height)
            icon = Rect(x, y + grid_height - title_height, title_height, title_height)
            hotkey = Rect(icon.left + grid_width - title_height, icon.top, title_height, title_height)
            title = Rect(icon.left + icon.width, icon.top, grid_width - icon.width - hotkey.width, title_height)

            grids.append(bunch({
                'grid_rect': grid,
                'thumb_rect': thumb,
                'title_rect': title,
                'icon_rect': icon,
                'hotkey_rect': hotkey,
            }))

    return bunch({
        'screen_width': screen_width,
        'screen_height': screen_height,
        'panel_rect': panel_rect,
        'grids': grids,
    })


if __name__ == '__main__':
    import json
    from pathlib import Path
    layout = layout_grids(3, 4, 1920 / 2, 1080 / 2, title_height=36 / 2)
    with Path('~/webtmp/src/data.json').expanduser().open('w') as f:
        json.dump(layout, f)
