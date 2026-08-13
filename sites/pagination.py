from rest_framework.pagination import PageNumberPagination


class SitePagination(PageNumberPagination):
    """Définit la pagination pour les sites"""
    page_size = 3                  
    page_size_query_param = 'page_size' 
    max_page_size = 5               
