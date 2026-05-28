"""
Management command to seed full sample data.
Run: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Brand, Testimonial, WhyChooseUs, SiteSettings, SocialLink
from products.models import Category, Product, ProductAttribute, ProductAttributeValue, FAQ, Review
from pages.models import Service, ServingArea


class Command(BaseCommand):
    help = 'Seed database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.HTTP_INFO('Seeding TechZone sample data...\n'))

        # ── Site Settings ───────────────────────────────────────────
        s = SiteSettings.get_settings()
        s.site_name     = 'TechZone'
        s.tagline       = 'Your Premium Electronics Destination'
        s.phone         = '+91 98765 43210'
        s.whatsapp      = '919876543210'
        s.email         = 'hello@techzone.in'
        s.address       = 'Shop No. 12, Electronics Market, Ring Road, Surat, Gujarat 395003'
        s.working_hours = 'Mon–Sat: 10am – 8pm'
        s.meta_description = 'Shop premium electronics at TechZone — mobiles, laptops, TVs, cameras and more at best prices in Gujarat.'
        s.save()
        self.stdout.write(self.style.SUCCESS('✓ Site settings'))

        # ── Brands ──────────────────────────────────────────────────
        brands_data = [
            ('Apple','#000000',True), ('Samsung','#1428A0',True), ('Sony','#000000',True),
            ('LG','#A50034',True), ('OnePlus','#F5010C',True), ('Dell','#007DB8',True),
            ('HP','#0096D6',True), ('Lenovo','#E2231A',True), ('Asus','#00539B',False),
            ('Xiaomi','#FF6900',True), ('Realme','#FFD700',False), ('boAt','#FF4D00',False),
            ('JBL','#FF0000',False), ('Bose','#1A1A1A',True), ('Canon','#CC0000',False),
            ('Nikon','#FFDD00',False),
        ]
        for name, color, featured in brands_data:
            Brand.objects.get_or_create(name=name, defaults={
                'is_featured': featured, 'is_active': True,
            })
        self.stdout.write(self.style.SUCCESS('✓ Brands'))

        # ── Categories with subcategories, colors, SEO ──────────────
        cats = [
            {
                'name': 'Mobiles', 'icon': 'ti-device-mobile', 'color': '#2563eb', 'order': 1,
                'description': 'Explore the latest smartphones from top brands — Apple, Samsung, OnePlus and more.',
                'meta_title': 'Buy Mobiles Online — Best Prices | TechZone',
                'meta_description': 'Shop the latest smartphones at TechZone. Best prices on iPhones, Samsung Galaxy, OnePlus and more.',
                'subs': [
                    ('Apple iPhones', 'ti-brand-apple', '#000000'),
                    ('Samsung Galaxy', 'ti-device-mobile', '#1428A0'),
                    ('Budget Phones', 'ti-device-mobile-dollar', '#16a34a'),
                    ('5G Phones', 'ti-antenna', '#7c3aed'),
                ],
            },
            {
                'name': 'Laptops', 'icon': 'ti-device-laptop', 'color': '#7c3aed', 'order': 2,
                'description': 'Powerful laptops for work, study and gaming from Dell, HP, Apple and more.',
                'meta_title': 'Buy Laptops Online — Best Prices | TechZone',
                'meta_description': 'Find the best laptops at TechZone. MacBooks, Dell XPS, HP, Lenovo and gaming laptops at great prices.',
                'subs': [
                    ('MacBooks', 'ti-brand-apple', '#000000'),
                    ('Business Laptops', 'ti-briefcase', '#1d4ed8'),
                    ('Gaming Laptops', 'ti-device-gamepad-2', '#dc2626'),
                    ('Budget Laptops', 'ti-device-laptop', '#16a34a'),
                ],
            },
            {
                'name': 'Accessories', 'icon': 'ti-headphones', 'color': '#059669', 'order': 3,
                'description': 'Cases, chargers, cables, screen protectors and more accessories for all your devices.',
                'meta_title': 'Mobile & Laptop Accessories | TechZone',
                'meta_description': 'Shop mobile and laptop accessories — cases, chargers, cables, keyboards, mice and more.',
                'subs': [
                    ('Phone Cases', 'ti-device-mobile', '#2563eb'),
                    ('Chargers & Cables', 'ti-plug', '#f59e0b'),
                    ('Keyboards & Mice', 'ti-keyboard', '#7c3aed'),
                    ('Screen Protectors', 'ti-device-mobile-check', '#059669'),
                ],
            },
            {
                'name': 'TVs', 'icon': 'ti-device-tv', 'color': '#dc2626', 'order': 4,
                'description': 'Smart TVs, OLED, QLED and LED TVs from Sony, Samsung, LG and more.',
                'meta_title': 'Buy Smart TVs Online | TechZone',
                'meta_description': 'Best Smart TVs at TechZone — 4K OLED, QLED, LED TVs from Sony, Samsung, LG.',
                'subs': [
                    ('OLED TVs', 'ti-device-tv', '#7c3aed'),
                    ('4K Smart TVs', 'ti-device-tv-old', '#1d4ed8'),
                    ('Budget TVs', 'ti-device-tv', '#16a34a'),
                ],
            },
            {
                'name': 'Cameras', 'icon': 'ti-camera', 'color': '#d97706', 'order': 5,
                'description': 'DSLR, mirrorless and point-and-shoot cameras from Canon, Nikon, Sony.',
                'meta_title': 'Buy Cameras Online | TechZone',
                'meta_description': 'Shop cameras at TechZone — DSLR, mirrorless, action cameras from Canon, Nikon, Sony.',
                'subs': [
                    ('DSLR Cameras', 'ti-camera', '#dc2626'),
                    ('Mirrorless', 'ti-camera-selfie', '#2563eb'),
                    ('Action Cameras', 'ti-device-camera', '#d97706'),
                ],
            },
            {
                'name': 'Smart Watches', 'icon': 'ti-device-watch', 'color': '#0891b2', 'order': 6,
                'description': 'Apple Watch, Samsung Galaxy Watch and other smartwatches for fitness and productivity.',
                'meta_title': 'Buy Smart Watches | TechZone',
                'meta_description': 'Best smartwatches at TechZone — Apple Watch, Samsung Galaxy Watch and fitness trackers.',
                'subs': [],
            },
            {
                'name': 'Audio Devices', 'icon': 'ti-speakerphone', 'color': '#7c3aed', 'order': 7,
                'description': 'Headphones, earbuds, speakers and soundbars from JBL, Sony, Bose and more.',
                'meta_title': 'Buy Headphones & Speakers | TechZone',
                'meta_description': 'Premium audio at TechZone — headphones, earbuds, Bluetooth speakers from Sony, JBL, Bose.',
                'subs': [
                    ('Headphones', 'ti-headphones', '#1d4ed8'),
                    ('Earbuds & TWS', 'ti-headset', '#7c3aed'),
                    ('Bluetooth Speakers', 'ti-speakerphone', '#d97706'),
                ],
            },
            {
                'name': 'Gaming', 'icon': 'ti-device-gamepad-2', 'color': '#dc2626', 'order': 8,
                'description': 'Gaming consoles, controllers, headsets and accessories for all platforms.',
                'meta_title': 'Gaming Consoles & Accessories | TechZone',
                'meta_description': 'Shop gaming at TechZone — consoles, controllers, gaming chairs, headsets.',
                'subs': [
                    ('Consoles', 'ti-device-gamepad', '#1d4ed8'),
                    ('Gaming Accessories', 'ti-device-gamepad-2', '#dc2626'),
                ],
            },
            {
                'name': 'Home Appliances', 'icon': 'ti-home', 'color': '#059669', 'order': 9,
                'description': 'Smart home appliances from trusted brands for modern living.',
                'meta_title': 'Home Appliances | TechZone',
                'meta_description': 'Shop home appliances at TechZone — ACs, refrigerators, washing machines and more.',
                'subs': [],
            },
            {
                'name': 'Networking', 'icon': 'ti-router', 'color': '#0891b2', 'order': 10,
                'description': 'Routers, switches, range extenders and networking accessories.',
                'meta_title': 'Networking Devices | TechZone',
                'meta_description': 'Buy routers, switches and networking equipment at TechZone.',
                'subs': [],
            },
        ]

        for cat_data in cats:
            subs = cat_data.pop('subs')
            parent, _ = Category.objects.update_or_create(
                name=cat_data['name'],
                defaults={
                    'icon':             cat_data['icon'],
                    'color':            cat_data['color'],
                    'order':            cat_data['order'],
                    'description':      cat_data['description'],
                    'meta_title':       cat_data.get('meta_title', ''),
                    'meta_description': cat_data.get('meta_description', ''),
                    'is_active':        True,
                    'is_featured':      True,
                    'show_in_nav':      True,
                }
            )
            for i, (sub_name, sub_icon, sub_color) in enumerate(subs):
                Category.objects.get_or_create(
                    name=sub_name, parent=parent,
                    defaults={
                        'icon': sub_icon, 'color': sub_color,
                        'is_active': True, 'is_featured': False,
                        'show_in_nav': False, 'order': i,
                    }
                )
        self.stdout.write(self.style.SUCCESS('✓ Categories + sub-categories'))

        # ── Products ────────────────────────────────────────────────
        mobile_cat = Category.objects.filter(name='Mobiles').first()
        laptop_cat = Category.objects.filter(name='Laptops').first()
        audio_cat  = Category.objects.filter(name='Audio Devices').first()
        tv_cat     = Category.objects.filter(name='TVs').first()
        apple   = Brand.objects.filter(name='Apple').first()
        samsung = Brand.objects.filter(name='Samsung').first()
        dell    = Brand.objects.filter(name='Dell').first()
        sony    = Brand.objects.filter(name='Sony').first()
        oneplus = Brand.objects.filter(name='OnePlus').first()

        products_data = [
            # (name, cat, brand, price, sale_price, featured, trending, new_arrival, desc, color)
            ('iPhone 15 Pro Max', mobile_cat, apple, 134900, 129900, True, True, True, 'The most powerful iPhone ever with the A17 Pro chip, titanium design and Action button.', 'Black Titanium'),
            ('iPhone 15', mobile_cat, apple, 79900, None, True, False, True, 'The new iPhone 15 with Dynamic Island, USB-C and 48MP camera.', 'Blue'),
            ('Samsung Galaxy S24 Ultra', mobile_cat, samsung, 129999, 119999, True, True, True, 'The ultimate Galaxy with built-in S Pen, 200MP camera and AI features.', 'Titanium Black'),
            ('Samsung Galaxy A55 5G', mobile_cat, samsung, 38999, 34999, False, True, True, 'Feature-packed mid-ranger with 50MP OIS camera and IP67 rating.', 'Awesome Navy'),
            ('OnePlus 12', mobile_cat, oneplus, 64999, 59999, True, True, True, 'Flagship killer with Snapdragon 8 Gen 3, 50W wireless charging.', 'Silky Black'),
            ('Dell XPS 15', laptop_cat, dell, 189990, 179990, True, True, True, 'Premium 15" laptop with OLED display, Intel Core i9 and RTX 4070.', 'Platinum Silver'),
            ('Dell Inspiron 15 3520', laptop_cat, dell, 65990, 59990, False, False, True, 'Reliable everyday laptop for work and study with Intel Core i5.', 'Carbon Black'),
            ('Sony WH-1000XM5', audio_cat, sony, 34990, 29990, True, True, True, 'Industry-leading noise cancellation headphones with 30hr battery.', 'Black'),
            ('Samsung 55" QLED 4K', tv_cat, samsung, 89990, 79990, True, True, True, 'Quantum dot technology for vivid 4K HDR experience with smart TV features.', 'Black'),
            ('Sony 65" OLED 4K', tv_cat, sony, 179990, 159990, True, False, True, 'Breathtaking OLED display with Acoustic Surface Audio+ technology.', 'Black'),
        ]

        attr_processor, _ = ProductAttribute.objects.get_or_create(name='Processor')
        attr_ram, _       = ProductAttribute.objects.get_or_create(name='RAM')
        attr_storage, _   = ProductAttribute.objects.get_or_create(name='Storage')
        attr_display, _   = ProductAttribute.objects.get_or_create(name='Display')
        attr_battery, _   = ProductAttribute.objects.get_or_create(name='Battery')
        attr_camera, _    = ProductAttribute.objects.get_or_create(name='Camera')

        spec_map = {
            'iPhone 15 Pro Max':      [(attr_processor,'A17 Pro'),(attr_ram,'8GB'),(attr_storage,'256GB'),(attr_display,'6.7" Super Retina XDR'),(attr_battery,'4422mAh'),(attr_camera,'48MP + 12MP + 12MP')],
            'Samsung Galaxy S24 Ultra':[(attr_processor,'Snapdragon 8 Gen 3'),(attr_ram,'12GB'),(attr_storage,'256GB'),(attr_display,'6.8" QHD+ AMOLED'),(attr_battery,'5000mAh'),(attr_camera,'200MP + 10MP + 50MP')],
            'Dell XPS 15':            [(attr_processor,'Intel Core i9-13900H'),(attr_ram,'32GB DDR5'),(attr_storage,'1TB NVMe SSD'),(attr_display,'15.6" OLED 3.5K'),(attr_battery,'86Wh')],
        }

        for name, cat, brand, price, sale_price, featured, trending, new_arrival, desc, color in products_data:
            if not cat: continue
            p, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'category': cat, 'brand': brand, 'price': price,
                    'sale_price': sale_price, 'stock': 20 + (price % 17),
                    'is_featured': featured, 'is_trending': trending,
                    'is_new_arrival': new_arrival, 'is_active': True,
                    'short_description': desc,
                        'color': color,
                    'warranty': '1 Year Manufacturer Warranty',
                    'meta_title': f'Buy {name} at Best Price | TechZone',
                    'meta_description': f'{desc} Available at TechZone with free delivery.',
                }
            )
            if created:
                for attr, val in spec_map.get(name, []):
                    ProductAttributeValue.objects.create(product=p, attribute=attr, value=val)
                FAQ.objects.create(product=p, question=f'Does {name} come with warranty?',
                                   answer='Yes, it includes a 1-year manufacturer warranty covering manufacturing defects.', order=1)
                FAQ.objects.create(product=p, question='Is free delivery available?',
                                   answer='Yes, free delivery is available on orders above ₹999 across Gujarat.', order=2)
                Review.objects.create(product=p, name='Verified Buyer', email='buyer@example.com',
                                      rating=5, title='Excellent product!',
                                      content='Really happy with my purchase. Fast delivery and great quality.',
                                      is_approved=True, is_verified_purchase=True)
        self.stdout.write(self.style.SUCCESS('✓ Products'))

        # ── Why Choose Us ────────────────────────────────────────────
        why_data = [
            ('ti-shield-check', 'Genuine Products', 'Every product is 100% authentic with official manufacturer warranty. We are authorised dealers for all major brands.'),
            ('ti-truck', 'Fast Delivery', 'Same-day delivery in Surat. 2–3 days across Gujarat. Free delivery above ₹999.'),
            ('ti-headset', 'Expert Support', 'Certified tech experts available Mon–Sat to help you choose the perfect electronics.'),
            ('ti-refresh', 'Easy Returns', '7-day hassle-free returns on all products. No questions asked.'),
            ('ti-cash', 'Best Prices', 'Price-match guarantee. If you find it cheaper elsewhere, we will beat it.'),
            ('ti-award', 'Award Winning', 'Rated #1 electronics store in Gujarat for 3 consecutive years by our customers.'),
        ]
        for icon, title, desc in why_data:
            WhyChooseUs.objects.get_or_create(title=title, defaults={'icon': icon, 'description': desc, 'is_active': True})
        self.stdout.write(self.style.SUCCESS('✓ Why Choose Us'))

        # ── Testimonials ─────────────────────────────────────────────
        testimonials = [
            ('Amit Shah', 'Business Owner, Surat', 5, 'Bought a MacBook Pro from TechZone. Best price in the market and delivery was super fast. Highly recommend!'),
            ('Priya Patel', 'Student, Ahmedabad', 5, 'Excellent service and genuine products. The team helped me choose the right laptop for my studies within my budget.'),
            ('Rahul Mehta', 'IT Professional, Vadodara', 4, 'Great selection, competitive pricing and knowledgeable staff. Will definitely shop here again.'),
            ('Sneha Joshi', 'Homemaker, Rajkot', 5, 'Bought a Samsung smart TV and the installation team was professional and on time. Excellent experience!'),
            ('Vikram Desai', 'Engineer, Surat', 5, 'Amazing customer service. They helped me find the perfect laptop within my budget. Very transparent.'),
            ('Kavya Nair', 'Doctor, Gandhinagar', 4, 'Smooth buying experience. WhatsApp support is very convenient for quick queries. Great store!'),
        ]
        for name, designation, rating, content in testimonials:
            Testimonial.objects.get_or_create(name=name, defaults={'designation': designation, 'rating': rating, 'content': content, 'is_active': True})
        self.stdout.write(self.style.SUCCESS('✓ Testimonials'))

        # ── Social Links ─────────────────────────────────────────────
        for platform, url in [('facebook','https://facebook.com/techzone'),('instagram','https://instagram.com/techzone'),
                               ('youtube','https://youtube.com/@techzone'),('whatsapp','https://wa.me/919876543210')]:
            SocialLink.objects.get_or_create(platform=platform, defaults={'url': url, 'is_active': True})
        self.stdout.write(self.style.SUCCESS('✓ Social links'))

        # ── Services ─────────────────────────────────────────────────
        services_data = [
            ('ti-bulb','Product Consultation','expert-consultation','Expert advice to help you choose the right electronics for your needs and budget.'),
            ('ti-tool','Installation Services','installation','Professional installation of TVs, ACs, and networking equipment at your home or office.'),
            ('ti-device-mobile','Device Repair','repair','Fast and reliable repair for mobiles, laptops, tablets and all electronics.'),
            ('ti-shield-checkered','Warranty Support','warranty','Hassle-free warranty claims and after-sales support for all products.'),
            ('ti-package','Bulk Orders','bulk-orders','Special pricing and a dedicated manager for bulk electronics purchases.'),
            ('ti-home','Home Delivery','home-delivery','Fast and safe doorstep delivery with real-time tracking across Gujarat.'),
            ('ti-building-community','Corporate Solutions','corporate','End-to-end electronics procurement and IT support for enterprises.'),
        ]
        for icon, title, slug, desc in services_data:
            Service.objects.get_or_create(slug=slug, defaults={'icon': icon, 'title': title, 'short_description': desc, 'is_active': True})
        self.stdout.write(self.style.SUCCESS('✓ Services'))

        # ── Serving Areas ─────────────────────────────────────────────
        cities = ['Ahmedabad','Surat','Vadodara','Rajkot','Gandhinagar','Anand','Nadiad',
                  'Sānand','Mehsana','Bharuch','Navsari','Vapi','Morbi','Junagadh','Bhavnagar']
        featured_cities = {'Ahmedabad','Surat','Vadodara','Rajkot'}
        for city in cities:
            ServingArea.objects.get_or_create(city=city, defaults={'is_active': True, 'is_featured': city in featured_cities})
        self.stdout.write(self.style.SUCCESS('✓ Serving areas'))

        # ── Admin User ────────────────────────────────────────────────
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@techzone.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('✓ Admin user created  →  admin / admin123'))
        else:
            self.stdout.write('  Admin user already exists')

        self.stdout.write(self.style.SUCCESS('\n✅  All sample data seeded successfully!'))
        self.stdout.write(self.style.HTTP_INFO('Run:   python manage.py runserver'))
        self.stdout.write(self.style.HTTP_INFO('Admin: http://localhost:8000/admin/   (admin / admin123)'))
        self.stdout.write(self.style.HTTP_INFO('Site:  http://localhost:8000/'))
