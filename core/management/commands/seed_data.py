from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Brand, Testimonial, WhyChooseUs, SiteSettings, SocialLink
from products.models import Category, Product, ProductAttribute, ProductAttributeValue, FAQ, Review, ProductInquiry
from pages.models import Service, ServingArea


class Command(BaseCommand):
    help = 'Seed TechZone with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.HTTP_INFO('\n🌱  Seeding TechZone...\n'))

        # ── Site Settings ──────────────────────────────────────
        s = SiteSettings.get_settings()
        s.site_name = 'TechZone'; s.tagline = 'Your Premium Electronics Destination'
        s.phone = '+91 98765 43210'; s.whatsapp = '919876543210'
        s.email = 'hello@techzone.in'
        s.address = 'Shop No. 12, Electronics Market, Ring Road, Surat, Gujarat 395003'
        s.working_hours = 'Mon–Sat: 10am – 8pm'
        s.meta_description = 'Shop premium electronics at TechZone.'
        s.save()
        self.stdout.write(self.style.SUCCESS('  ✓ Site settings'))

        # ── Brands ─────────────────────────────────────────────
        brands_data = [
            ('Apple','#000000',True),('Samsung','#1428A0',True),('Sony','#000000',True),
            ('LG','#A50034',True),('OnePlus','#F5010C',True),('Dell','#007DB8',True),
            ('HP','#0096D6',True),('Lenovo','#E2231A',True),('Asus','#00539B',False),
            ('Xiaomi','#FF6900',True),('Realme','#FFD700',False),('boAt','#FF4D00',False),
            ('JBL','#FF0000',False),('Bose','#1A1A1A',True),('Canon','#CC0000',False),
            ('Nikon','#FFDD00',False),
        ]
        for name, color, featured in brands_data:
            Brand.objects.get_or_create(name=name, defaults={'is_featured': featured, 'is_active': True})
        self.stdout.write(self.style.SUCCESS('  ✓ Brands (16)'))

        # ── Categories ─────────────────────────────────────────
        cats_data = [
            {'name':'Mobiles','icon':'ti-device-mobile','color':'#2563eb','order':1,
             'description':'Explore the latest smartphones from top brands.',
             'meta_title':'Buy Mobiles Online | TechZone',
             'meta_description':'Shop latest smartphones at TechZone. Best prices on iPhones, Samsung, OnePlus.',
             'subs':[('Apple iPhones','ti-brand-apple','#000000'),('Samsung Galaxy','ti-device-mobile','#1428A0'),('Budget Phones','ti-device-mobile-dollar','#16a34a'),('5G Phones','ti-antenna','#7c3aed')]},
            {'name':'Laptops','icon':'ti-device-laptop','color':'#7c3aed','order':2,
             'description':'Powerful laptops for work, study and gaming.',
             'meta_title':'Buy Laptops Online | TechZone',
             'meta_description':'Find the best laptops at TechZone — MacBooks, Dell, HP, Lenovo.',
             'subs':[('MacBooks','ti-brand-apple','#000000'),('Business Laptops','ti-briefcase','#1d4ed8'),('Gaming Laptops','ti-device-gamepad-2','#dc2626'),('Budget Laptops','ti-device-laptop','#16a34a')]},
            {'name':'Accessories','icon':'ti-headphones','color':'#059669','order':3,
             'description':'Cases, chargers, cables and more.',
             'meta_title':'Mobile & Laptop Accessories | TechZone',
             'meta_description':'Shop accessories — cases, chargers, cables and more.',
             'subs':[('Phone Cases','ti-device-mobile','#2563eb'),('Chargers & Cables','ti-plug','#f59e0b'),('Keyboards & Mice','ti-keyboard','#7c3aed')]},
            {'name':'TVs','icon':'ti-device-tv','color':'#dc2626','order':4,
             'description':'Smart TVs, OLED, QLED from top brands.',
             'meta_title':'Buy Smart TVs | TechZone',
             'meta_description':'Best Smart TVs at TechZone — 4K OLED, QLED from Sony, Samsung, LG.',
             'subs':[('OLED TVs','ti-device-tv','#7c3aed'),('4K Smart TVs','ti-device-tv-old','#1d4ed8'),('Budget TVs','ti-device-tv','#16a34a')]},
            {'name':'Cameras','icon':'ti-camera','color':'#d97706','order':5,
             'description':'DSLR, mirrorless cameras from Canon, Nikon, Sony.',
             'meta_title':'Buy Cameras | TechZone',
             'meta_description':'Shop cameras at TechZone — DSLR, mirrorless from Canon, Nikon, Sony.',
             'subs':[('DSLR Cameras','ti-camera','#dc2626'),('Mirrorless','ti-camera-selfie','#2563eb'),('Action Cameras','ti-device-camera','#d97706')]},
            {'name':'Smart Watches','icon':'ti-device-watch','color':'#0891b2','order':6,
             'description':'Apple Watch, Samsung Galaxy Watch and more.',
             'meta_title':'Buy Smart Watches | TechZone',
             'meta_description':'Best smartwatches at TechZone.','subs':[]},
            {'name':'Audio Devices','icon':'ti-speakerphone','color':'#7c3aed','order':7,
             'description':'Headphones, earbuds, speakers from JBL, Sony, Bose.',
             'meta_title':'Buy Headphones & Speakers | TechZone',
             'meta_description':'Premium audio at TechZone.',
             'subs':[('Headphones','ti-headphones','#1d4ed8'),('Earbuds & TWS','ti-headset','#7c3aed'),('Bluetooth Speakers','ti-speakerphone','#d97706')]},
            {'name':'Gaming','icon':'ti-device-gamepad-2','color':'#dc2626','order':8,
             'description':'Consoles, controllers, headsets.',
             'meta_title':'Gaming Consoles & Accessories | TechZone',
             'meta_description':'Shop gaming at TechZone.',
             'subs':[('Consoles','ti-device-gamepad','#1d4ed8'),('Gaming Accessories','ti-device-gamepad-2','#dc2626')]},
            {'name':'Home Appliances','icon':'ti-home','color':'#059669','order':9,
             'description':'Smart home appliances for modern living.',
             'meta_title':'Home Appliances | TechZone',
             'meta_description':'Shop home appliances at TechZone.','subs':[]},
            {'name':'Networking','icon':'ti-router','color':'#0891b2','order':10,
             'description':'Routers, switches, networking accessories.',
             'meta_title':'Networking Devices | TechZone',
             'meta_description':'Buy networking equipment at TechZone.','subs':[]},
        ]
        for cd in cats_data:
            subs = cd.pop('subs')
            parent, _ = Category.objects.update_or_create(name=cd['name'], defaults={
                'icon': cd['icon'], 'color': cd['color'], 'order': cd['order'],
                'description': cd['description'], 'meta_title': cd.get('meta_title',''),
                'meta_description': cd.get('meta_description',''),
                'is_active': True, 'is_featured': True, 'show_in_nav': True,
            })
            for i, (sn, si, sc) in enumerate(subs):
                Category.objects.get_or_create(name=sn, parent=parent, defaults={
                    'icon': si, 'color': sc, 'is_active': True, 'show_in_nav': False, 'order': i,
                })
        self.stdout.write(self.style.SUCCESS('  ✓ Categories + sub-categories'))

        # ── Attributes ─────────────────────────────────────────
        attr_p, _ = ProductAttribute.objects.get_or_create(name='Processor')
        attr_r, _ = ProductAttribute.objects.get_or_create(name='RAM')
        attr_s, _ = ProductAttribute.objects.get_or_create(name='Storage')
        attr_d, _ = ProductAttribute.objects.get_or_create(name='Display')
        attr_b, _ = ProductAttribute.objects.get_or_create(name='Battery')
        attr_c, _ = ProductAttribute.objects.get_or_create(name='Camera')
        attr_os,_ = ProductAttribute.objects.get_or_create(name='Operating System')
        attr_cn,_ = ProductAttribute.objects.get_or_create(name='Connectivity')

        mob_cat   = Category.objects.filter(name='Mobiles').first()
        lap_cat   = Category.objects.filter(name='Laptops').first()
        aud_cat   = Category.objects.filter(name='Audio Devices').first()
        tv_cat    = Category.objects.filter(name='TVs').first()
        cam_cat   = Category.objects.filter(name='Cameras').first()
        apple     = Brand.objects.filter(name='Apple').first()
        samsung   = Brand.objects.filter(name='Samsung').first()
        dell      = Brand.objects.filter(name='Dell').first()
        sony      = Brand.objects.filter(name='Sony').first()
        oneplus   = Brand.objects.filter(name='OnePlus').first()
        canon     = Brand.objects.filter(name='Canon').first()
        lg        = Brand.objects.filter(name='LG').first()
        bose      = Brand.objects.filter(name='Bose').first()

        products_info = [
            {
                'name': 'iPhone 15 Pro Max', 'cat': mob_cat, 'brand': apple,
                'price': 134900, 'sale': 129900, 'featured': True, 'trending': True, 'new': True,
                'color': 'Black Titanium', 'stock': 15,
                'short': 'The most powerful iPhone with A17 Pro chip, titanium design, Action button, and 48MP triple camera.',
                'desc': '''The iPhone 15 Pro Max represents the pinnacle of smartphone engineering. Built with aerospace-grade titanium, it is lighter yet stronger than ever. The A17 Pro chip delivers desktop-class performance, enabling console-quality gaming and blazing-fast processing.\n\nThe camera system features a 48MP main sensor with second-generation sensor-shift OIS, a 12MP ultrawide, and a 12MP 5× optical zoom telephoto — the longest optical zoom ever in an iPhone. Shoot 4K 60fps ProRes video directly to external storage.\n\nThe Action button provides customisable one-touch access to your most-used features. USB 3 speeds via the USB-C port mean 20x faster data transfer than Lightning.''',
                'warranty': '1 Year Apple Warranty',
                'attrs': [(attr_p,'A17 Pro (3nm)'),(attr_r,'8 GB'),(attr_s,'256 GB'),(attr_d,'6.7" Super Retina XDR OLED'),(attr_b,'4422 mAh'),(attr_c,'48MP + 12MP + 12MP'),(attr_os,'iOS 17'),(attr_cn,'5G, Wi-Fi 6E, Bluetooth 5.3')],
                'faqs': [
                    ('Does it support 5G?','Yes, iPhone 15 Pro Max supports Sub-6GHz and mmWave 5G networks.'),
                    ('What is the warranty period?','It comes with a 1-year limited warranty from Apple, extendable with AppleCare+.'),
                    ('Does it have a headphone jack?','No, it uses USB-C. You can use USB-C earphones or a wireless pair.'),
                    ('Is it water resistant?','Yes, rated IP68 — up to 6 metres for 30 minutes.'),
                ],
                'reviews': [
                    ('Rahul Mehta', 5, 'Absolutely stunning!', 'The camera quality is unmatched. Photos are crisp even in low light. Battery easily lasts a full day of heavy use.', 'Titanium build, camera, performance', 'Price is high but worth it'),
                    ('Priya Shah', 5, 'Best iPhone ever', 'The 5x zoom is incredible. Action button is very handy. The display is gorgeous.', 'Display, zoom camera, build quality', 'Expensive'),
                    ('Amit Kumar', 4, 'Great phone, minor issues', 'Performance is top notch. The USB-C switch is welcome. Slightly heavy.', 'Speed, cameras, USB-C', 'A bit heavy'),
                ],
            },
            {
                'name': 'Samsung Galaxy S24 Ultra', 'cat': mob_cat, 'brand': samsung,
                'price': 129999, 'sale': 119999, 'featured': True, 'trending': True, 'new': True,
                'color': 'Titanium Black', 'stock': 20,
                'short': 'Ultimate Galaxy with built-in S Pen, 200MP camera, Galaxy AI, and titanium frame.',
                'desc': '''Galaxy S24 Ultra is the ultimate Android flagship. The built-in S Pen lets you write, sketch and translate on the go. Galaxy AI transforms how you communicate — Circle to Search, Live Translate, and Note Assist work across apps.\n\nThe pro-grade camera system packs a 200MP main sensor, 10MP 3× zoom, 50MP 5× zoom, and a 12MP ultrawide — giving you an unmatched photography toolkit in your pocket.''',
                'warranty': '1 Year Samsung Warranty',
                'attrs': [(attr_p,'Snapdragon 8 Gen 3'),(attr_r,'12 GB'),(attr_s,'256 GB'),(attr_d,'6.8" QHD+ Dynamic AMOLED 2X'),(attr_b,'5000 mAh'),(attr_c,'200MP + 10MP + 50MP + 12MP'),(attr_os,'Android 14 / One UI 6.1'),(attr_cn,'5G, Wi-Fi 7, Bluetooth 5.3')],
                'faqs': [
                    ('Does S Pen come in the box?','Yes, the S Pen is built into the phone and included out of the box.'),
                    ('Does it support wireless charging?','Yes, 15W wireless charging and 4.5W reverse wireless charging.'),
                    ('What AI features does it have?','Circle to Search, Live Translate, Chat Assist, Note Assist, and Generative Edit in Gallery.'),
                ],
                'reviews': [
                    ('Vikram Desai', 5, 'The Android king', 'S Pen is a game changer. AI features are surprisingly useful. Camera is insane.', 'S Pen, AI features, camera versatility', 'Very expensive'),
                    ('Sneha Joshi', 4, 'Powerful but big', 'Blazing fast performance. Galaxy AI features work great. A bit large for one-hand use.', 'Performance, camera, S Pen', 'Too big for small hands'),
                ],
            },
            {
                'name': 'OnePlus 12', 'cat': mob_cat, 'brand': oneplus,
                'price': 64999, 'sale': 59999, 'featured': True, 'trending': True, 'new': True,
                'color': 'Silky Black', 'stock': 25,
                'short': 'Flagship killer with Snapdragon 8 Gen 3, 100W charging, and Hasselblad cameras.',
                'desc': 'OnePlus 12 delivers true flagship performance at a more accessible price. The Snapdragon 8 Gen 3 chip paired with LPDDR5X RAM ensures snappy performance. The 100W SUPERVOOC charging fills from 0 to 100% in just 26 minutes.',
                'warranty': '1 Year OnePlus Warranty',
                'attrs': [(attr_p,'Snapdragon 8 Gen 3'),(attr_r,'12 GB LPDDR5X'),(attr_s,'256 GB UFS 4.0'),(attr_d,'6.82" LTPO AMOLED 120Hz'),(attr_b,'5400 mAh'),(attr_c,'50MP + 64MP + 48MP Hasselblad'),(attr_os,'Android 14 / OxygenOS 14'),(attr_cn,'5G, Wi-Fi 7, Bluetooth 5.4')],
                'faqs': [
                    ('How fast does it charge?','100W SUPERVOOC wired charging. 0–100% in about 26 minutes.'),
                    ('Does it have wireless charging?','Yes, 50W AIRVOOC wireless charging.'),
                ],
                'reviews': [
                    ('Aditya Patel', 5, 'Best value flagship!', '100W charging is phenomenal. Performance is top tier. Hasselblad cameras are very capable.', 'Charging speed, performance, value', 'No IP68 rating'),
                ],
            },
            {
                'name': 'Dell XPS 15 (2024)', 'cat': lap_cat, 'brand': dell,
                'price': 189990, 'sale': 179990, 'featured': True, 'trending': True, 'new': True,
                'color': 'Platinum Silver', 'stock': 8,
                'short': 'Premium 15.6" laptop with OLED display, Intel Core i9, RTX 4070, and all-day battery.',
                'desc': '''The Dell XPS 15 defines premium Windows laptops. The stunning 3.5K OLED display covers 100% DCI-P3 with factory calibration. Intel Core i9-13900H delivers 24 cores of processing power for the most demanding creative workloads.\n\nNVIDIA GeForce RTX 4070 handles 3D rendering, video editing and gaming with ease. The CNC-machined aluminium chassis is rigid yet elegant.''',
                'warranty': '1 Year Dell ProSupport',
                'attrs': [(attr_p,'Intel Core i9-13900H'),(attr_r,'32 GB DDR5'),(attr_s,'1 TB NVMe SSD'),(attr_d,'15.6" 3.5K OLED Touch'),(attr_b,'86 Wh'),(attr_os,'Windows 11 Home'),(attr_cn,'Wi-Fi 6E, Bluetooth 5.3, Thunderbolt 4')],
                'faqs': [
                    ('Does it have a dedicated GPU?','Yes, NVIDIA GeForce RTX 4070 with 8GB GDDR6.'),
                    ('Is the display touch-enabled?','Yes, the 3.5K OLED display is touch-enabled.'),
                    ('What ports does it have?','2× Thunderbolt 4, 1× USB-A, SD card reader, 3.5mm audio jack.'),
                ],
                'reviews': [
                    ('Neha Gupta', 5, 'Best Windows laptop', 'OLED display is jaw-dropping. Build quality is exceptional. Battery is reasonable for an OLED machine.', 'Display quality, build, performance', 'Expensive, gets warm under load'),
                    ('Ravi Sharma', 4, 'Powerful workstation', 'Handles video editing like a breeze. Display is colour accurate for my design work.', 'Performance, colour accuracy, keyboard', 'Heavy at 1.8kg'),
                ],
            },
            {
                'name': 'Dell Inspiron 15 3520', 'cat': lap_cat, 'brand': dell,
                'price': 65990, 'sale': 59990, 'featured': False, 'trending': False, 'new': True,
                'color': 'Carbon Black', 'stock': 18,
                'short': 'Reliable everyday laptop with Intel Core i5, fast SSD and Full HD display.',
                'desc': 'The Inspiron 15 3520 is the ideal everyday laptop for students and professionals. Intel Core i5-1235U delivers snappy performance for Office apps, browsing and light multimedia tasks.',
                'warranty': '1 Year Dell Warranty',
                'attrs': [(attr_p,'Intel Core i5-1235U'),(attr_r,'8 GB DDR4'),(attr_s,'512 GB SSD'),(attr_d,'15.6" FHD IPS Anti-glare'),(attr_b,'41 Wh'),(attr_os,'Windows 11 Home'),(attr_cn,'Wi-Fi 5, Bluetooth 5.1, USB-C')],
                'faqs': [
                    ('Can RAM be upgraded?','Yes, it has 2 SODIMM slots supporting up to 32 GB DDR4.'),
                    ('Does it have a backlit keyboard?','Yes, a single-colour backlit keyboard is included.'),
                ],
                'reviews': [
                    ('Kavya Nair', 4, 'Great budget laptop', 'Fast SSD boot time. Display is bright. Good value for the price.', 'SSD speed, value for money, display', 'Battery life average'),
                ],
            },
            {
                'name': 'Sony WH-1000XM5', 'cat': aud_cat, 'brand': sony,
                'price': 34990, 'sale': 29990, 'featured': True, 'trending': True, 'new': True,
                'color': 'Black', 'stock': 30,
                'short': 'Industry-leading noise cancellation headphones with 30-hour battery and crystal-clear calls.',
                'desc': '''Sony WH-1000XM5 sets the benchmark for noise-cancelling headphones. Eight microphones and two processors work together to analyse and cancel ambient noise in real time.\n\nMultipoint connection lets you pair with two devices simultaneously. Speak-to-Chat automatically pauses music when you start talking.''',
                'warranty': '1 Year Sony Warranty',
                'attrs': [(attr_d,'40mm Dynamic Driver'),(attr_b,'30 hours (ANC on)'),(attr_cn,'Bluetooth 5.2, NFC, 3.5mm jack'),(attr_os,'Sony Headphones Connect App')],
                'faqs': [
                    ('Does it support multipoint connection?','Yes, connect to two devices simultaneously.'),
                    ('How long does it take to charge?','About 3.5 hours for a full charge. 3 mins gives 3 hours of playback.'),
                    ('Does it work wired?','Yes, with the included 3.5mm cable.'),
                ],
                'reviews': [
                    ('Divya Mehta', 5, 'Best ANC headphones period', 'Noise cancellation is absolutely phenomenal. Comfort is great even after 6 hours of use.', 'ANC quality, comfort, battery life', 'Expensive'),
                    ('Suresh Patel', 5, 'Worth every rupee', 'Call quality is exceptional. My colleagues cannot tell I am in a noisy environment.', 'ANC, call quality, build', 'Carrying case could be bigger'),
                ],
            },
            {
                'name': 'Samsung 55" QLED 4K Smart TV', 'cat': tv_cat, 'brand': samsung,
                'price': 89990, 'sale': 79990, 'featured': True, 'trending': True, 'new': True,
                'color': 'Black', 'stock': 12,
                'short': 'Quantum dot 4K HDR TV with Tizen OS, Object Tracking Sound and Motion Xcelerator 120Hz.',
                'desc': 'The Samsung QLED 4K delivers vivid colours through Quantum Dot technology. 100% Colour Volume means colours stay true across all brightness levels.',
                'warranty': '1 Year Samsung Warranty',
                'attrs': [(attr_d,'55" QLED 4K UHD 120Hz'),(attr_p,'Quantum 4K Processor'),(attr_b,'N/A (Power supply)'),(attr_cn,'Wi-Fi, Bluetooth, 4× HDMI 2.1, 2× USB, ARC')],
                'faqs': [
                    ('Does it support HDR?','Yes — HDR10+, HLG, HDR10.'),
                    ('Is gaming mode available?','Yes, Auto Low Latency Mode (ALLM) with 4K@120Hz input.'),
                ],
                'reviews': [
                    ('Ankit Joshi', 5, 'Stunning picture quality', 'Colours pop off the screen. Gaming at 4K 120Hz is silky smooth.', 'Picture quality, gaming, smart features', 'Remote feels cheap'),
                ],
            },
            {
                'name': 'Sony 65" OLED Bravia XR A80L', 'cat': tv_cat, 'brand': sony,
                'price': 179990, 'sale': 159990, 'featured': True, 'trending': False, 'new': True,
                'color': 'Black', 'stock': 5,
                'short': 'Premium 65" OLED TV with Cognitive Processor XR, Acoustic Surface Audio+, and Google TV.',
                'desc': 'The Sony Bravia XR A80L uses Cognitive Processor XR to reproduce content the way the human eye sees it. Acoustic Surface Audio+ turns the entire screen into a speaker.',
                'warranty': '2 Year Sony Warranty',
                'attrs': [(attr_d,'65" 4K OLED 120Hz'),(attr_p,'Cognitive Processor XR'),(attr_b,'N/A'),(attr_cn,'Wi-Fi, Bluetooth, 4× HDMI 2.1, 3× USB, eARC')],
                'faqs': [
                    ('Does it have Google TV?','Yes, with built-in Chromecast and works with Google Assistant and Alexa.'),
                    ('What is Acoustic Surface Audio+?','Actuators behind the screen vibrate the panel to produce sound directly from the screen.'),
                ],
                'reviews': [
                    ('Pooja Verma', 5, 'Cinema at home', 'OLED blacks are absolutely perfect. Acoustic Surface Audio is mind-blowing. Best TV I have ever owned.', 'Picture quality, sound, smart features', 'Very expensive'),
                ],
            },
            {
                'name': 'iPhone 15', 'cat': mob_cat, 'brand': apple,
                'price': 79900, 'sale': None, 'featured': True, 'trending': False, 'new': True,
                'color': 'Blue', 'stock': 22,
                'short': 'iPhone 15 with Dynamic Island, USB-C, and 48MP main camera.',
                'desc': 'iPhone 15 brings Dynamic Island to the standard lineup. USB-C replaces Lightning. The 48MP main camera captures stunning detail.',
                'warranty': '1 Year Apple Warranty',
                'attrs': [(attr_p,'A16 Bionic'),(attr_r,'6 GB'),(attr_s,'128 GB'),(attr_d,'6.1" Super Retina XDR OLED'),(attr_b,'3877 mAh'),(attr_c,'48MP + 12MP'),(attr_os,'iOS 17'),(attr_cn,'5G, Wi-Fi 6, Bluetooth 5.3')],
                'faqs': [('Does it support MagSafe?','Yes, MagSafe for wireless charging and accessories.')],
                'reviews': [('Meena Shah', 4, 'Great upgrade from iPhone 12', 'Dynamic Island is useful. USB-C is finally here. Camera is excellent.', 'Camera, Dynamic Island, USB-C', 'Same design as iPhone 14')],
            },
            {
                'name': 'Samsung Galaxy A55 5G', 'cat': mob_cat, 'brand': samsung,
                'price': 38999, 'sale': 34999, 'featured': False, 'trending': True, 'new': True,
                'color': 'Awesome Navy', 'stock': 35,
                'short': 'Feature-packed mid-ranger with 50MP OIS camera, IP67 rating and 5000mAh battery.',
                'desc': 'Galaxy A55 5G punches above its weight with premium features including IP67 water resistance, 50MP OIS camera, and a 5000mAh battery.',
                'warranty': '1 Year Samsung Warranty',
                'attrs': [(attr_p,'Exynos 1480'),(attr_r,'8 GB'),(attr_s,'128 GB'),(attr_d,'6.6" FHD+ AMOLED 120Hz'),(attr_b,'5000 mAh'),(attr_c,'50MP OIS + 12MP + 5MP'),(attr_os,'Android 14 / One UI 6.1'),(attr_cn,'5G, Wi-Fi 6, Bluetooth 5.3')],
                'faqs': [('Is it water resistant?','Yes, IP67 rated — up to 1 metre for 30 minutes.')],
                'reviews': [('Rohan Kapoor', 4, 'Best mid-range phone', 'IP67 at this price is amazing. Camera produces great shots. Battery lasts 2 days easily.', 'IP67, camera, battery', 'Exynos chip gets slightly warm')],
            },
            {
                'name': 'Bose QuietComfort 45', 'cat': aud_cat, 'brand': bose,
                'price': 29900, 'sale': 24900, 'featured': False, 'trending': True, 'new': False,
                'color': 'White Smoke', 'stock': 14,
                'short': 'Premium over-ear headphones with world-class noise cancellation and 24-hour battery.',
                'desc': 'Bose QC45 combines legendary Bose noise cancellation with exceptional comfort. The lightweight design with plush ear cushions lets you wear them for hours.',
                'warranty': '1 Year Bose Warranty',
                'attrs': [(attr_d,'40mm TriPort acoustic architecture'),(attr_b,'24 hours'),(attr_cn,'Bluetooth 5.1, 2.5mm audio jack')],
                'faqs': [('Can I use them wired?','Yes, using the included 2.5mm to 3.5mm audio cable.')],
                'reviews': [('Sanjay Mehta', 4, 'Incredibly comfortable', 'These are the most comfortable headphones I have worn. ANC is excellent. Sound is warm and rich.', 'Comfort, ANC, build quality', 'No multipoint connection')],
            },
            {
                'name': 'Canon EOS R50', 'cat': cam_cat, 'brand': canon,
                'price': 74990, 'sale': 69990, 'featured': False, 'trending': False, 'new': True,
                'color': 'Black', 'stock': 9,
                'short': 'Compact mirrorless camera with 24.2MP sensor, 4K video and Dual Pixel CMOS AF.',
                'desc': 'The EOS R50 is Canon compact mirrorless for creators. The 24.2MP APS-C sensor delivers excellent image quality. Dual Pixel CMOS AF II tracks subjects with precision.',
                'warranty': '1 Year Canon Warranty',
                'attrs': [(attr_p,'DIGIC X processor'),(attr_s,'Dual SD slots'),(attr_d,'3" Vari-angle Touchscreen LCD'),(attr_b,'210 shots per charge'),(attr_c,'24.2MP APS-C CMOS'),(attr_cn,'Wi-Fi, Bluetooth, USB-C')],
                'faqs': [
                    ('Does it shoot 4K video?','Yes, uncropped 4K 30fps and 4K 60fps with crop.'),
                    ('What lenses are compatible?','All Canon RF and RF-S mount lenses. EF lenses via adapter.'),
                ],
                'reviews': [('Tanya Gupta', 5, 'Perfect beginner mirrorless', 'Image quality is superb. AF tracking is super reliable. Compact and lightweight for travel.', 'AF speed, image quality, size', 'Battery life could be better')],
            },
        ]

        for info in products_info:
            if not info['cat']: continue
            p, created = Product.objects.get_or_create(name=info['name'], defaults={
                'category': info['cat'], 'brand': info['brand'],
                'price': info['price'], 'sale_price': info['sale'],
                'stock': info['stock'], 'color': info['color'],
                'is_featured': info['featured'], 'is_trending': info['trending'],
                'is_new_arrival': info['new'], 'is_active': True,
                'short_description': info['short'], 'description': info['desc'],
                'warranty': info['warranty'],
                'meta_title': f'Buy {info["name"]} at Best Price | TechZone',
                'meta_description': info['short'],
            })
            if created:
                for attr, val in info.get('attrs', []):
                    ProductAttributeValue.objects.get_or_create(product=p, attribute=attr, defaults={'value': val})
                for i, (q, a) in enumerate(info.get('faqs', []), 1):
                    FAQ.objects.get_or_create(product=p, question=q, defaults={'answer': a, 'order': i, 'is_active': True})
                for rev_name, rating, title, content, pros, cons in info.get('reviews', []):
                    Review.objects.create(product=p, name=rev_name, email=f'{rev_name.lower().replace(" ",".")}@example.com',
                                         rating=rating, title=title, content=content, pros=pros, cons=cons,
                                         is_approved=True, is_verified_purchase=True)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Products ({len(products_info)}) with specs, FAQs, reviews'))

        # ── Why Choose Us ───────────────────────────────────────
        why_data = [
            ('ti-shield-check','Genuine Products','Every product is 100% authentic with official manufacturer warranty.'),
            ('ti-truck','Free Delivery','Same-day delivery in Surat. 2–3 days across Gujarat. Free above ₹999.'),
            ('ti-headset','Expert Support','Certified tech experts available Mon–Sat 10am–8pm.'),
            ('ti-refresh','Easy Returns','7-day hassle-free returns. No questions asked.'),
            ('ti-cash','Best Prices','Price-match guarantee. Found it cheaper? We will beat it.'),
            ('ti-award','Award Winning','Rated #1 electronics store in Gujarat for 3 consecutive years.'),
        ]
        for icon, title, desc in why_data:
            WhyChooseUs.objects.get_or_create(title=title, defaults={'icon': icon, 'description': desc, 'is_active': True})
        self.stdout.write(self.style.SUCCESS('  ✓ Why Choose Us'))

        # ── Testimonials ────────────────────────────────────────
        testimonials = [
            ('Amit Shah','Business Owner, Surat',5,'Bought a MacBook from TechZone. Best price and super-fast delivery. Highly recommend!'),
            ('Priya Patel','Student, Ahmedabad',5,'The team helped me choose the right laptop within my budget. Excellent service.'),
            ('Rahul Mehta','IT Professional, Vadodara',4,'Great selection and competitive pricing. Will definitely shop again.'),
            ('Sneha Joshi','Homemaker, Rajkot',5,'Bought a Samsung TV and the installation team was professional and on time.'),
            ('Vikram Desai','Engineer, Surat',5,'Amazing customer service. Very transparent and honest recommendations.'),
            ('Kavya Nair','Doctor, Gandhinagar',4,'Smooth buying experience. WhatsApp support is very convenient.'),
        ]
        for name, designation, rating, content in testimonials:
            Testimonial.objects.get_or_create(name=name, defaults={'designation': designation, 'rating': rating, 'content': content, 'is_active': True})
        self.stdout.write(self.style.SUCCESS('  ✓ Testimonials'))

        # ── Social Links ────────────────────────────────────────
        for platform, url in [('facebook','https://facebook.com/techzone'),('instagram','https://instagram.com/techzone'),
                               ('youtube','https://youtube.com/@techzone'),('whatsapp','https://wa.me/919876543210')]:
            SocialLink.objects.get_or_create(platform=platform, defaults={'url': url, 'is_active': True})
        self.stdout.write(self.style.SUCCESS('  ✓ Social links'))

        # ── Services ────────────────────────────────────────────
        services_data = [
            ('ti-bulb','Product Consultation','expert-consultation','Expert advice to help you choose the right electronics.'),
            ('ti-tool','Installation Services','installation','Professional installation of TVs, ACs, networking equipment.'),
            ('ti-device-mobile','Device Repair','repair','Fast and reliable repair for mobiles, laptops and tablets.'),
            ('ti-shield-checkered','Warranty Support','warranty','Hassle-free warranty claims and after-sales support.'),
            ('ti-package','Bulk Orders','bulk-orders','Special pricing for bulk electronics purchases.'),
            ('ti-home','Home Delivery','home-delivery','Fast doorstep delivery across Gujarat. Same-day in Surat.'),
            ('ti-building-community','Corporate Solutions','corporate','End-to-end electronics procurement for enterprises.'),
        ]
        for icon, title, slug, desc in services_data:
            Service.objects.get_or_create(slug=slug, defaults={'icon': icon, 'title': title, 'short_description': desc, 'is_active': True})
        self.stdout.write(self.style.SUCCESS('  ✓ Services'))

        # ── Serving Areas ───────────────────────────────────────
        cities = ['Ahmedabad','Surat','Vadodara','Rajkot','Gandhinagar','Anand','Nadiad',
                  'Sānand','Mehsana','Bharuch','Navsari','Vapi','Morbi','Junagadh','Bhavnagar']
        featured = {'Ahmedabad','Surat','Vadodara','Rajkot'}
        for city in cities:
            ServingArea.objects.get_or_create(city=city, defaults={'is_active': True, 'is_featured': city in featured})
        self.stdout.write(self.style.SUCCESS('  ✓ Serving areas'))

        # ── Admin User ──────────────────────────────────────────
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin','admin@techzone.com','admin123')
            self.stdout.write(self.style.SUCCESS('  ✓ Admin user  →  admin / admin123'))
        else:
            self.stdout.write('  ℹ  Admin user already exists')

        self.stdout.write(self.style.SUCCESS('\n✅  All data seeded!\n'))
        self.stdout.write(self.style.HTTP_INFO('  Admin: http://localhost:8000/admin/  (admin / admin123)'))
        self.stdout.write(self.style.HTTP_INFO('  Site:  http://localhost:8000/\n'))
