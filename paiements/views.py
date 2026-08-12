from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema

from .models import Billet, Payment, StatutPaiement, StatutBillet, PRIX_PAR_TYPE
from .serializers import (
    BilletSerializer, CommandeBilletSerializer, CommandeReponseSerializer,
    PaymentSerializer, PaymentCreateSerializer,
)
from .gateway import get_gateway


class BilletListCreateView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CommandeBilletSerializer

    @extend_schema(
        summary="Réserver des billets",
        description=(
            "Permet à un spectateur de réserver des billets sans créer de compte.\n\n"
            "Prix par type :\n"
            "- STANDARD : 5 000 FCFA\n"
            "- VIP : 15 000 FCFA\n"
            "- PRESSE : gratuit"
        ),
        request=CommandeBilletSerializer,
        responses={201: CommandeReponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = CommandeBilletSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        billets = serializer.save()
        total = sum(PRIX_PAR_TYPE.get(b.type_billet, 0) for b in billets)
        return Response({
            'billets': BilletSerializer(billets, many=True).data,
            'total': total,
            'nombre_billets': len(billets),
        }, status=status.HTTP_201_CREATED)


class BilletDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = BilletSerializer
    queryset = Billet.objects.select_related('evenement', 'spectateur')

    @extend_schema(
        summary="Détail d'un billet",
        description="Retourne le détail d'un billet avec ses zones accessibles.",
        responses={200: BilletSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PaymentCreateView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PaymentCreateSerializer

    @extend_schema(
        summary="Initier un paiement",
        description=(
            "Initie le paiement d'un billet. Le montant est calculé côté serveur.\n\n"
            "En cas de succès, le billet passe au statut VALIDÉ."
        ),
        request=PaymentCreateSerializer,
        responses={201: PaymentSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        billet = serializer.validated_data['billet']
        methode = serializer.validated_data['methode']
        montant = PRIX_PAR_TYPE.get(billet.type_billet, 0)

        with transaction.atomic():
            payment = Payment.objects.create(
                billet=billet,
                montant=montant,
                methode=methode,
                statut=StatutPaiement.EN_COURS,
            )
            gateway = get_gateway()
            resultat = gateway.initier(
                reference=str(payment.reference),
                montant=float(montant),
                methode=methode,
            )
            if resultat['succes']:
                payment.statut = StatutPaiement.REUSSI
                payment.reference_prestataire = resultat['reference_prestataire']
                payment.save()
                billet.statut = StatutBillet.VALIDE
                billet.save()
            else:
                payment.statut = StatutPaiement.ECHOUE
                payment.save()
                return Response({'erreur': resultat['message']}, status=status.HTTP_400_BAD_REQUEST)

        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class PaymentDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PaymentSerializer
    queryset = Payment.objects.select_related('billet')

    @extend_schema(
        summary="Résumé d'un paiement",
        description="Retourne le résumé d'un paiement.",
        responses={200: PaymentSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
