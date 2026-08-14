from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema
from .models import Billet, Payment, StatutPaiement, StatutBillet, PRIX_PAR_TYPE, Transaction
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
            "Initie le paiement de plusieurs billets (une commande). Le montant total est calculé côté serveur.\n\n"
            "En cas de succès, tous les billets passent au statut VALIDÉ."
        ),
        request=PaymentCreateSerializer,
        responses={201: PaymentSerializer(many=True)},
    )
    def post(self, request, *args, **kwargs):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        billets = serializer.validated_data['billets']
        methode = serializer.validated_data['methode']
        
        montant_total = sum(PRIX_PAR_TYPE.get(billet.type_billet, 0) for billet in billets)
        spectateur = billets[0].spectateur

        with transaction.atomic():
            payment = Payment.objects.create(
                billet=billets[0],
                montant=montant_total,
                methode=methode,
                statut=StatutPaiement.EN_COURS,
            )
            
            gateway = get_gateway()
            resultat = gateway.initier(
                reference=str(payment.reference),
                montant=float(montant_total),
                methode=methode,
            )
            
            if resultat['succes']:
                payment.statut = StatutPaiement.REUSSI
                payment.reference_prestataire = resultat['reference_prestataire']
                payment.statut_mis_a_jour = True   # ← FLAG : transition intentionnelle
                payment.save(update_fields=['statut', 'reference_prestataire'])
                ...

                
                # Une seule transaction pour TOUS les billets
                transaction_obj = Transaction.objects.create(
                    numero_transaction=f"MOCK-{payment.reference}",
                    mode_paiement=methode,
                    montant=montant_total,
                    telephone=spectateur.tel,
                    date=payment.date_creation
                )
                
                # Associer la même transaction à TOUS les billets
                for billet in billets:
                    billet.transaction = transaction_obj
                    billet.statut = StatutBillet.VALIDE
                    billet.save()
                
            else:
                payment.statut = StatutPaiement.ECHOUE
                payment.save()
                return Response({'erreur': resultat['message']}, status=status.HTTP_400_BAD_REQUEST)

        payments = Payment.objects.filter(billet__in=billets)
        return Response(PaymentSerializer(payments, many=True).data, status=status.HTTP_201_CREATED)


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