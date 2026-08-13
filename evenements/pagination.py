from rest_framework.pagination import PageNumberPagination

class EvenementPagination (PageNumberPagination):
    page_size = 10