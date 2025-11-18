from django.core.management.base import BaseCommand
from bills.models import Category

class Command(BaseCommand):
    help = 'Setup default categories'
    
    def handle(self, *args, **options):
        default_categories = [
            ('Food & Dining', 'FOOD', 'restaurant,cafe,food,dining,lunch,dinner,breakfast,mcdonalds,starbucks,subway', '#FF6B6B'),
            ('Transportation', 'TRANSPORT', 'gas,fuel,taxi,uber,lyft,bus,train,parking,shell,exxon,chevron', '#4ECDC4'),
            ('Shopping', 'SHOPPING', 'store,shop,market,walmart,target,amazon,retail,costco', '#45B7D1'),
            ('Utilities', 'UTILITIES', 'electric,gas,water,internet,phone,utility,bill,payment', '#96CEB4'),
            ('Healthcare', 'HEALTHCARE', 'hospital,clinic,doctor,pharmacy,medical,health,cvs,walgreens', '#FFEAA7'),
            ('Entertainment', 'ENTERTAINMENT', 'movie,netflix,spotify,game,entertainment,theater', '#DDA0DD'),
            ('Business', 'BUSINESS', 'office,supplies,fedex,ups,business,meeting,work', '#98D8C8'),
            ('Travel', 'TRAVEL', 'hotel,airline,airbnb,flight,travel,vacation,trip', '#F7DC6F'),
            ('Education', 'EDUCATION', 'school,university,course,book,education,learning', '#BB8FCE'),
            ('Other', 'OTHER', '', '#BDC3C7'),
        ]
        
        for name, category_type, keywords, color in default_categories:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={
                    'type': category_type,
                    'keywords': keywords,
                    'color': color,
                    'description': f'Default {name} category'
                }
            )
            if created:
                self.stdout.write(f'Created category: {name}')
            else:
                self.stdout.write(f'Category already exists: {name}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully setup default categories!')
        )