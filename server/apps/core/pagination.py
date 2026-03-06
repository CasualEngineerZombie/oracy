"""
Custom pagination classes for the Oracy AI API.
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """
    Standard pagination with page size control.
    """
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class LargePagination(PageNumberPagination):
    """
    Pagination for large datasets.
    """
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 500


class SmallPagination(PageNumberPagination):
    """
    Pagination for small datasets (e.g., dropdowns).
    """
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50
