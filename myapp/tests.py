from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .models import BlogPost


class BlogPostTests(TestCase):
	def test_blog_page_displays_admin_created_photo_and_description(self):
		photo = SimpleUploadedFile(
			'activity.jpg',
			b'not-a-real-image-but-valid-for-model-upload',
			content_type='image/jpeg',
		)
		BlogPost.objects.create(
			photo=photo,
			description='TOP5SAI delivered sound and lighting for the event.',
			event_date='2026-09-15',
			venue='Kigali Convention Centre',
		)

		response = self.client.get('/blogs/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'TOP5SAI delivered sound and lighting for the event.')
		self.assertContains(response, 'September 15, 2026')
		self.assertContains(response, 'Kigali Convention Centre')
		self.assertContains(response, '/media/blog/photos/activity')

	def test_blog_page_embeds_youtube_video_without_photo(self):
		BlogPost.objects.create(
			youtube_url='https://www.youtube.com/watch?v=TOP5Video123',
			description='TOP5SAI activity video.',
		)

		response = self.client.get('/blogs/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'https://www.youtube.com/embed/TOP5Video123')
		self.assertContains(response, 'TOP5SAI activity video.')

