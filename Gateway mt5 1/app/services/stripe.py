"""
Stripe Integration für MT5 Flask Gateway
Zahlungsabwicklung und Abonnement-Management
"""

import logging
import stripe
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from app.config import Config

@dataclass
class StripeCustomer:
    """Stripe-Kunde"""
    customer_id: str
    email: str
    name: str
    created_at: datetime

@dataclass
class StripeSubscription:
    """Stripe-Abonnement"""
    subscription_id: str
    customer_id: str
    plan_id: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool

class StripeService:
    """Stripe-Service für Zahlungsabwicklung"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Stripe konfigurieren
        stripe.api_key = config.STRIPE_SECRET_KEY
        self.webhook_secret = config.STRIPE_WEBHOOK_SECRET
        
        # Verfügbare Pläne
        self.plans = {
            'basic': {
                'name': 'Basic',
                'price': 9900,  # €99.00 in Cent
                'currency': 'eur',
                'interval': 'month',
                'features': ['max_concurrent_orders', 'basic_trading', 'api_access', 'email_support']
            },
            'pro': {
                'name': 'Pro',
                'price': 19900,  # €199.00 in Cent
                'currency': 'eur',
                'interval': 'month',
                'features': ['max_concurrent_orders', 'advanced_strategies', 'custom_indicators', 'priority_support']
            },
            'enterprise': {
                'name': 'Enterprise',
                'price': 49900,  # €499.00 in Cent
                'currency': 'eur',
                'interval': 'month',
                'features': ['unlimited_orders', 'all_strategies', 'white_label', '24_7_support']
            }
        }
    
    def create_customer(self, email: str, name: str) -> Optional[StripeCustomer]:
        """Erstellt Stripe-Kunde"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    'source': 'mt5_gateway',
                    'created_at': datetime.utcnow().isoformat()
                }
            )
            
            return StripeCustomer(
                customer_id=customer.id,
                email=customer.email,
                name=customer.name,
                created_at=datetime.fromtimestamp(customer.created)
            )
            
        except stripe.error.StripeError as e:
            self.logger.error(f"Fehler beim Erstellen des Stripe-Kunden: {e}")
            return None
    
    def create_checkout_session(self, customer_id: str, plan_id: str, 
                               success_url: str, cancel_url: str) -> Optional[str]:
        """Erstellt Checkout-Session"""
        try:
            plan = self.plans.get(plan_id)
            if not plan:
                return None
            
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': plan['currency'],
                        'product_data': {
                            'name': f"MT5 Gateway {plan['name']}",
                            'description': f"{plan['name']} Lizenz für MT5 Flask Gateway"
                        },
                        'unit_amount': plan['price'],
                        'recurring': {
                            'interval': plan['interval']
                        }
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'plan_id': plan_id,
                    'source': 'mt5_gateway'
                }
            )
            
            return session.url
            
        except stripe.error.StripeError as e:
            self.logger.error(f"Fehler beim Erstellen der Checkout-Session: {e}")
            return None
    
    def get_subscription(self, subscription_id: str) -> Optional[StripeSubscription]:
        """Ruft Abonnement ab"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            return StripeSubscription(
                subscription_id=subscription.id,
                customer_id=subscription.customer,
                plan_id=subscription.items.data[0].price.id,
                status=subscription.status,
                current_period_start=datetime.fromtimestamp(subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(subscription.current_period_end),
                cancel_at_period_end=subscription.cancel_at_period_end
            )
            
        except stripe.error.StripeError as e:
            self.logger.error(f"Fehler beim Abrufen des Abonnements: {e}")
            return None
    
    def cancel_subscription(self, subscription_id: str, 
                          cancel_at_period_end: bool = True) -> bool:
        """Kündigt Abonnement"""
        try:
            if cancel_at_period_end:
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                stripe.Subscription.delete(subscription_id)
            
            return True
            
        except stripe.error.StripeError as e:
            self.logger.error(f"Fehler beim Kündigen des Abonnements: {e}")
            return False
    
    def handle_webhook(self, payload: str, signature: str) -> Optional[Dict[str, Any]]:
        """Behandelt Stripe-Webhook"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            
            # Event verarbeiten
            if event['type'] == 'checkout.session.completed':
                return self._handle_checkout_completed(event['data']['object'])
            elif event['type'] == 'customer.subscription.created':
                return self._handle_subscription_created(event['data']['object'])
            elif event['type'] == 'customer.subscription.updated':
                return self._handle_subscription_updated(event['data']['object'])
            elif event['type'] == 'customer.subscription.deleted':
                return self._handle_subscription_deleted(event['data']['object'])
            elif event['type'] == 'invoice.payment_succeeded':
                return self._handle_payment_succeeded(event['data']['object'])
            elif event['type'] == 'invoice.payment_failed':
                return self._handle_payment_failed(event['data']['object'])
            
            return {'status': 'ignored', 'event_type': event['type']}
            
        except stripe.error.SignatureVerificationError as e:
            self.logger.error(f"Stripe-Webhook-Signatur ungültig: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten des Stripe-Webhooks: {e}")
            return None
    
    def _handle_checkout_completed(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt abgeschlossene Checkout-Session"""
        self.logger.info(f"Checkout-Session abgeschlossen: {session['id']}")
        
        return {
            'status': 'success',
            'event_type': 'checkout.session.completed',
            'session_id': session['id'],
            'customer_id': session['customer'],
            'subscription_id': session.get('subscription')
        }
    
    def _handle_subscription_created(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt erstelltes Abonnement"""
        self.logger.info(f"Abonnement erstellt: {subscription['id']}")
        
        return {
            'status': 'success',
            'event_type': 'customer.subscription.created',
            'subscription_id': subscription['id'],
            'customer_id': subscription['customer'],
            'status': subscription['status']
        }
    
    def _handle_subscription_updated(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt aktualisiertes Abonnement"""
        self.logger.info(f"Abonnement aktualisiert: {subscription['id']}")
        
        return {
            'status': 'success',
            'event_type': 'customer.subscription.updated',
            'subscription_id': subscription['id'],
            'customer_id': subscription['customer'],
            'status': subscription['status']
        }
    
    def _handle_subscription_deleted(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt gelöschtes Abonnement"""
        self.logger.info(f"Abonnement gelöscht: {subscription['id']}")
        
        return {
            'status': 'success',
            'event_type': 'customer.subscription.deleted',
            'subscription_id': subscription['id'],
            'customer_id': subscription['customer']
        }
    
    def _handle_payment_succeeded(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt erfolgreiche Zahlung"""
        self.logger.info(f"Zahlung erfolgreich: {invoice['id']}")
        
        return {
            'status': 'success',
            'event_type': 'invoice.payment_succeeded',
            'invoice_id': invoice['id'],
            'customer_id': invoice['customer'],
            'amount_paid': invoice['amount_paid']
        }
    
    def _handle_payment_failed(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt fehlgeschlagene Zahlung"""
        self.logger.warning(f"Zahlung fehlgeschlagen: {invoice['id']}")
        
        return {
            'status': 'success',
            'event_type': 'invoice.payment_failed',
            'invoice_id': invoice['id'],
            'customer_id': invoice['customer'],
            'amount_due': invoice['amount_due']
        }
    
    def get_plan_info(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Gibt Plan-Informationen zurück"""
        return self.plans.get(plan_id)
    
    def get_all_plans(self) -> Dict[str, Any]:
        """Gibt alle verfügbaren Pläne zurück"""
        return self.plans

# Globale Stripe-Service Instanz
stripe_service: Optional[StripeService] = None

def init_stripe_service(config: Config) -> None:
    """Initialisiert den Stripe-Service"""
    global stripe_service
    stripe_service = StripeService(config)

def get_stripe_service() -> Optional[StripeService]:
    """Gibt den Stripe-Service zurück"""
    return stripe_service
