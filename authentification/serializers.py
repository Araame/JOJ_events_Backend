from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import Group

Utilisateur = get_user_model()




class InscriptionSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    role = serializers.CharField(write_only=True, required=False, default='admin')

    class Meta:
        model = Utilisateur
        fields = ('username', 'email', 'password', 'password2', 'role')
        extra_kwargs = {
            'email': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        role = validated_data.pop('role', 'admin')
        validated_data.pop('password2')
        
        utilisateur = Utilisateur.objects.create_user(**validated_data)
        
        # Attribuer le rôle via les groupes Django
        if role == 'superadmin':
            groupe, _ = Group.objects.get_or_create(name='superadmin')
            utilisateur.is_superuser = True
            utilisateur.is_staff = True
        else:  # admin par défaut
            groupe, _ = Group.objects.get_or_create(name='admin')
            utilisateur.is_staff = True
        
        utilisateur.groups.add(groupe)
        utilisateur.save()
        return utilisateur




# Serializer pour la création de superadmin
class CreerSuperAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    role = serializers.CharField(write_only=True, required=False, default='superadmin')  # <-- superadmin par défaut

    class Meta:
        model = Utilisateur
        fields = ('username', 'email', 'password', 'password2', 'role')
        extra_kwargs = {
            'email': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        role = validated_data.pop('role', 'superadmin')
        validated_data.pop('password2')
        
        utilisateur = Utilisateur.objects.create_user(**validated_data)
        
        # Attribuer le rôle superadmin
        groupe, _ = Group.objects.get_or_create(name='superadmin')
        utilisateur.is_superuser = True
        utilisateur.is_staff = True
        utilisateur.groups.add(groupe)
        utilisateur.save()
        return utilisateur




# Serializer pour la création d'admin
class CreerAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    role = serializers.CharField(write_only=True, required=False, default='admin')  # <-- admin par défaut

    class Meta:
        model = Utilisateur
        fields = ('username', 'email', 'password', 'password2', 'role')
        extra_kwargs = {
            'email': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        role = validated_data.pop('role', 'admin')
        validated_data.pop('password2')
        
        utilisateur = Utilisateur.objects.create_user(**validated_data)
        
        # Attribuer le rôle admin
        groupe, _ = Group.objects.get_or_create(name='admin')
        utilisateur.is_staff = True
        utilisateur.groups.add(groupe)
        utilisateur.save()
        return utilisateur



class UtilisateurSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Utilisateur
        fields = ('id', 'username', 'email', 'role', 'date_joined', 'last_login', 'is_active')
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
            'date_joined': {'read_only': True},
            'last_login': {'read_only': True},
            'is_active': {'read_only': True},
        }

    def get_role(self, obj):
        if obj.groups.exists():
            return obj.groups.first().name
        return 'utilisateur'



class ChangerMotDePasseSerializer(serializers.Serializer):
    ancien_mot_de_passe = serializers.CharField(required=True)
    nouveau_mot_de_passe = serializers.CharField(required=True, validators=[validate_password])
    confirmation_nouveau_mot_de_passe = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['nouveau_mot_de_passe'] != attrs['confirmation_nouveau_mot_de_passe']:
            raise serializers.ValidationError({"nouveau_mot_de_passe": "Les mots de passe ne correspondent pas."})
        return attrs



class DeconnexionSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        required=True,
        help_text="Le refresh token à invalider",
        label="Refresh Token"
    )