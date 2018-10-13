
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 2                   # 默认每页返回的条数
    max_page_size = 20              # 每页返回的最大条数
    page_size_query_param = 'page_size'    # url中设置 page_size的键,默认为page_size
    page_query_param = 'page'          # url中设置 page的键,默认为page
