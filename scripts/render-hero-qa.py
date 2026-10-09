from pathlib import Path
from unittest.mock import patch
from django.test import Client
from django.utils import timezone
from datetime import timedelta
from apps.morning_devotions.models import MorningDevotionSession

out = Path('test-results/hero-fixtures')
out.mkdir(parents=True, exist_ok=True)
now = timezone.now()
for state in ('live', 'upcoming', 'none'):
    session = None if state == 'none' else MorningDevotionSession(
        slug='hero-qa-session', title_en='Walking by Faith', title_rw='Kugendera mu kwizera',
        start_datetime=now - timedelta(minutes=5) if state == 'live' else now + timedelta(days=1),
        end_datetime=now + timedelta(minutes=55) if state == 'live' else now + timedelta(days=1, hours=1),
        status=MorningDevotionSession.STATUS_PUBLISHED,
        meet_url='https://meet.google.com/abc-defg-hij',
    )
    with patch('apps.core.views.MorningDevotionSession.current_or_next', return_value=session):
        response = Client().get('/')
    out.joinpath(state+'.html').write_bytes(response.content)
