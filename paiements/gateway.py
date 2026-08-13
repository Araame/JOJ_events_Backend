from abc import ABC, abstractmethod


class PaymentGateway(ABC):
    """
    Interface abstraite pour les prestataires de paiement.
    Implémenter cette classe pour intégrer Orange Money, Wave, etc.
    """

    @abstractmethod
    def initier(self, reference: str, montant: float, methode: str) -> dict:
        """
        Initie un paiement.
        Retourne : { 'succes': bool, 'reference_prestataire': str, 'message': str }
        """
        pass


class MockPaymentGateway(PaymentGateway):
    """
    Simulation pour le développement.
    Approuve toujours le paiement.
    """

    def initier(self, reference: str, montant: float, methode: str) -> dict:
        return {
            'succes': True,
            'reference_prestataire': f"MOCK-{reference}",
            'message': 'Paiement simulé avec succès',
        }


def get_gateway() -> PaymentGateway:
    """Retourne le gateway actif. Remplacer MockPaymentGateway par le vrai prestataire quand il sera défini."""
    return MockPaymentGateway()
