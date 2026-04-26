from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse
import sqlite3
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, String
import tempfile

router = APIRouter()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "mediahub.db")

# Регистрируем шрифт с поддержкой кириллицы
def register_cyrillic_font():
    try:
        # Сначала проверяем локальный шрифт в проекте
        project_font = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'DejaVuSans.ttf')
        if os.path.exists(project_font):
            pdfmetrics.registerFont(TTFont('Cyrillic', project_font))
            return 'Cyrillic'

        # Пытаемся использовать системный шрифт Arial
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/System/Library/Fonts/Arial.ttf',
            'C:\\Windows\\Fonts\\arial.ttf',
        ]

        font_path = None
        for path in font_paths:
            if os.path.exists(path):
                font_path = path
                break

        if font_path:
            pdfmetrics.registerFont(TTFont('Cyrillic', font_path))
            return 'Cyrillic'
        else:
            # Если шрифт не найден, используем стандартный
            return 'Helvetica'
    except Exception as e:
        print(f"Error registering font: {e}")
        return 'Helvetica'

CYRILLIC_FONT = register_cyrillic_font()

BRAND = {
    "indigo": colors.HexColor("#6366f1"),
    "violet": colors.HexColor("#a855f7"),
    "emerald": colors.HexColor("#10b981"),
    "amber": colors.HexColor("#f59e0b"),
    "blue": colors.HexColor("#3b82f6"),
    "slate900": colors.HexColor("#0f172a"),
    "slate700": colors.HexColor("#334155"),
    "slate500": colors.HexColor("#64748b"),
    "slate200": colors.HexColor("#e2e8f0"),
    "slate100": colors.HexColor("#f1f5f9"),
    "white": colors.white,
}

