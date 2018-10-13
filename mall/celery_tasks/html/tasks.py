import os
from django.template import loader
from mall import settings
from celery_tasks.main import app
from contents.models import ContentCategory
from utils.goods import get_categories


@app.task(name='generate_static_list_search_html')
def generate_static_list_search_html():
    categories = get_categories()
    context = {
        'categories': categories,
    }
    template = loader.get_template("list.html")
    html_data = template.render(context=context)
    file_path = os.path.join(settings.GENERATED_STATIC_HTML_FILES_DIR, 'list.html')
    with open(file_path, 'w') as f:
        f.write(html_data)
