import django_filters
from .models import Evenement
from django.db.models import Q

class EventFiltre(django_filters.FilterSet):
    site_id = django_filters.NumberFilter(
        field_name='site_id'
    )
    categorie_id = django_filters.CharFilter(
        field_name='categorie_id'
    )
    date = django_filters.DateFilter(
        field_name='date'
    )
    heure = django_filters.TimeFilter(
        field_name='heure'
    )
    recherche = django_filters.CharFilter(
        method='filtrer_recherche'
    )

    def filtrer_recherche(self, queryset, name, value):
        return queryset.filter(
            #__icontains cherche value n'importe où dans le texte, sans tenir 
            # compte des majuscules/minuscules.
            Q(titre__icontains=value) |
            Q(categorie__nom__icontains=value) |
            Q(categorie__discipline__nom__icontains=value)
        )

    class Meta:
        model = Evenement
        fields = ['site_id','categorie_id','date','heure','recherche']
        