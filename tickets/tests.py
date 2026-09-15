from datetime import timedelta

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Event, TicketCategory, Ticket


class ReserveTicketsFlowTests(TestCase):
    def test_home_page_hides_buy_tickets_link_when_no_upcoming_event_is_open(self):
        Event.objects.create(
            title='Past Event',
            slug='past-event',
            venue='Main Hall',
            start_datetime=timezone.now() - timedelta(days=3),
            end_datetime=timezone.now() - timedelta(days=1),
            is_active=True,
        )

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'BUY TICKETS')

    def test_home_page_shows_buy_tickets_link_when_an_event_is_still_open(self):
        Event.objects.create(
            title='Upcoming Event',
            slug='upcoming-event',
            venue='Main Hall',
            start_datetime=timezone.now() + timedelta(days=1),
            end_datetime=timezone.now() + timedelta(days=3),
            is_active=True,
        )

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'BUY TICKETS')

    def test_event_detail_page_shows_remaining_ticket_count(self):
        event = Event.objects.create(
            title='Limited Event',
            slug='limited-event',
            venue='Main Hall',
            start_datetime='2026-07-10T18:00:00Z',
            end_datetime='2026-07-10T22:00:00Z',
            is_active=True,
        )
        category = TicketCategory.objects.create(
            event=event,
            name='VIP',
            price='2500.00',
            quantity=10,
            sold=4,
        )

        response = self.client.get(reverse('tickets:event_detail', args=[event.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '6 left')
        self.assertContains(response, 'VIP')

    def test_reserve_page_renders_with_selected_ticket_details(self):
        event = Event.objects.create(
            title='Test Event',
            slug='test-event',
            venue='Main Hall',
            start_datetime='2026-07-10T18:00:00Z',
            end_datetime='2026-07-10T22:00:00Z',
            is_active=True,
        )
        category = TicketCategory.objects.create(
            event=event,
            name='VIP',
            price='2500.00',
            quantity=100,
        )

        response = self.client.post(
            reverse('tickets:reserve_tickets'),
            {
                'category_id': category.id,
                'quantity': 2,
                'phone_number': '+250788123456',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reserve Tickets')
        self.assertContains(response, 'Mobile Money')
        self.assertContains(response, 'Airtel Money')
        self.assertContains(response, '2')

    def test_reservation_redirects_to_event_detail_with_ticket(self):
        event = Event.objects.create(
            title='MoMo Event',
            slug='momo-event',
            venue='Main Hall',
            start_datetime='2026-07-10T18:00:00Z',
            end_datetime='2026-07-10T22:00:00Z',
            is_active=True,
        )
        category = TicketCategory.objects.create(
            event=event,
            name='VIP',
            price='2500.00',
            quantity=100,
        )

        response = self.client.post(
            reverse('tickets:reserve_tickets'),
            {
                'category_id': category.id,
                'quantity': 1,
                'payment_method': 'mobile_money',
                'email_address': 'guest@example.com',
                'phone_number': '+250788111222',
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith('/tickets/event/momo-event/'))

    def test_successful_reservation_sends_ticket_email_with_download_link(self):
        event = Event.objects.create(
            title='Launch Event',
            slug='launch-event',
            venue='Grand Hall',
            start_datetime='2026-07-10T18:00:00Z',
            end_datetime='2026-07-10T22:00:00Z',
            is_active=True,
        )
        category = TicketCategory.objects.create(
            event=event,
            name='Standard',
            price='3000.00',
            quantity=50,
        )

        response = self.client.post(
            reverse('tickets:reserve_tickets'),
            {
                'category_id': category.id,
                'quantity': 1,
                'payment_method': 'mobile_money',
                'email_address': 'guest@example.com',
                'phone_number': '+250788111222',
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith('/tickets/event/launch-event/'))

        payment_response = self.client.get(response.url, follow=True)
        self.assertContains(payment_response, 'Thank you for booking!')
        self.assertContains(payment_response, 'Your reservation is confirmed.')
        self.assertContains(payment_response, 'Download Ticket Image')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Your ticket for', mail.outbox[0].subject)
        self.assertIn('download', mail.outbox[0].body.lower())
        self.assertTrue(mail.outbox[0].attachments)