def _draw_brand_chrome(canvas, doc, title: str):
    """Header/footer for every page (keeps reports visually consistent)."""
    canvas.saveState()

    w, h = doc.pagesize
    header_h = 0.55 * inch
    canvas.setFillColor(BRAND["slate900"])
    canvas.rect(0, h - header_h, w, header_h, stroke=0, fill=1)

    canvas.setFillColor(BRAND["white"])
    canvas.setFont(CYRILLIC_FONT, 12)
    canvas.drawString(0.65 * inch, h - 0.36 * inch, "MediaHub")

    canvas.setFillColor(colors.HexColor("#c7d2fe"))  # light indigo
    canvas.setFont(CYRILLIC_FONT, 10)
    canvas.drawRightString(w - 0.65 * inch, h - 0.35 * inch, title)

    canvas.setStrokeColor(BRAND["slate200"])
    canvas.setLineWidth(1)
    canvas.line(0.65 * inch, 0.65 * inch, w - 0.65 * inch, 0.65 * inch)

    canvas.setFillColor(BRAND["slate500"])
    canvas.setFont(CYRILLIC_FONT, 9)
    canvas.drawString(0.65 * inch, 0.42 * inch, f"Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    canvas.drawRightString(w - 0.65 * inch, 0.42 * inch, f"Страница {canvas.getPageNumber()}")

    canvas.restoreState()

def _kpi_cards(items, col_widths, title_style, value_style):
    """
    KPI cards row as a 1-row table: each cell looks like a card.
    items: list of dicts {title, value, accent_color}
    """
    cells = []
    for it in items:
        accent = it.get("accent_color", BRAND["indigo"])
        cells.append(
            Table(
                [
                    [Paragraph(it["title"], title_style)],
                    [Paragraph(it["value"], value_style)],
                ],
                colWidths=[col_widths],
            )
        )
        cells[-1].setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), BRAND["slate100"]),
                    ("LINEBEFORE", (0, 0), (0, -1), 6, accent),
                    ("BOX", (0, 0), (-1, -1), 1, BRAND["slate200"]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

    wrapper = Table([cells], colWidths=[col_widths] * len(cells))
    wrapper.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return wrapper

def _bar_chart(title: str, pairs, width=6.6 * inch, bar_h=12, gap=8, palette=None, title_style=None):
    """
    Simple horizontal bar chart using vector shapes (PDF-friendly).
    pairs: list[(label:str, value:int)]
    """
    palette = palette or [BRAND["indigo"], BRAND["violet"], BRAND["emerald"], BRAND["amber"], BRAND["blue"]]
    max_v = max([v for _, v in pairs], default=0)
    left = 140
    right_pad = 28
    top_pad = 22
    height = top_pad + len(pairs) * (bar_h + gap) + 6
    d = Drawing(width, height)

    # Title
    d.add(String(0, height - 14, title, fontName=CYRILLIC_FONT, fontSize=11, fillColor=BRAND["slate700"]))

    track_w = max(10, width - left - right_pad)
    y = height - top_pad - bar_h
    for i, (label, v) in enumerate(pairs):
        color = palette[i % len(palette)]
        d.add(String(0, y + 2, label, fontName=CYRILLIC_FONT, fontSize=9, fillColor=BRAND["slate700"]))

        # Track
        d.add(Rect(left, y, track_w, bar_h, strokeWidth=0, fillColor=BRAND["slate200"]))

        # Bar
        fill_w = 0 if max_v == 0 else (track_w * (v / max_v))
        d.add(Rect(left, y, fill_w, bar_h, strokeWidth=0, fillColor=color))

        d.add(
            String(
                left + track_w + 6,
                y + 2,
                str(v),
                fontName=CYRILLIC_FONT,
                fontSize=9,
                fillColor=BRAND["slate500"],
            )
        )
        y -= (bar_h + gap)

    return d

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/api/admin/report")
async def generate_report(request: Request):
    """Генерация PDF отчета со статистикой"""
    # Проверяем что пользователь админ
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    conn = get_db_connection()
    try:
        user = conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user or user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")

        # Собираем статистику
        stats = {}

        # Статистика пользователей
        stats['users'] = {
            'total': conn.execute("SELECT COUNT(*) as count FROM users").fetchone()["count"],
            'active': conn.execute("SELECT COUNT(*) as count FROM users WHERE status = 'active'").fetchone()["count"],
            'pending': conn.execute("SELECT COUNT(*) as count FROM users WHERE status = 'pending'").fetchone()["count"],
            'by_role': {}
        }

        for role in ['admin', 'smm', 'editor', 'observer', 'volunteer']:
            count = conn.execute("SELECT COUNT(*) as count FROM users WHERE role = ?", (role,)).fetchone()["count"]
            stats['users']['by_role'][role] = count

        # Статистика постов
        stats['posts'] = {
            'total': conn.execute("SELECT COUNT(*) as count FROM posts").fetchone()["count"],
            'published': conn.execute("SELECT COUNT(*) as count FROM posts WHERE status = 'published'").fetchone()["count"],
            'pending': conn.execute("SELECT COUNT(*) as count FROM posts WHERE status = 'pending_review'").fetchone()["count"],
            'draft': conn.execute("SELECT COUNT(*) as count FROM posts WHERE status = 'draft'").fetchone()["count"],
            'scheduled': conn.execute("SELECT COUNT(*) as count FROM posts WHERE status = 'scheduled'").fetchone()["count"]
        }

        # Топ пользователей
        stats['top_users'] = conn.execute("""
            SELECT u.username, u.role, COUNT(p.id) as post_count
            FROM users u
            LEFT JOIN posts p ON u.id = p.author_id
            GROUP BY u.id
            ORDER BY post_count DESC
            LIMIT 10
        """).fetchall()

        # Последние пользователи
        stats['recent_users'] = conn.execute("""
            SELECT username, email, role, status, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT 10
        """).fetchall()

    finally:
        conn.close()

    # Создаем PDF
    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(tempfile.gettempdir(), filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=1.15 * inch,
        bottomMargin=0.9 * inch,
    )
    story = []
    styles = getSampleStyleSheet()

    # Создаем стили с кириллическим шрифтом
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=CYRILLIC_FONT,
        fontSize=24,
        textColor=colors.HexColor('#6366f1'),
        alignment=TA_CENTER,
        spaceAfter=30
    )

    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontName=CYRILLIC_FONT,
        fontSize=18,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12
    )

    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontName=CYRILLIC_FONT,
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=CYRILLIC_FONT,
        fontSize=10,
        textColor=BRAND["slate500"]
    )

    kpi_title_style = ParagraphStyle(
        "KpiTitle",
        parent=normal_style,
        fontName=CYRILLIC_FONT,
        fontSize=9,
        textColor=BRAND["slate500"],
        spaceAfter=2,
    )
    kpi_value_style = ParagraphStyle(
        "KpiValue",
        parent=styles["Heading2"],
        fontName=CYRILLIC_FONT,
        fontSize=18,
        textColor=BRAND["slate900"],
        spaceAfter=0,
    )

    # Заголовок
    story.append(Paragraph("Отчет о деятельности платформы Медиахаб", title_style))
    story.append(Spacer(1, 12))

    # Дата генерации
    date_style = ParagraphStyle(
        'DateStyle',
        parent=normal_style,
        alignment=TA_CENTER
    )
    story.append(Paragraph(f"Дата генерации: {datetime.now().strftime('%d.%m.%Y %H:%M')}", date_style))
    story.append(Spacer(1, 20))

    # KPI карточки
    kpis = [
        {"title": "Всего пользователей", "value": str(stats["users"]["total"]), "accent_color": BRAND["indigo"]},
        {"title": "Активных пользователей", "value": str(stats["users"]["active"]), "accent_color": BRAND["emerald"]},
        {"title": "Всего постов", "value": str(stats["posts"]["total"]), "accent_color": BRAND["blue"]},
    ]
    story.append(_kpi_cards(kpis, col_widths=1.65 * inch, title_style=kpi_title_style, value_style=kpi_value_style))
    story.append(Spacer(1, 16))

    # Секция статистики пользователей
    story.append(Paragraph("Статистика пользователей", heading2_style))
    story.append(Spacer(1, 12))

    user_data = [
        ['Показатель', 'Значение'],
        ['Всего пользователей', str(stats['users']['total'])],
        ['Активных', str(stats['users']['active'])],
        ['Ожидают подтверждения', str(stats['users']['pending'])],
    ]

    user_table = Table(user_data, colWidths=[3*inch, 2*inch])
    user_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND["indigo"]),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), CYRILLIC_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), BRAND["slate100"]),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BRAND["slate100"], colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.75, BRAND["slate200"]),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(user_table)
    story.append(Spacer(1, 20))

    # Распределение по ролям
    story.append(Paragraph("Распределение по ролям", heading3_style))
    story.append(Spacer(1, 12))

    role_data = [['Роль', 'Количество']]
    role_names = {
        'admin': 'Администраторы',
        'smm': 'SMM специалисты',
        'editor': 'Редакторы',
        'observer': 'Наблюдатели',
        'volunteer': 'Волонтеры'
    }

    for role, count in stats['users']['by_role'].items():
        role_data.append([role_names.get(role, role), str(count)])

    role_table = Table(role_data, colWidths=[3*inch, 2*inch])
    role_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND["violet"]),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), CYRILLIC_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), BRAND["slate100"]),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BRAND["slate100"], colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.75, BRAND["slate200"]),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(role_table)
    story.append(Spacer(1, 10))
    role_pairs = [(role_names.get(r, r), int(c)) for r, c in stats["users"]["by_role"].items()]
    story.append(_bar_chart("Инфографика: роли пользователей", role_pairs, palette=[BRAND["violet"], BRAND["indigo"], BRAND["blue"], BRAND["emerald"], BRAND["amber"]]))
    story.append(Spacer(1, 20))

    # Статистика постов
    story.append(Paragraph("Статистика постов", heading2_style))
    story.append(Spacer(1, 12))

    post_data = [
        ['Статус', 'Количество'],
        ['Всего постов', str(stats['posts']['total'])],
        ['Опубликованных', str(stats['posts']['published'])],
        ['На модерации', str(stats['posts']['pending'])],
        ['Черновиков', str(stats['posts']['draft'])],
        ['Запланированных', str(stats['posts']['scheduled'])],
    ]

    post_table = Table(post_data, colWidths=[3*inch, 2*inch])
    post_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND["emerald"]),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), CYRILLIC_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), BRAND["slate100"]),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BRAND["slate100"], colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.75, BRAND["slate200"]),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(post_table)
    story.append(Spacer(1, 10))
    post_pairs = [
        ("Опубликовано", int(stats["posts"]["published"])),
        ("На модерации", int(stats["posts"]["pending"])),
        ("Черновики", int(stats["posts"]["draft"])),
        ("Запланировано", int(stats["posts"]["scheduled"])),
    ]
    story.append(_bar_chart("Инфографика: статусы постов", post_pairs, palette=[BRAND["emerald"], BRAND["amber"], BRAND["violet"], BRAND["blue"]]))
    story.append(Spacer(1, 20))

    # Топ авторов
    story.append(Paragraph("Топ авторов", heading2_style))
    story.append(Spacer(1, 12))

    top_data = [['#', 'Пользователь', 'Роль', 'Публикаций']]
    for i, user in enumerate(stats['top_users'], 1):
        top_data.append([
            str(i),
            user['username'],
            user['role'],
            str(user['post_count'])
        ])

    top_table = Table(top_data, colWidths=[0.5*inch, 2.5*inch, 1.5*inch, 1*inch])
    top_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND["amber"]),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), CYRILLIC_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), BRAND["slate100"]),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BRAND["slate100"], colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.75, BRAND["slate200"]),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(top_table)

    # Генерируем PDF
    report_title = "Админ-отчет"
    doc.build(
        story,
        onFirstPage=lambda c, d: _draw_brand_chrome(c, d, report_title),
        onLaterPages=lambda c, d: _draw_brand_chrome(c, d, report_title),
    )

    # Отправляем файл и удаляем его после отправки
    return FileResponse(
        filepath,
        media_type="application/pdf",
        filename=filename,
        background=None
    )

