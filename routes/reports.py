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

    doc = SimpleDocTemplate(filepath, pagesize=letter)
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
        textColor=colors.gray
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
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), CYRILLIC_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
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
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#a855f7')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), CYRILLIC_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(role_table)
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
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), CYRILLIC_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(post_table)
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
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f59e0b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), CYRILLIC_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(top_table)

    # Генерируем PDF
    doc.build(story)

    # Отправляем файл и удаляем его после отправки
    return FileResponse(
        filepath,
        media_type="application/pdf",
        filename=filename,
        background=None
    )
