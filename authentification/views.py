from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema

from .serializers import (
    CreerSuperAdminSerializer,
    CreerAdminSerializer,
    UtilisateurSerializer,
    ChangerMotDePasseSerializer,
)

Utilisateur = get_user_model()


class CreerAdminView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreerAdminSerializer

    @extend_schema(
        summary="Créer un administrateur",
        description="Crée un nouvel administrateur. Réservé aux superadmins.",
        request=CreerAdminSerializer,
        responses={201: UtilisateurSerializer},
    )
    def create(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response(
                {'erreur': 'Seul un superadmin peut créer un administrateur'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        utilisateur = serializer.save()
        return Response({
            'utilisateur': UtilisateurSerializer(utilisateur).data,
            'message': 'Administrateur créé avec succès'
        }, status=status.HTTP_201_CREATED)


class CreerSuperAdminView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = CreerSuperAdminSerializer

    @extend_schema(
        summary="Créer un superadministrateur",
        description=(
            "Crée le premier superadmin librement. "
            "Si un superadmin existe déjà, seul un superadmin connecté peut en créer un autre."
        ),
        request=CreerSuperAdminSerializer,
        responses={201: UtilisateurSerializer},
    )
    def create(self, request, *args, **kwargs):
        if Utilisateur.objects.filter(is_superuser=True).exists():
            if not request.user.is_authenticated or not request.user.is_superuser:
                return Response(
                    {'erreur': 'Vous devez être superadmin pour créer un autre superadmin'},
                    status=status.HTTP_403_FORBIDDEN
                )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        utilisateur = serializer.save()
        return Response({
            'utilisateur': UtilisateurSerializer(utilisateur).data,
            'message': 'Superadmin créé avec succès'
        }, status=status.HTTP_201_CREATED)


class ProfilUtilisateurView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Obtenir le profil",
        description="Retourne les informations de l'utilisateur authentifié.",
        responses={200: UtilisateurSerializer},
    )
    def get(self, request):
        serializer = UtilisateurSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        summary="Mettre à jour le profil",
        description="Met à jour les informations de l'utilisateur (email, username).",
        request=UtilisateurSerializer,
        responses={200: UtilisateurSerializer},
    )
    def put(self, request):
        serializer = UtilisateurSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeconnexionView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Déconnexion",
        description="Invalide le refresh token pour déconnecter l'utilisateur.",
        request={"application/json": {
            "type": "object",
            "properties": {"refresh": {"type": "string"}},
            "required": ["refresh"]
        }},
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}},
    )
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'erreur': 'Refresh token requis'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Déconnecté avec succès'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'erreur': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChangerMotDePasseView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Changer le mot de passe",
        description="Permet à l'utilisateur connecté de changer son mot de passe.",
        request=ChangerMotDePasseSerializer,
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}},
    )
    def put(self, request):
        serializer = ChangerMotDePasseSerializer(data=request.data)
        if serializer.is_valid():
            utilisateur = request.user
            if not utilisateur.check_password(serializer.validated_data['ancien_mot_de_passe']):
                return Response(
                    {'ancien_mot_de_passe': 'Mot de passe incorrect'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            utilisateur.set_password(serializer.validated_data['nouveau_mot_de_passe'])
            utilisateur.save()
            return Response({'message': 'Mot de passe changé avec succès'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListeUtilisateursView(generics.ListAPIView):
    """Liste tous les utilisateurs. Réservé aux superadmins."""
    permission_classes = [IsAuthenticated]
    serializer_class = UtilisateurSerializer
    queryset = Utilisateur.objects.all().order_by('-date_joined')

    @extend_schema(
        summary="Lister les utilisateurs",
        description="Retourne la liste de tous les utilisateurs. Réservé aux superadmins.",
        responses={200: UtilisateurSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response(
                {'erreur': 'Seul un superadmin peut voir la liste des utilisateurs'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().list(request, *args, **kwargs)


class RevoquerAccesView(APIView):
    """Désactive un administrateur. Réservé aux superadmins."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Révoquer l'accès d'un administrateur",
        description="Désactive le compte d'un administrateur. Réservé aux superadmins.",
        responses={
            200: UtilisateurSerializer,
            403: {"type": "object", "properties": {"erreur": {"type": "string"}}},
            404: {"type": "object", "properties": {"erreur": {"type": "string"}}},
        },
    )
    def post(self, request, utilisateur_id):
        if not request.user.is_superuser:
            return Response(
                {'erreur': "Seul un superadmin peut révoquer l'accès d'un administrateur"},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            utilisateur = Utilisateur.objects.get(id=utilisateur_id)
        except Utilisateur.DoesNotExist:
            return Response({'erreur': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)

        if utilisateur.is_superuser:
            return Response(
                {'erreur': "Impossible de révoquer l'accès d'un superadmin"},
                status=status.HTTP_403_FORBIDDEN
            )
        utilisateur.is_active = False
        utilisateur.save()
        return Response({
            'message': f'Accès révoqué pour {utilisateur.username}',
            'utilisateur': UtilisateurSerializer(utilisateur).data
        }, status=status.HTTP_200_OK)


class ReactiverAccesView(APIView):
    """Réactive un administrateur désactivé. Réservé aux superadmins."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Réactiver l'accès d'un administrateur",
        description="Réactive le compte d'un administrateur désactivé. Réservé aux superadmins.",
        responses={
            200: UtilisateurSerializer,
            403: {"type": "object", "properties": {"erreur": {"type": "string"}}},
            404: {"type": "object", "properties": {"erreur": {"type": "string"}}},
        },
    )
    def post(self, request, utilisateur_id):
        if not request.user.is_superuser:
            return Response(
                {'erreur': "Seul un superadmin peut réactiver l'accès d'un administrateur"},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            utilisateur = Utilisateur.objects.get(id=utilisateur_id)
        except Utilisateur.DoesNotExist:
            return Response({'erreur': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)

        utilisateur.is_active = True
        utilisateur.save()
        return Response({
            'message': f'Accès réactivé pour {utilisateur.username}',
            'utilisateur': UtilisateurSerializer(utilisateur).data
        }, status=status.HTTP_200_OK)
