from docx import Document
import os
from database import db
from models import Post

def convert_docx_to_posts(docx_path):
    """
    Convierte un documento .docx en posts para el blog.
    Cada sección del documento se convierte en un post separado.
    """
    doc = Document(docx_path)
    current_title = "Introducción"
    current_content = []
    posts = []

    for paragraph in doc.paragraphs:
        # Si es un título (texto en negrita o estilo de título)
        if any(run.bold for run in paragraph.runs) or paragraph.style.name.startswith('Heading'):
            # Si hay contenido acumulado, guardarlo como post
            if current_content:
                posts.append({
                    'title': current_title,
                    'content': '\n\n'.join(current_content)
                })
                current_content = []
            current_title = paragraph.text
        else:
            if paragraph.text.strip():
                current_content.append(paragraph.text)

    # Guardar el último post
    if current_content:
        posts.append({
            'title': current_title,
            'content': '\n\n'.join(current_content)
        })

    return posts

def import_docx_to_blog(docx_path):
    """
    Importa el contenido del documento como posts en el blog.
    """
    try:
        posts = convert_docx_to_posts(docx_path)
        for post_data in posts:
            post = Post(
                title=post_data['title'],
                content=post_data['content']
            )
            db.session.add(post)
        db.session.commit()
        return True, f"Se importaron {len(posts)} posts exitosamente"
    except Exception as e:
        return False, f"Error al importar el documento: {str(e)}"