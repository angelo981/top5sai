from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from voting.models import VotingCampaign, VotingCategory, Candidate


class Command(BaseCommand):
    help = 'Populate the database with sample voting campaigns and candidates for testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Creating sample voting data...'))

        # Check if data already exists
        if VotingCampaign.objects.exists():
            self.stdout.write(
                self.style.ERROR('Sample data already exists. Please delete existing campaigns first.')
            )
            return

        # Create Campaign 1
        campaign1 = VotingCampaign.objects.create(
            title='Best Artist 2024',
            description='Vote for your favorite artist in this exciting competition. This campaign celebrates the most talented artists of 2024.',
            short_description='Participate in our annual artist voting competition',
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30)
        )
        self.stdout.write(f'✓ Created campaign: {campaign1.title}')

        # Create categories for campaign 1
        category1_1 = VotingCategory.objects.create(
            campaign=campaign1,
            name='Best Male Artist',
            description='Vote for the best performing male artist',
            order=1
        )
        
        category1_2 = VotingCategory.objects.create(
            campaign=campaign1,
            name='Best Female Artist',
            description='Vote for the best performing female artist',
            order=2
        )
        
        category1_3 = VotingCategory.objects.create(
            campaign=campaign1,
            name='Best Group',
            description='Vote for the best music group or band',
            order=3
        )
        self.stdout.write(f'✓ Created 3 categories for {campaign1.title}')

        # Create candidates for category 1
        candidates_male = [
            {'name': 'Ismail Ayouni', 'description': 'Rising star from Rwanda with unique musical style'},
            {'name': 'Rafiki Jazz', 'description': 'Award-winning jazz musician from East Africa'},
            {'name': 'The Riddler', 'description': 'Popular hip-hop artist with viral hits'},
            {'name': 'King Kaka', 'description': 'Legendary artist with decades of experience'},
        ]
        
        for idx, cand in enumerate(candidates_male, 1):
            Candidate.objects.create(
                category=category1_1,
                name=cand['name'],
                description=cand['description'],
                order=idx
            )
        self.stdout.write(f'✓ Created 4 candidates for {category1_1.name}')

        # Create candidates for category 2
        candidates_female = [
            {'name': 'Mama Rwanda', 'description': 'Iconic female artist known for powerful vocals'},
            {'name': 'Umurage TV', 'description': 'Young talented singer with modern sound'},
            {'name': 'Candy Wa Rwanda', 'description': 'Pop artist with infectious energy'},
            {'name': 'Ruby Soul', 'description': 'Soulful R&B singer captivating audiences'},
        ]
        
        for idx, cand in enumerate(candidates_female, 1):
            Candidate.objects.create(
                category=category1_2,
                name=cand['name'],
                description=cand['description'],
                order=idx
            )
        self.stdout.write(f'✓ Created 4 candidates for {category1_2.name}')

        # Create candidates for category 3
        candidates_groups = [
            {'name': 'The Great Voices', 'description': 'Legendary group with timeless hits'},
            {'name': 'Urban Movement', 'description': 'Contemporary music collective with fresh sound'},
            {'name': 'Kigali Harmony', 'description': 'Vocal group known for intricate harmonies'},
            {'name': 'Beats United', 'description': 'Electronic music group pushing boundaries'},
        ]
        
        for idx, cand in enumerate(candidates_groups, 1):
            Candidate.objects.create(
                category=category1_3,
                name=cand['name'],
                description=cand['description'],
                order=idx
            )
        self.stdout.write(f'✓ Created 4 candidates for {category1_3.name}')

        # Create Campaign 2
        campaign2 = VotingCampaign.objects.create(
            title='Best Song of the Year',
            description='Vote for the most memorable and impactful song released this year. Choose based on lyrics, melody, production, and overall impact.',
            short_description='Vote for your favorite song of the year',
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=14)
        )
        self.stdout.write(f'✓ Created campaign: {campaign2.title}')

        # Create categories for campaign 2
        category2_1 = VotingCategory.objects.create(
            campaign=campaign2,
            name='Best Pop Song',
            description='The catchiest pop songs of the year',
            order=1
        )
        
        category2_2 = VotingCategory.objects.create(
            campaign=campaign2,
            name='Best Hip-Hop Track',
            description='The hottest hip-hop tracks of the year',
            order=2
        )
        self.stdout.write(f'✓ Created 2 categories for {campaign2.title}')

        # Create candidates for campaign 2
        songs_pop = [
            {'name': 'Dancing in the Moonlight', 'description': 'Upbeat summer anthem'},
            {'name': 'Forever Young', 'description': 'Emotional ballad about timeless youth'},
            {'name': 'Electric Dreams', 'description': 'Synth-pop masterpiece'},
            {'name': 'Love is Real', 'description': 'Heartfelt love song'},
        ]
        
        for idx, song in enumerate(songs_pop, 1):
            Candidate.objects.create(
                category=category2_1,
                name=song['name'],
                description=song['description'],
                order=idx
            )
        self.stdout.write(f'✓ Created 4 songs for {category2_1.name}')

        songs_hiphop = [
            {'name': 'Street Legends', 'description': 'Gritty street narrative'},
            {'name': 'Rise and Grind', 'description': 'Motivational hip-hop anthem'},
            {'name': 'Wordplay Master', 'description': 'Lyrical masterpiece'},
            {'name': 'Urban Stories', 'description': 'Real stories from the streets'},
        ]
        
        for idx, song in enumerate(songs_hiphop, 1):
            Candidate.objects.create(
                category=category2_2,
                name=song['name'],
                description=song['description'],
                order=idx
            )
        self.stdout.write(f'✓ Created 4 songs for {category2_2.name}')

        # Create a draft campaign
        campaign3 = VotingCampaign.objects.create(
            title='Best Music Video 2024',
            description='Vote for the most creative and visually stunning music video.',
            short_description='Upcoming campaign coming soon',
            status='draft',
            start_date=timezone.now() + timedelta(days=30),
            end_date=timezone.now() + timedelta(days=60)
        )
        self.stdout.write(f'✓ Created draft campaign: {campaign3.title}')

        self.stdout.write(
            self.style.SUCCESS('\n✅ Sample voting data created successfully!\n')
        )
        self.stdout.write(self.style.WARNING('Summary:'))
        self.stdout.write(f'  - Created 2 active campaigns and 1 draft campaign')
        self.stdout.write(f'  - Created 5 categories across campaigns')
        self.stdout.write(f'  - Created 12 total candidates')
        self.stdout.write(f'\nNext steps:')
        self.stdout.write(f'  1. Start the development server: python manage.py runserver')
        self.stdout.write(f'  2. Visit the voting page: http://127.0.0.1:8000/voting/')
        self.stdout.write(f'  3. Or access the admin: http://127.0.0.1:8000/admin/')
