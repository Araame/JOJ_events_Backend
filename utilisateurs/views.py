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
from .permissions import EstSuperAdmin

Utilisateur = get_user_model()


class CreerAdminView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, EstSuperAdmin]
    serializer_class = CreerAdminSerializer

    @extend_schema(
        summary="Creer un administrateur",
        description="Cree un nouvel administrateur avec des permissions specifiques. Reserve aux superadmins.",
        request=CreerAdminSerializer,
        responses={201: UtilisateurSerializer},
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        utilisateur = serializer.save()
        return Response({
            'utilisateur': UtilisateurSerializer(utilisateur).data,
            'message': 'Administrateur cree avec succes'
        }, status=status.HTTP_201_CREATED)


class CreerSuperAdminView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = CreerSuperAdminSerializer

    @extend_schema(
        summary="Creer un superadministrateur",
        description=(
            "Cree le premier superadmin librement. "
            "Si un superadmin existe deja, seul un superadmin connecte peut en creer un autre."
        ),
        request=CreerSuperAdminSerializer,
        responses={201: UtilisateurSerializer},
    )
    def create(self, request, *args, **kwargs):
        if Utilisateur.objects.filter(is_superuser=True).exists():
            if not request.user.is_authenticated or not request.user.is_superuser:
                return Response(
                    {'erreur': 'Vous devez etre superadmin pour creer un autre superadmin'},
                    status=status.HTTP_403_FORBIDDEN
                )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        utilisateur = serializer.save()
        return Response({
            'utilisateur': UtilisateurSerializer(utilisateur).data,
            'message': 'Superadmin cree avec succes'
        }, status=status.HTTP_201_CREATED)


class ProfilUtilisateurView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Obtenir le profil",
        description="Retourne les informations de l'utilisateur authentifie.",
        responses={200: UtilisateurSerializer},
    )
    def get(self, request):
        serializer = UtilisateurSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        summary="Mettre a jour le profil",
        description="Met a jour les informations de l'utilisateur (email, username).",
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
        summary="Deconnexion",
        description="Invalide le refresh token pour deconnecter l'utilisateur.",
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
            return Response({'message': 'Deconnecte avec succes'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'erreur': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChangerMotDePasseView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Changer le mot de passe",
        description="Permet a l'utilisateur connecte de changer son mot de passe.",
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
            return Response({'message': 'Mot de passe change avec succes'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListeUtilisateursView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, EstSuperAdmin]
    serializer_class = UtilisateurSerializer
    queryset = Utilisateur.objects.all().order_by('-date_joined')

    @extend_schema(
        summary="Lister les utilisateurs",
        description="Retourne la liste de tous les utilisateurs. Reserve aux superadmins.",
        responses={200: UtilisateurSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class RevoquerAccesView(APIView):
    permission_classes = [IsAuthenticated, EstSuperAdmin]

    @extend_schema(
        summary="Revoquer l'acces d'un administrateur",
        description="Desactive le compte d'un administrateur. Reserve aux superadmins.",
        responses={
            200: UtilisateurSerializer,
            403: {"type": "object", "properties": {"erreur": {"type": "string"}}},
            404: {"type": "object", "properties": {"erreur": {"type": "string"}}},
        },
    )
    def post(self, request, utilisateur_id):
        try:
            utilisateur = Utilisateur.objects.get(id=utilisateur_id)
        except Utilisateur.DoesNotExist:
            return Response({'erreur': 'Utilisateur non trouve'}, status=status.HTTP_404_NOT_FOUND)

        if utilisateur.is_superuser:
            return Response(
                {'erreur': "Impossible de revoquer l'acces d'un superadmin"},
                status=status.HTTP_403_FORBIDDEN
            )
        utilisateur.is_active = False
        utilisateur.save()
        return Response({
            'message': f'Acces revoque pour {utilisateur.username}',
            'utilisateur': UtilisateurSerializer(utilisateur).data
        }, status=status.HTTP_200_OK)


class ReactiverAccesView(APIView):
    permission_classes = [IsAuthenticated, EstSuperAdmin]

    @extend_schema(
        summary="Reactiver l'acces d'un administrateur",
        description="Reactive le compte d'un administrateur desactive. Reserve aux superadmins.",
        responses={
            200: UtilisateurSerializer,
            403: {"type": "object", "properties": {"erreur": {"type": "string"}}},
            404: {"type": "object", "properties": {"erreur": {"type": "string"}}},
        },
    )
    def post(self, request, utilisateur_id):
        try:
            utilisateur = Utilisateur.objects.get(id=utilisateur_id)
        except Utilisateur.DoesNotExist:
            return Response({'erreur': 'Utilisateur non trouve'}, status=status.HTTP_404_NOT_FOUND)

        utilisateur.is_active = True
        utilisateur.save()
        return Response({
            'message': f'Acces reactive pour {utilisateur.username}',
            'utilisateur': UtilisateurSerializer(utilisateur).data
        }, status=status.HTTP_200_OK)