@router.get("/api/editor/report")
async def generate_editor_report(request: Request):
    """Генерация PDF отчета со статистикой постов для SMM-менеджера"""
    # Проверяем что пользователь авторизован
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    conn = get_db_connection()
    try:
        user = conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user or user["role"] not in ["smm", "editor", "admin"]:
            raise HTTPException(status_code=403, detail="SMM/Editor access required")

        # Собираем статистику постов
        stats = {}

        # Общая статистика постов
        stats['posts'] = {
            'total': conn.execute("SELECT COUNT(*) as count FROM posts").fetchone()["count"],
            'published': conn.execute("SELECT COUNT(*) as count FROM posts WHERE status = 'published'").fetchone()["count"],
            'pending': conn.execute("SELECT COUNT(*) as count FROM posts WHERE status = 'pending_review'").fetchone()["count"],
            'draft': conn.execute("SELECT COUNT(*) as count FROM posts WHERE status = 'draft'").fetchone()["count"],
            'scheduled': conn.execute("SELECT COUNT(*) as count FROM posts WHERE status = 'scheduled'").fetchone()["count"]
        }

        # Статистика по авторам
        stats['authors'] = conn.execute("""
            SELECT u.username, u.role, COUNT(p.id) as post_count,
                   SUM(CASE WHEN p.status = 'published' THEN 1 ELSE 0 END) as published_count,
                   SUM(CASE WHEN p.status = 'pending_review' THEN 1 ELSE 0 END) as pending_count
            FROM users u
            LEFT JOIN posts p ON u.id = p.author_id
            GROUP BY u.id
            ORDER BY post_count DESC
        """).fetchall()

        # Последние посты
        stats['recent_posts'] = conn.execute("""
            SELECT p.id, p.title, p.status, u.username, p.created_at
            FROM posts p
            JOIN users u ON p.author_id = u.id
            ORDER BY p.created_at DESC
            LIMIT 10
        """).fetchall()

    finally:
        conn.close()

    # Создаем PDF
    filename = f"posts_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(tempfile.gettempdir(), filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=1.15 * inch,
        bottomMargin=0.9 * inch,
    )
    story = []
    styles = getSampleStyleSheet()

    # Создаем стили с кириллическим шрифтом
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=CYRILLIC_FONT,
        fontSize=24,
        textColor=colors.HexColor('#6366f1'),
        alignment=TA_CENTER,
        spaceAfter=30
    )

    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontName=CYRILLIC_FONT,
        fontSize=18,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12
    )

    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontName=CYRILLIC_FONT,
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=CYRILLIC_FONT,
        fontSize=10,
        textColor=BRAND["slate500"]
    )

    kpi_title_style = ParagraphStyle(
        "KpiTitle",
        parent=normal_style,
        fontName=CYRILLIC_FONT,
        fontSize=9,
        textColor=BRAND["slate500"],
        spaceAfter=2,
    )
    kpi_value_style = ParagraphStyle(
        "KpiValue",
        parent=styles["Heading2"],
        fontName=CYRILLIC_FONT,
        fontSize=18,
        textColor=BRAND["slate900"],
        spaceAfter=0,
    )

    # Заголовок
    story.append(Paragraph("Отчет о постах платформы Медиахаб", title_style))
    story.append(Spacer(1, 12))

    # Дата генерации
    date_style = ParagraphStyle(
        'DateStyle',
        parent=normal_style,
        alignment=TA_CENTER
    )
    story.append(Paragraph(f"Дата генерации: {datetime.now().strftime('%d.%m.%Y %H:%M')}", date_style))
    story.append(Spacer(1, 20))

    # KPI карточки
    kpis = [
        {"title": "Всего постов", "value": str(stats["posts"]["total"]), "accent_color": BRAND["blue"]},
        {"title": "Опубликовано", "value": str(stats["posts"]["published"]), "accent_color": BRAND["emerald"]},
        {"title": "На модерации", "value": str(stats["posts"]["pending"]), "accent_color": BRAND["amber"]},
        {"title": "Черновики", "value": str(stats["posts"]["draft"]), "accent_color": BRAND["violet"]},
    ]
    story.append(_kpi_cards(kpis, col_widths=1.25 * inch, title_style=kpi_title_style, value_style=kpi_value_style))
    story.append(Spacer(1, 16))

    # Секция статистики постов
    story.append(Paragraph("Общая статистика постов", heading2_style))
    story.append(Spacer(1, 12))

    post_data = [
        ['Статус', 'Количество'],
        ['Всего постов', str(stats['posts']['total'])],
        ['Опубликованных', str(stats['posts']['published'])],
        ['На модерации', str(stats['posts']['pending'])],
        ['Черновиков', str(stats['posts']['draft'])],
        ['Запланированных', str(stats['posts']['scheduled'])],
    ]

    post_table = Table(post_data, colWidths=[3*inch, 2*inch])
    post_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND["emerald"]),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), CYRILLIC_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), BRAND["slate100"]),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BRAND["slate100"], colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.75, BRAND["slate200"]),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(post_table)
    story.append(Spacer(1, 10))
    post_pairs = [
        ("Опубликовано", int(stats["posts"]["published"])),
        ("На модерации", int(stats["posts"]["pending"])),
        ("Черновики", int(stats["posts"]["draft"])),
        ("Запланировано", int(stats["posts"]["scheduled"])),
    ]
    story.append(_bar_chart("Инфографика: статусы постов", post_pairs, palette=[BRAND["emerald"], BRAND["amber"], BRAND["violet"], BRAND["blue"]]))
    story.append(Spacer(1, 20))

    # Статистика по авторам
    story.append(Paragraph("Статистика по авторам", heading2_style))
    story.append(Spacer(1, 12))

    author_data = [['Автор', 'Роль', 'Всего постов', 'Опубликовано', 'На модерации']]
    for author in stats['authors']:
        author_data.append([
            author['username'],
            author['role'],
            str(author['post_count']),
            str(author['published_count'] or 0),
            str(author['pending_count'] or 0)
        ])

    author_table = Table(author_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1*inch, 1*inch])
    author_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND["violet"]),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), CYRILLIC_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), BRAND["slate100"]),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BRAND["slate100"], colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.75, BRAND["slate200"]),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(author_table)
    story.append(Spacer(1, 20))

    # Последние посты
    story.append(Paragraph("Последние посты", heading2_style))
    story.append(Spacer(1, 12))

    recent_data = [['ID', 'Заголовок', 'Автор', 'Статус', 'Дата']]
    status_names = {
        'published': 'Опубликован',
        'pending_review': 'На модерации',
        'draft': 'Черновик',
        'scheduled': 'Запланирован'
    }

    for post in stats['recent_posts']:
        recent_data.append([
            str(post['id']),
            post['title'][:30] + '...' if len(post['title']) > 30 else post['title'],
            post['username'],
            status_names.get(post['status'], post['status']),
            post['created_at'][:10] if post['created_at'] else ''
        ])

    recent_table = Table(recent_data, colWidths=[0.5*inch, 2.5*inch, 1.5*inch, 1.5*inch, 1*inch])
    recent_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND["blue"]),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), CYRILLIC_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), BRAND["slate100"]),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [BRAND["slate100"], colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.75, BRAND["slate200"]),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(recent_table)

    # Генерируем PDF
    report_title = "Отчет по постам"
    doc.build(
        story,
        onFirstPage=lambda c, d: _draw_brand_chrome(c, d, report_title),
        onLaterPages=lambda c, d: _draw_brand_chrome(c, d, report_title),
    )

    # Отправляем файл
    return FileResponse(
        filepath,
        media_type="application/pdf",
        filename=filename,
        background=None
    )
