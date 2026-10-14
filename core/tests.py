from decimal import Decimal
from datetime import timedelta
from unittest.mock import MagicMock, patch

import razorpay
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Address, Cart, Order, Payment, Product, ProductSize


class RazorpayCheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='buyer', password='pass12345')
        self.client.login(username='buyer', password='pass12345')

        self.address = Address.objects.create(
            user=self.user,
            first_name='Test',
            last_name='Buyer',
            city='Hyderabad',
            address_line_one='123 Street',
        )

        self.product = Product.objects.create(name='Mango Pickle')
        self.size = ProductSize.objects.create(
            product=self.product, size='250 grms', price=Decimal('100.00')
        )
        Cart.objects.create(
            user=self.user,
            product=self.product,
            size=self.size.size,
            quantity=2,
            price_at_addition=Decimal('100.00'),
        )

    @patch('core.views.razorpay.Client')
    def test_online_checkout_creates_pending_order_and_keeps_cart(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.order.create.return_value = {
            'id': 'order_test123', 'amount': 20000, 'currency': 'INR'
        }
        mock_client_cls.return_value = mock_client

        response = self.client.post(
            reverse('checkout'),
            data={'address_id': self.address.id, 'payment_method': 'online'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['razorpay_order_id'], 'order_test123')

        order = Order.objects.get(id=payload['order_id'])
        self.assertEqual(order.status, 'pending')
        payment = Payment.objects.get(order=order)
        self.assertEqual(payment.payment_id, 'order_test123')
        self.assertEqual(payment.status, 'pending')
        # Cart must survive until payment is verified.
        self.assertTrue(Cart.objects.filter(user=self.user).exists())

    @patch('core.views.razorpay.Client')
    def test_verify_payment_success_places_order_and_clears_cart(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        order = Order.objects.create(
            user=self.user, address=self.address, payment_method='online',
            status='pending', total_amount=Decimal('200.00'),
        )
        payment = Payment.objects.create(
            order=order, user=self.user, payment_method='online',
            amount=Decimal('200.00'), status='pending', payment_id='order_test123',
        )

        response = self.client.post(
            reverse('verify_payment'),
            data={
                'order_id': order.id,
                'razorpay_order_id': 'order_test123',
                'razorpay_payment_id': 'pay_test123',
                'razorpay_signature': 'sig_test123',
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])

        order.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(order.status, 'placed')
        self.assertEqual(payment.status, 'success')
        self.assertEqual(payment.transaction_id, 'pay_test123')
        self.assertFalse(Cart.objects.filter(user=self.user).exists())

    @patch('core.views.razorpay.Client')
    def test_verify_payment_bad_signature_cancels_order(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.utility.verify_payment_signature.side_effect = (
            razorpay.errors.SignatureVerificationError('bad signature')
        )
        mock_client_cls.return_value = mock_client

        order = Order.objects.create(
            user=self.user, address=self.address, payment_method='online',
            status='pending', total_amount=Decimal('200.00'),
        )
        Payment.objects.create(
            order=order, user=self.user, payment_method='online',
            amount=Decimal('200.00'), status='pending', payment_id='order_test123',
        )

        response = self.client.post(
            reverse('verify_payment'),
            data={
                'order_id': order.id,
                'razorpay_order_id': 'order_test123',
                'razorpay_payment_id': 'pay_test123',
                'razorpay_signature': 'bad_sig',
            },
            content_type='application/json',
        )

        payload = response.json()
        self.assertFalse(payload['success'])
        order.refresh_from_db()
        self.assertEqual(order.status, 'cancelled')
        # Cart should still exist so the user can retry.
        self.assertTrue(Cart.objects.filter(user=self.user).exists())

    def test_payment_cancel_marks_pending_order_cancelled(self):
        order = Order.objects.create(
            user=self.user, address=self.address, payment_method='online',
            status='pending', total_amount=Decimal('200.00'),
        )
        Payment.objects.create(
            order=order, user=self.user, payment_method='online',
            amount=Decimal('200.00'), status='pending', payment_id='order_test123',
        )

        response = self.client.post(
            reverse('payment_cancel'),
            data={'order_id': order.id},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'cancelled')

    def test_cod_checkout_still_works(self):
        response = self.client.post(
            reverse('checkout'),
            data={'address_id': self.address.id, 'payment_method': 'cod'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        order = Order.objects.get(id=payload['order_id'])
        self.assertEqual(order.status, 'placed')
        self.assertFalse(Cart.objects.filter(user=self.user).exists())


class OrderAdminDeleteTests(TestCase):
    def test_order_with_payment_can_be_deleted_from_admin(self):
        admin_user = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='pass12345'
        )
        buyer = User.objects.create_user(username='buyer')
        order = Order.objects.create(
            user=buyer, payment_method='cod', total_amount=Decimal('100.00')
        )
        Payment.objects.create(
            order=order, user=buyer, payment_method='cod',
            amount=Decimal('100.00'),
        )
        self.client.force_login(admin_user)
        changelist_url = reverse('admin:core_order_changelist')
        selected_order = str(order.pk)

        confirmation = self.client.post(
            changelist_url,
            {
                'action': 'delete_selected',
                '_selected_action': selected_order,
                'index': '0',
            },
        )
        self.assertEqual(confirmation.status_code, 200)

        response = self.client.post(
            changelist_url,
            {
                'action': 'delete_selected',
                '_selected_action': selected_order,
                'post': 'yes',
            },
        )
        self.assertRedirects(response, changelist_url)
        self.assertFalse(Order.objects.filter(pk=order.pk).exists())


class DashboardOrderTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='pass12345'
        )
        self.customer = User.objects.create_user(username='buyer')
        self.client.force_login(self.admin_user)

    def test_dashboard_shows_latest_ten_unseen_orders(self):
        created_at = timezone.now()
        orders = [
            Order.objects.create(
                user=self.customer,
                payment_method='cod',
                total_amount=Decimal('100.00'),
                created_at=created_at + timedelta(seconds=index),
            )
            for index in range(11)
        ]

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        displayed_order_ids = [order.pk for order in response.context['orders']]
        self.assertEqual(
            displayed_order_ids,
            [order.pk for order in reversed(orders[1:])],
        )

    def test_marking_order_seen_removes_it_from_dashboard_but_keeps_it_in_orders(self):
        order = Order.objects.create(
            user=self.customer,
            payment_method='cod',
            total_amount=Decimal('100.00'),
        )

        response = self.client.post(
            reverse('mark_order_seen', args=[order.pk])
        )

        self.assertRedirects(response, reverse('dashboard'))
        order.refresh_from_db()
        self.assertTrue(order.is_seen)
        self.assertNotContains(self.client.get(reverse('dashboard')), '#{}'.format(order.pk))
        self.assertContains(self.client.get(reverse('orders_list')), '#{}'.format(order.pk))


class ProductPriceEditingTests(TestCase):
    def setUp(self):
        admin_user = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='pass12345'
        )
        self.client.force_login(admin_user)
        self.product = Product.objects.create(name='Mango Pickle')
        self.size = ProductSize.objects.create(
            product=self.product,
            size='250 grms',
            price=Decimal('100.00'),
            discounted_price=Decimal('90.00'),
        )

    def test_create_product_page_uses_inline_responsive_layout_styles(self):
        response = self.client.get(reverse('create_product'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'create-product-form')
        self.assertContains(response, '<div class="content-wrapper">')
        self.assertContains(response, '@media (max-width: 767.98px)')
        self.assertNotContains(response, 'backend/assets/js/pages/dashboard.js')
        self.assertNotContains(response, 'admin-responsive.css')

    def test_product_list_renders_products_and_resolved_shared_assets(self):
        response = self.client.get(reverse('products'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
        self.assertContains(response, reverse('edit_product', args=[self.product.slug]))
        self.assertContains(response, '/static/backend/assets/js/vendor.js')
        self.assertNotContains(response, "{% static")
        self.assertNotContains(response, "products__sidebar")

    def test_edit_page_displays_product_size_prices(self):
        response = self.client.get(
            reverse('edit_product', args=[self.product.slug])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Size pricing')
        self.assertContains(response, 'value="100.00"')
        self.assertContains(response, 'value="90.00"')

    def test_edit_product_updates_size_prices(self):
        response = self.client.post(
            reverse('edit_product', args=[self.product.slug]),
            {
                'name': self.product.name,
                'in_stock': 'in_stock',
                'stock_count': '10',
                'status': 'active',
                'sizes-TOTAL_FORMS': '2',
                'sizes-INITIAL_FORMS': '1',
                'sizes-MIN_NUM_FORMS': '0',
                'sizes-MAX_NUM_FORMS': '1000',
                'sizes-0-id': str(self.size.pk),
                'sizes-0-size': '250 grms',
                'sizes-0-price': '125.50',
                'sizes-0-discounted_price': '110.00',
                'sizes-1-size': '500 grms',
                'sizes-1-price': '220.00',
                'sizes-1-discounted_price': '200.00',
            },
        )

        self.assertRedirects(response, reverse('products'))
        self.size.refresh_from_db()
        self.assertEqual(self.size.price, Decimal('125.50'))
        self.assertEqual(self.size.discounted_price, Decimal('110.00'))
        added_size = ProductSize.objects.get(product=self.product, size='500 grms')
        self.assertEqual(added_size.price, Decimal('220.00'))
        self.assertEqual(added_size.discounted_price, Decimal('200.00'))
