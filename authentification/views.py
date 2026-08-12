from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter, OpenApiTypes
from drf_spectacular.types import OpenApiTypes

from .serializers import (
    InscriptionSerializer, 
    CreerSuperAdminSerializer, 
    CreerAdminSerializer,       
    UtilisateurSerializer, 
    ChangerMotDePasseSerializer
)

Utilisateur = get_user_model()



class InscriptionView(generics.CreateAPIView):
    queryset = Utilisateur.objects.all()
    permission_classes = [AllowAny]
    serializer_class = InscriptionSerializer
    
    @extend_schema(
        summary="Inscription d'un nouvel utilisateur",
        description="Crée un nouvel utilisateur avec le rôle spécifié (admin par défaut)",
        request=InscriptionSerializer,
        responses={201: UtilisateurSerializer},
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        utilisateur = serializer.save()
        
        refresh = RefreshToken.for_user(utilisateur)
        
        return Response({
            'utilisateur': UtilisateurSerializer(utilisateur).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Inscription réussie'
        }, status=status.HTTP_201_CREATED)



class CreerAdminView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreerAdminSerializer
    
    @extend_schema(
        summary="Créer un administrateur",
        description="Crée un nouvel administrateur (réservé aux superadmins)",
        request=CreerAdminSerializer,
        responses={201: {"utilisateur": UtilisateurSerializer, "message": "Administrateur créé avec succès"}},
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
        description="Crée un superadmin (premier utilisateur ou réservé aux superadmins)",
        request=CreerSuperAdminSerializer,
        responses={201: {"utilisateur": UtilisateurSerializer, "message": "Superadmin créé avec succès"}},
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
        description="Retourne les informations de l'utilisateur authentifié",
        responses={200: UtilisateurSerializer},
    )
    def get(self, request):
        serializer = UtilisateurSerializer(request.user)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Mettre à jour le profil",
        description="Met à jour les informations de l'utilisateur (email, username, etc.)",
        request=UtilisateurSerializer,
        responses={200: UtilisateurSerializer},
    )
    def put(self, request):
        utilisateur = request.user
        serializer = UtilisateurSerializer(utilisateur, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






class DeconnexionView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Déconnexion",
        description="Invalide le refresh token pour déconnecter l'utilisateur",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'refresh': {
                        'type': 'string',
                        'description': 'Le refresh token à invalider',
                        'example': 'votre_refresh_token_ici'
                    }
                },
                'required': ['refresh']
            }
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string', 'example': 'Déconnecté avec succès'}
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'erreur': {'type': 'string', 'example': 'Refresh token requis'}
                }
            }
        },
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({'erreur': 'Refresh token requis'}, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Déconnecté avec succès'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'erreur': str(e)}, status=status.HTTP_400_BAD_REQUEST)




class ChangerMotDePasseView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Changer le mot de passe",
        description="Permet à l'utilisateur de changer son mot de passe",
        request=ChangerMotDePasseSerializer,
        responses={200: {"message": "Mot de passe changé avec succès"}},
    )
    def put(self, request):
        serializer = ChangerMotDePasseSerializer(data=request.data)
        if serializer.is_valid():
            utilisateur = request.user
            ancien_mot_de_passe = serializer.validated_data['ancien_mot_de_passe']
            nouveau_mot_de_passe = serializer.validated_data['nouveau_mot_de_passe']
            
            if not utilisateur.check_password(ancien_mot_de_passe):
                return Response({'ancien_mot_de_passe': 'Mot de passe incorrect'}, status=status.HTTP_400_BAD_REQUEST)
            
            utilisateur.set_password(nouveau_mot_de_passe)
            utilisateur.save()
            
            return Response({'message': 'Mot de passe changé avec succès'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class CreerAdminView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreerAdminSerializer 
    
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




class ListeUtilisateursView(generics.ListAPIView):
    """
    Liste tous les utilisateurs (actifs et inactifs)
    Accessible uniquement aux superadmins
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UtilisateurSerializer
    queryset = Utilisateur.objects.all().order_by('-date_joined')
    
    def list(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response(
                {'erreur': 'Seul un superadmin peut voir la liste des utilisateurs'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().list(request, *args, **kwargs)




class RevoquerAccesView(APIView):
    """
    Révoquer l'accès d'un administrateur (le désactiver)
    Accessible uniquement aux superadmins
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, utilisateur_id):
        # Vérifier si l'utilisateur connecté est superadmin
        if not request.user.is_superuser:
            return Response(
                {'erreur': 'Seul un superadmin peut révoquer l\'accès d\'un administrateur'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            utilisateur = Utilisateur.objects.get(id=utilisateur_id)
        except Utilisateur.DoesNotExist:
            return Response(
                {'erreur': 'Utilisateur non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Ne pas permettre de révoquer un superadmin
        if utilisateur.is_superuser:
            return Response(
                {'erreur': 'Impossible de révoquer l\'accès d\'un superadmin'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Révoquer l'accès (désactiver l'utilisateur)
        utilisateur.is_active = False
        utilisateur.save()
        
        return Response({
            'message': f'Accès révoqué pour {utilisateur.username}',
            'utilisateur': UtilisateurSerializer(utilisateur).data
        }, status=status.HTTP_200_OK)




class ReactiverAccesView(APIView):
    """
    Réactiver l'accès d'un administrateur désactivé
    Accessible uniquement aux superadmins
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, utilisateur_id):
        # Vérifier si l'utilisateur connecté est superadmin
        if not request.user.is_superuser:
            return Response(
                {'erreur': 'Seul un superadmin peut réactiver l\'accès d\'un administrateur'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            utilisateur = Utilisateur.objects.get(id=utilisateur_id)
        except Utilisateur.DoesNotExist:
            return Response(
                {'erreur': 'Utilisateur non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Réactiver l'accès
        utilisateur.is_active = True
        utilisateur.save()
        
        return Response({
            'message': f'Accès réactivé pour {utilisateur.username}',
            'utilisateur': UtilisateurSerializer(utilisateur).data
        }, status=status.HTTP_200_OK)