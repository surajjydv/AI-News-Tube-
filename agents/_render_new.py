def render_tv_broadcast_frame(
    headline_text: str,
    news_photo_path: Optional[str],
    global_t: float = 0.0,
    category: str = "TOP STORIES",
    ticker_headlines: Optional[List[str]] = None,
    quick_cards: Optional[List[str]] = None
) -> Image.Image:
    """
    PREMIUM 3D Broadcast Frame — Full Redesign.
    Layout: 1280x720 output with:
    - Deep 3D studio background (hex grid + volumetric light beams + depth gradient)
    - News photo PIP in right panel with neon animated border
    - Top HUD bar (3D extruded) with LIVE badge, category, IST clock
    - 3D Lower-Third: beveled slab + angled badge + specular sweep + shadow extrusion
    - Animated neon accent rings around the frame
    - Dual-row ticker with gradient fade edges
    """
    W, H = 1280, 720
    is_brk = "break" in category.lower() or "brk" in category.lower()

    GOLD  = (255, 215, 0)
    RED   = (220, 30,  30)
    CYAN  = (0,   200, 255)
    DARK  = (5,   8,   22)
    PANEL = (8,   13,  32)

    live_pulse  = abs(math.sin(global_t * 3.5))
    fast_pulse  = abs(math.sin(global_t * 6.0))
    badge_cycle = int(global_t / 7.0) % 4

    if is_brk:
        badge_label  = "BREAKING"
        badge_color  = (220, 20,  20)
        accent_color = (255, 60,  60)
    else:
        opts = [
            ("TOP STORY",   (20,  110, 200), (60,  160, 255)),
            ("TRENDING",    (200, 80,  10),  (255, 140, 40)),
            ("EXCLUSIVE",   (130, 20,  180), (200, 80,  255)),
            ("LIVE UPDATE", (15,  150, 70),  (40,  220, 110)),
        ]
        badge_label, badge_color, accent_color = opts[badge_cycle]

    # ── LAYER 0: DEEP 3D STUDIO BACKGROUND ────────────────────────────────────
    frame = Image.new("RGB", (W, H), DARK)
    d_draw = ImageDraw.Draw(frame)

    # Depth gradient
    for y in range(H):
        fy = y / H
        r = max(0, int(4  + 12 * fy))
        g = max(0, int(6  + 8  * fy))
        b = max(0, int(20 + 28 * fy))
        d_draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Hex grid (animated)
    hex_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hex_layer)
    grid_size = 52
    wall_bottom = H - 200
    phase = (global_t * 18) % grid_size
    for gy in range(-grid_size, wall_bottom + grid_size, grid_size):
        for gx in range(-grid_size, W + grid_size, grid_size):
            ox = (grid_size // 2) if ((gy // grid_size) % 2) else 0
            cx, cy = gx + ox + int(phase * 0.5), gy + int(phase * 0.3)
            sz = 22
            dist_c = math.hypot(cx - W // 2, cy - wall_bottom // 2) / (W * 0.65)
            alpha = max(0, int((1.0 - dist_c) * 32))
            hd.polygon([(cx, cy-sz), (cx+sz, cy-sz//2), (cx+sz, cy+sz//2),
                        (cx, cy+sz), (cx-sz, cy+sz//2), (cx-sz, cy-sz//2)],
                       outline=(*CYAN, alpha), width=1)
    frame = Image.alpha_composite(frame.convert("RGBA"), hex_layer).convert("RGB")
    d_draw = ImageDraw.Draw(frame)

    # Volumetric light beams
    beam_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(beam_layer)
    for i, bx_frac in enumerate([0.15, 0.30, 0.50, 0.70, 0.85]):
        bx = int(W * bx_frac)
        flicker = abs(math.sin(global_t * 1.2 + i * 0.7))
        ba = int(18 * flicker)
        bd.polygon([(bx-5, 0), (bx+5, 0), (bx+120, wall_bottom), (bx-120, wall_bottom)],
                   fill=(180, 200, 255, ba))
    frame = Image.alpha_composite(frame.convert("RGBA"), beam_layer).convert("RGB")
    d_draw = ImageDraw.Draw(frame)

    # Studio desk / floor
    desk_y = H - 200
    desk_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(desk_layer)
    for y in range(desk_y, H):
        prog = (y - desk_y) / (H - desk_y)
        r = int(10 + 20 * prog); g = int(14 + 16 * prog); b = int(38 + 30 * prog)
        dd.line([(0, y), (W, y)], fill=(r, g, b, 220))
    dd.line([(0, desk_y), (W, desk_y)], fill=(*GOLD, 180), width=2)
    frame = Image.alpha_composite(frame.convert("RGBA"), desk_layer).convert("RGB")
    d_draw = ImageDraw.Draw(frame)

    # ── LAYER 1: NEON ANIMATED BORDER ─────────────────────────────────────────
    border_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    brd = ImageDraw.Draw(border_layer)
    glow_a = int(120 + 80 * live_pulse)
    for bw in [8, 5, 3, 1]:
        a = int(glow_a * bw / 10)
        brd.rectangle([(bw, bw), (W-bw, H-bw)], outline=(*accent_color, a), width=1)
    brd.rectangle([(3, 3), (W-3, H-3)], outline=(*GOLD, 200), width=2)
    cs = 24
    for cx2, cy2 in [(0, 0), (W-cs, 0), (0, H-cs), (W-cs, H-cs)]:
        brd.rectangle([(cx2, cy2), (cx2+cs, cy2+cs)],
                      fill=(*accent_color, int(180 * fast_pulse)))
    frame = Image.alpha_composite(frame.convert("RGBA"), border_layer).convert("RGB")
    d_draw = ImageDraw.Draw(frame)

    # ── LAYER 2: NEWS PHOTO PIP (right side) ──────────────────────────────────
    pip_x, pip_y = W // 2 + 20, 90
    pip_w, pip_h = W - pip_x - 20, desk_y - pip_y - 20
    pip_photo = None

    if news_photo_path and Path(news_photo_path).exists():
        try:
            pip_photo = Image.open(str(news_photo_path)).convert("RGB")
        except Exception:
            pass

    if pip_photo:
        pw, ph = pip_photo.size
        scale  = max(pip_w / pw, pip_h / ph)
        nw, nh = int(pw * scale), int(ph * scale)
        pip_photo = pip_photo.resize((nw, nh), Image.Resampling.LANCZOS)
        cx2 = (nw - pip_w) // 2; cy2 = (nh - pip_h) // 2
        pip_photo = pip_photo.crop((cx2, cy2, cx2 + pip_w, cy2 + pip_h))

        ov = Image.new("RGBA", (pip_w, pip_h), (0, 0, 0, 0))
        ov_d = ImageDraw.Draw(ov)
        for edge in range(30):
            ov_d.rectangle([(edge, edge), (pip_w-edge, pip_h-edge)],
                           outline=(0, 0, 0, int(160 * (1 - edge / 30))), width=1)
        pip_rgba = Image.alpha_composite(pip_photo.convert("RGBA"), ov)
        frame.paste(pip_rgba.convert("RGB"), (pip_x, pip_y))

        pf_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pfd = ImageDraw.Draw(pf_layer)
        bg2 = int(140 + 80 * fast_pulse)
        for gw in [6, 4, 2]:
            pfd.rectangle([(pip_x-gw, pip_y-gw), (pip_x+pip_w+gw, pip_y+pip_h+gw)],
                          outline=(*accent_color, int(bg2 * gw / 8)), width=1)
        pfd.rectangle([(pip_x-2, pip_y-2), (pip_x+pip_w+2, pip_y+pip_h+2)],
                      outline=(*GOLD, 230), width=2)
        s2 = 16
        for (ex, ey) in [(pip_x-2, pip_y-2)]:
            pfd.rectangle([(ex, ey), (ex+s2, ey+4)], fill=(*accent_color, 255))
            pfd.rectangle([(ex, ey), (ex+4, ey+s2)], fill=(*accent_color, 255))
        frame = Image.alpha_composite(frame.convert("RGBA"), pf_layer).convert("RGB")
        d_draw = ImageDraw.Draw(frame)
        d_draw.rectangle([(pip_x+4, pip_y+4), (pip_x+100, pip_y+26)], fill=(*RED, 220))
        d_draw.text((pip_x+10, pip_y+7), "LIVE REPORT",
                    fill=(255, 255, 255), font=_load_font(14, bold=True))

    # ── LAYER 3: TOP 3D HUD BAR ───────────────────────────────────────────────
    top_h = 72
    top_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(top_layer)
    for depth in range(6, 0, -1):
        td.rectangle([(0, depth), (W, top_h + depth)], fill=(0, 0, 0, int(180 * depth / 6)))
    td.rectangle([(0, 0), (W, top_h)], fill=(*PANEL, 245))
    td.rectangle([(0, 0), (W, 3)], fill=(*GOLD, 255))
    td.rectangle([(0, top_h-3), (W, top_h)], fill=(*accent_color, int(200 * live_pulse)))
    frame = Image.alpha_composite(frame.convert("RGBA"), top_layer).convert("RGB")
    d_draw = ImageDraw.Draw(frame)

    live_font = _load_font(20, bold=True)
    hud_font  = _load_font(17, bold=True)
    clk_font  = _load_font(22, bold=True)
    sm_font   = _load_font(14, bold=True)

    dot_r2 = int(7 + 4 * live_pulse)
    d_draw.ellipse([(20 - dot_r2//2, 36 - dot_r2//2),
                    (20 + dot_r2//2, 36 + dot_r2//2)], fill=RED)
    d_draw.ellipse([(16, 32), (24, 40)], fill=(255, 80, 80))
    d_draw.text((32, 10), "LIVE", fill=RED,  font=clk_font)
    d_draw.text((32, 42), CHANNEL_NAME.upper(), fill=GOLD, font=sm_font)
    d_draw.rectangle([(140, 10), (143, top_h-10)], fill=(*GOLD, 160))

    cat_str = category.upper()[:20]
    cat_bg_w = len(cat_str) * 11 + 22
    d_draw.rounded_rectangle([(152, 14), (152 + cat_bg_w, top_h-14)],
                              radius=6, fill=badge_color)
    d_draw.text((162, 22), cat_str, fill=(255, 255, 255), font=hud_font)

    now      = _dt.datetime.now()
    time_str = now.strftime("%H:%M:%S")
    date_str = now.strftime("%d %b %Y").upper()
    city_name, city_weather = INDIAN_CITIES_WEATHER[int(global_t / 3.0) % len(INDIAN_CITIES_WEATHER)]
    d_draw.text((W - 340, 10), time_str, fill=GOLD, font=clk_font)
    d_draw.text((W - 340, 42), f"{date_str}  |  {city_name} {city_weather}",
                fill=(200, 220, 255), font=sm_font)

    # Animated scan line on top bar
    scan_x = int(((global_t * 200) % (W + 100)) - 50)
    sc_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sc_d = ImageDraw.Draw(sc_layer)
    sc_d.polygon([(scan_x, 3), (scan_x+60, 3), (scan_x+40, top_h-3), (scan_x-20, top_h-3)],
                 fill=(*accent_color, int(40 * live_pulse)))
    frame = Image.alpha_composite(frame.convert("RGBA"), sc_layer).convert("RGB")
    d_draw = ImageDraw.Draw(frame)

    # ── LAYER 4: 3D EXTRUDED LOWER-THIRD HEADLINE PANEL ───────────────────────
    TICKER_H = 86
    BANNER_H = 145
    banner_y  = H - TICKER_H - BANNER_H
    banner_bot = H - TICKER_H
    pop_t = min(1.0, global_t / 0.5)
    ease_y = int(BANNER_H * (1.0 - math.sin(pop_t * math.pi / 2)))
    clip_y = banner_y + ease_y

    if clip_y < banner_bot:
        lt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lt)

        # 3D shadow extrusion
        for depth in range(10, 0, -1):
            ld.rectangle([(depth, clip_y + depth), (W-depth, banner_bot + depth)],
                         fill=(0, 0, 0, int(200 * depth / 10)))

        # Main glass slab
        ld.rectangle([(0, clip_y), (W, banner_bot)], fill=(6, 10, 26, 252))
        ld.rectangle([(0, clip_y), (W, clip_y + 4)], fill=(*GOLD, 255))
        ld.rectangle([(0, clip_y + 4), (W, clip_y + 9)], fill=(255, 255, 255, int(60 * pop_t)))
        ld.rectangle([(0, banner_bot - 3), (W, banner_bot)], fill=(*GOLD, 180))

        # Left badge parallelogram
        slant = 28
        badge_w = 290
        ld.polygon([(0, clip_y+4), (badge_w, clip_y+4),
                    (badge_w-slant, banner_bot-3), (0, banner_bot-3)],
                   fill=(*badge_color, 255))
        ld.polygon([(0, clip_y+4), (badge_w, clip_y+4),
                    (badge_w-slant, clip_y + BANNER_H//3), (0, clip_y + BANNER_H//3)],
                   fill=(255, 255, 255, int(45 * pop_t)))

        # Chevron divider
        ld.polygon([(badge_w-8, clip_y+4), (badge_w+36, clip_y+4),
                    (badge_w+8, banner_bot-3), (badge_w-slant-4, banner_bot-3)],
                   fill=(255, 255, 255, 230))

        # Pulsing live dot
        pr = int(8 + 5 * live_pulse)
        dbx, dby = 22, (clip_y + banner_bot) // 2
        ld.ellipse([(dbx-pr, dby-pr), (dbx+pr, dby+pr)],
                   fill=(255, 255, 255, int(160 * live_pulse)))
        ld.ellipse([(dbx-7, dby-7), (dbx+7, dby+7)], fill=(255, 255, 255, 255))

        # Specular sweep
        sw_phase = (global_t * 0.8) % 4.0
        if sw_phase < 1.0:
            swx = int(badge_w + 36 + sw_phase * (W - badge_w - 36))
            ld.polygon([(swx, clip_y+4), (swx+80, clip_y+4),
                        (swx+40, banner_bot-3), (swx-40, banner_bot-3)],
                       fill=(255, 255, 255, int(55 * (1 - sw_phase))))

        frame = Image.alpha_composite(frame.convert("RGBA"), lt).convert("RGB")
        d_draw = ImageDraw.Draw(frame)

        # Badge text
        b_mid   = (clip_y + banner_bot) // 2
        b_parts = badge_label.split(" ", 1)
        bf1 = _load_font(24, bold=True)
        bf2 = _load_font(20, bold=True)
        if len(b_parts) == 1:
            d_draw.text((38, b_mid - 14), b_parts[0], fill=(255, 255, 255), font=bf1)
        else:
            d_draw.text((38, b_mid - 28), b_parts[0], fill=(255, 255, 255), font=bf1)
            d_draw.text((38, b_mid + 2),  b_parts[1], fill=GOLD, font=bf2)

        # Headline text
        hclean = headline_text.split(" - ")[0].strip()
        tx     = badge_w + 50
        max_tw = W - tx - 20
        nchars = len(hclean)
        hsize  = 44 if nchars > 70 else (52 if nchars > 45 else 60)
        hfont  = _load_font(hsize, bold=True)

        words = hclean.split()
        lines_out, curr = [], ""
        for word in words:
            test = f"{curr} {word}".strip()
            try:
                tw2 = d_draw.textlength(test, font=hfont)
            except Exception:
                tw2 = len(test) * hsize * 0.58
            if tw2 > max_tw and curr:
                lines_out.append(curr)
                curr = word
            else:
                curr = test
        if curr:
            lines_out.append(curr)

        lines_out   = lines_out[:2]
        line_gap    = hsize + 8
        total_txt_h = len(lines_out) * line_gap
        start_y     = clip_y + (BANNER_H - total_txt_h) // 2 + ease_y // 2

        for i, line in enumerate(lines_out):
            ly = start_y + i * line_gap
            for sd in range(4, 0, -1):
                d_draw.text((tx + sd, ly + sd), line,
                            fill=(0, 0, 0, int(100 - sd * 20)), font=hfont)
            d_draw.text((tx, ly), line, fill=(255, 255, 255), font=hfont)
            d_draw.text((tx-1, ly-1), line, fill=(255, 255, 255, 60), font=hfont)

    # ── LAYER 5: DUAL TICKER BOTTOM BAR ───────────────────────────────────────
    tick_y  = H - TICKER_H
    tick_mid = tick_y + TICKER_H // 2

    tk_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    tkd = ImageDraw.Draw(tk_layer)
    tkd.rectangle([(0, tick_y), (W, H)], fill=(*PANEL, 255))
    tkd.rectangle([(0, tick_y), (W, tick_y+3)], fill=(*GOLD, 255))
    tkd.rectangle([(0, tick_mid-1), (W-140, tick_mid+1)],
                  fill=(*accent_color, int(160 * fast_pulse)))
    frame = Image.alpha_composite(frame.convert("RGBA"), tk_layer).convert("RGB")
    d_draw = ImageDraw.Draw(frame)

    tfont = _load_font(18, bold=True)
    ctick = ("  |  ".join(ticker_headlines)
             if ticker_headlines else "AI-NewsTube 24/7 Live — Real-Time News Active")
    stxt  = f"  {ctick}  "
    try:
        tw3 = max(int(d_draw.textlength(stxt, font=tfont)), 1)
    except Exception:
        tw3 = max(len(stxt) * 11, 1)

    soff = int(global_t * 140) % max(tw3, 1)
    tick_canvas = Image.new("RGB", (W - 140, TICKER_H // 2 - 4), PANEL)
    tc_draw = ImageDraw.Draw(tick_canvas)
    x1t = -soff
    while x1t < W - 140:
        tc_draw.text((x1t, 6), stxt, fill=(255, 255, 255), font=tfont)
        x1t += tw3

    fade_w = 40
    for fx in range(fade_w):
        a3 = int(255 * (1 - fx / fade_w))
        tc_draw.line([(fx, 0), (fx, TICKER_H)], fill=(*PANEL, a3))
        tc_draw.line([(W - 140 - fx, 0), (W - 140 - fx, TICKER_H)], fill=(*PANEL, a3))
    frame.paste(tick_canvas, (0, tick_y + 4))
    d_draw = ImageDraw.Draw(frame)

    mkt_str = (f"SENSEX 81,420  +340  |  NIFTY 24,850  +95  |  "
               f"GOLD 72,500  |  USD/INR 83.42  |  {city_name}: {city_weather}")
    d_draw.text((12, tick_mid + 6), mkt_str, fill=GOLD, font=_load_font(15, bold=True))

    # Bottom-right category pill
    pill_x = W - 138
    d_draw.rectangle([(pill_x, tick_y), (W, H)], fill=badge_color)
    d_draw.rectangle([(pill_x, tick_y), (pill_x+3, H)], fill=(*GOLD, 255))
    d_draw.text((pill_x+12, tick_y+18), category.upper()[:8],
                fill=(255, 255, 255), font=_load_font(18, bold=True))
    d_draw.text((pill_x+12, tick_y+48), "NEWS", fill=GOLD, font=_load_font(14, bold=True))

    if frame.size != (W, H):
        frame = frame.resize((W, H), Image.Resampling.BILINEAR)

    return frame

