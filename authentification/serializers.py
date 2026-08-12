from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

Utilisateur = get_user_model()


class CreerSuperAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Confirmer le mot de passe")

    class Meta:
        model = Utilisateur
        fields = ('username', 'email', 'first_name', 'last_name', 'tel', 'password', 'password2')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'tel': {'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        utilisateur = Utilisateur.objects.create_user(**validated_data)
        # is_superuser déclenche Personnel.save() → role=SUPERADMIN automatiquement
        utilisateur.is_superuser = True
        utilisateur.save()
        return utilisateur


class CreerAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Confirmer le mot de passe")

    class Meta:
        model = Utilisateur
        fields = ('username', 'email', 'first_name', 'last_name', 'tel', 'password', 'password2')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'tel': {'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        utilisateur = Utilisateur.objects.create_user(**validated_data)
        # role=ADMIN par défaut dans le modèle
        utilisateur.is_staff = True
        utilisateur.save()
        return utilisateur


class UtilisateurSerializer(serializers.ModelSerializer):
    """
    Lecture et mise à jour du profil utilisateur.
    Le rôle est lu directement depuis le champ role du modèle Personnel.
    """
    class Meta:
        model = Utilisateur
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'tel', 'role', 'date_joined', 'last_login', 'is_active')
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'tel': {'required': False},
            'role': {'read_only': True},
            'date_joined': {'read_only': True},
            'last_login': {'read_only': True},
            'is_active': {'read_only': True},
        }


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
