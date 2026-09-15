Top5Sai Tickets
================

This app provides an events and ticketing system integrated into Top5Sai.

Quick setup:

1. Add `tickets` to `INSTALLED_APPS` (already added).
2. Install dependencies: `pip install qrcode pillow`
3. Make migrations and migrate:

   ```bash
   python manage.py makemigrations tickets
   python manage.py migrate
   ```

4. Configure mobile-money providers (MTN MoMo / Airtel Money) by replacing the stub in `tickets/utils.py` with real API calls.

Notes:
- QR codes are generated and saved to `MEDIA_ROOT/tickets/qrcodes/`.
- The payment flow is stubbed — integrate your provider's SDK/webhooks for production.
