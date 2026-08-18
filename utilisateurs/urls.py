from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView
)
from .views import (
    ProfilUtilisateurView,
    DeconnexionView,
    ChangerMotDePasseView,
    CreerAdminView,
    CreerSuperAdminView,
    ListeUtilisateursView,
    RevoquerAccesView,
    ReactiverAccesView,
)

urlpatterns = [
    # JWT
    path('connexion/', TokenObtainPairView.as_view(), name='connexion'),
    path('rafraichir-token/', TokenRefreshView.as_view(), name='rafraichir-token'),
    path('verifier-token/', TokenVerifyView.as_view(), name='verifier-token'),

    # Profil & session
    path('profil/', ProfilUtilisateurView.as_view(), name='profil'),
    path('deconnexion/', DeconnexionView.as_view(), name='deconnexion'),
    path('changer-mot-de-passe/', ChangerMotDePasseView.as_view(), name='changer-mot-de-passe'),

    # Création de comptes (réservé aux superadmins, sauf premier superadmin)
    path('creer-admin/', CreerAdminView.as_view(), name='creer-admin'),
    path('creer-superadmin/', CreerSuperAdminView.as_view(), name='creer-superadmin'),

    # Gestion des utilisateurs (réservé aux superadmins)
    path('utilisateurs/', ListeUtilisateursView.as_view(), name='liste-utilisateurs'),
    path('revoquer-acces/<int:utilisateur_id>/', RevoquerAccesView.as_view(), name='revoquer-acces'),
    path('reactiver-acces/<int:utilisateur_id>/', ReactiverAccesView.as_view(), name='reactiver-acces'),

    path('obtenir-token/', TokenObtainPairView.as_view(), name='obtenir-token'),
    path('blacklist-token/', TokenBlacklistView.as_view(), name='blacklist-token'),
]
