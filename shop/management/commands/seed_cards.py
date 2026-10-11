"""Seed the store with sample cards and generated placeholder card art."""
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from shop.models import Card

# emblem key, palette (bg1, bg2, accent)
OP_PALETTE = ('#e53e3e', '#7b1e1e', '#f6ad3b')
DI_PALETTE = ('#2b6cb0', '#1a365d', '#9f7aea')

EMBLEMS = {
    'skull': '<circle cx="0" cy="-8" r="30" fill="#fff"/><ellipse cx="0" cy="24" rx="20" ry="10" fill="#fff"/><circle cx="-11" cy="-10" r="7" fill="{bg2}"/><circle cx="11" cy="-10" r="7" fill="{bg2}"/><path d="M-4 4 L0 12 L4 4 Z" fill="{bg2}"/>',
    'hat': '<ellipse cx="0" cy="10" rx="46" ry="12" fill="#f2cf66" stroke="#c9a63e" stroke-width="3"/><path d="M-30 8 Q-28 -26 0 -26 Q28 -26 30 8 Q0 18 -30 8 Z" fill="#f2cf66" stroke="#c9a63e" stroke-width="3"/><path d="M-29 4 Q0 14 29 4 L29 10 Q0 20 -29 10 Z" fill="#e53e3e"/>',
    'swords': '<path d="M-30 -30 L26 26 M-30 26 L26 -30" stroke="#fff" stroke-width="8" stroke-linecap="round"/><circle cx="0" cy="-2" r="9" fill="{accent}"/>',
    'wave': '<path d="M-40 16 Q-24 -22 -2 6 Q4 -30 24 -2 Q34 -16 40 -4 L40 28 L-40 28 Z" fill="#fff"/>',
    'anchor': '<circle cx="0" cy="-24" r="9" fill="none" stroke="#fff" stroke-width="6"/><line x1="0" y1="-15" x2="0" y2="26" stroke="#fff" stroke-width="6"/><path d="M-26 8 Q-22 30 0 30 Q22 30 26 8 L16 12 Q16 22 0 22 Q-16 22 -16 12 Z" fill="#fff"/><line x1="-14" y1="-4" x2="14" y2="-4" stroke="#fff" stroke-width="6"/>',
    'bolt': '<path d="M6 -34 L-16 4 L-2 4 L-8 34 L18 -6 L2 -6 Z" fill="#ffe066" stroke="#c9a63e" stroke-width="2"/>',
    'sun': '<circle cx="0" cy="0" r="18" fill="#ffe066"/><g stroke="#ffe066" stroke-width="5">{rays}</g>'.format(rays=''.join(f'<line x1="0" y1="0" x2="{x}" y2="{y}"/>' for x, y in [(0, -34), (24, -24), (34, 0), (24, 24), (0, 34), (-24, 24), (-34, 0), (-24, -24)])),
    'crown': '<path d="M-30 16 L-30 -8 L-14 4 L0 -20 L14 4 L30 -8 L30 16 Z" fill="#ffe066" stroke="#c9a63e" stroke-width="3"/><circle cx="-30" cy="-12" r="4" fill="#ffe066"/><circle cx="0" cy="-24" r="4" fill="#ffe066"/><circle cx="30" cy="-12" r="4" fill="#ffe066"/>',
    'ears': '<circle cx="0" cy="6" r="24" fill="#fff"/><circle cx="-22" cy="-16" r="13" fill="#fff"/><circle cx="22" cy="-16" r="13" fill="#fff"/>',
    'snowflake': '<g stroke="#fff" stroke-width="5" stroke-linecap="round">' + ''.join(f'<line x1="0" y1="0" x2="{x}" y2="{y}"/>' for x, y in [(0, -30), (26, -15), (26, 15), (0, 30), (-26, 15), (-26, -15)]) + '</g><circle cx="0" cy="0" r="6" fill="#fff"/>',
    'paw': '<ellipse cx="0" cy="10" rx="18" ry="14" fill="#fff"/><circle cx="-18" cy="-8" r="7" fill="#fff"/><circle cx="-6" cy="-16" r="7" fill="#fff"/><circle cx="6" cy="-16" r="7" fill="#fff"/><circle cx="18" cy="-8" r="7" fill="#fff"/>',
    'star': '<path d="M0 -32 L9 -10 L32 -10 L14 4 L21 28 L0 14 L-21 28 L-14 4 L-32 -10 L-9 -10 Z" fill="#ffe066" stroke="#c9a63e" stroke-width="2"/>',
    'trident': '<line x1="0" y1="-30" x2="0" y2="30" stroke="#fff" stroke-width="6"/><path d="M-18 -30 Q-18 -10 0 -12 Q18 -10 18 -30" fill="none" stroke="#fff" stroke-width="6"/><path d="M-4 -34 L0 -44 L4 -34 Z" fill="#fff"/>',
    'lamp': '<path d="M-24 6 Q-24 -10 0 -10 Q24 -10 24 6 Q12 16 -12 16 Q-20 14 -24 6 Z" fill="#ffe066" stroke="#c9a63e" stroke-width="3"/><path d="M22 -2 Q38 -8 34 -20" fill="none" stroke="#c9a63e" stroke-width="4"/><ellipse cx="0" cy="-14" rx="8" ry="4" fill="#ffe066"/><path d="M0 -18 Q-4 -30 6 -34" fill="none" stroke="#fff" stroke-width="3"/>',
    'castle': '<rect x="-28" y="-4" width="56" height="32" fill="#fff"/><rect x="-20" y="-22" width="10" height="20" fill="#fff"/><rect x="10" y="-22" width="10" height="20" fill="#fff"/><rect x="-6" y="-32" width="12" height="30" fill="#fff"/><path d="M-8 -32 L0 -44 L8 -32 Z" fill="#fff"/><rect x="-4" y="14" width="8" height="14" fill="{bg2}"/>',
}

CARD_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 400" width="300" height="400">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{bg1}"/><stop offset="100%" stop-color="{bg2}"/>
    </linearGradient>
    <pattern id="dots" width="14" height="14" patternUnits="userSpaceOnUse">
      <circle cx="4" cy="4" r="1.6" fill="#ffffff" opacity="0.18"/>
      <circle cx="11" cy="11" r="1.6" fill="#ffffff" opacity="0.18"/>
    </pattern>
  </defs>
  <rect width="300" height="400" rx="16" fill="url(#bg)"/>
  <rect width="300" height="400" rx="16" fill="url(#dots)"/>
  <rect x="10" y="10" width="280" height="380" rx="12" fill="none" stroke="{accent}" stroke-width="4"/>
  <rect x="22" y="52" width="256" height="230" rx="10" fill="#00000033" stroke="{accent}" stroke-width="2"/>
  <g stroke="#ffffff" stroke-width="2" opacity="0.35">
    <line x1="30" y1="70" x2="270" y2="60"/><line x1="30" y1="100" x2="270" y2="88"/>
    <line x1="30" y1="240" x2="270" y2="252"/><line x1="30" y1="268" x2="270" y2="276"/>
  </g>
  <g transform="translate(150,167) scale(1.6)">{emblem}</g>
  <rect x="22" y="20" width="256" height="26" rx="8" fill="#00000055"/>
  <text x="150" y="39" text-anchor="middle" font-family="Impact, Arial Black, sans-serif" font-size="17" fill="#ffffff" letter-spacing="1">{name}</text>
  <rect x="22" y="294" width="256" height="66" rx="10" fill="#ffffffee"/>
  <text x="34" y="316" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#1a1a2e">{franchise} · {rarity}</text>
  <text x="34" y="334" font-family="Arial, sans-serif" font-size="11" fill="#333">{line1}</text>
  <text x="34" y="350" font-family="Arial, sans-serif" font-size="11" fill="#333">{line2}</text>
  <circle cx="262" cy="374" r="10" fill="{accent}"/>
  <text x="150" y="379" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" fill="#ffffffaa">CARD HEROES · {number}</text>
</svg>"""

CARDS = [
    # name, franchise, rarity, set, number, price, stock, featured, emblem, description
    ('Monkey D. Luffy — Gear Five', 'OP', 'SEC', 'Romance Dawn', 'OP01-001', 249.99, 2, True, 'hat',
     'The Warrior of Liberation awakens. Alt-art secret rare of the future Pirate King at his most joyful and most powerful.'),
    ('Roronoa Zoro — Three Sword Style', 'OP', 'SR', 'Romance Dawn', 'OP01-025', 89.99, 4, True, 'swords',
     'Santoryu master and first mate. Nothing happened. Super rare with foil blade detailing.'),
    ('Nami — Weather Sorceress', 'OP', 'R', 'Paramount War', 'OP02-036', 34.50, 6, False, 'bolt',
     'The Straw Hats\' navigator calls down thunderbolts with the Clima-Tact. Rare holo print.'),
    ('Sanji — Black Leg', 'OP', 'SR', 'Paramount War', 'OP02-041', 74.00, 3, False, 'sun',
     'The cook whose kicks burn like the sun. Diable Jambe alt-art, mint from a sealed case.'),
    ('Tony Tony Chopper — Cotton Candy Lover', 'OP', 'U', 'Pillars of Strength', 'OP03-014', 12.99, 10, False, 'paw',
     'The crew\'s doctor in Brain Point. Being called a raccoon dog not included. Uncommon.'),
    ('Nico Robin — Devil Child', 'OP', 'R', 'Pillars of Strength', 'OP03-028', 42.00, 5, False, 'skull',
     'The archaeologist who wants to live. Rare print with Ohara library backdrop.'),
    ('Portgas D. Ace — Flame Emperor', 'OP', 'SEC', 'Paramount War', 'OP02-013', 199.99, 1, True, 'sun',
     'Fire Fist Ace, secret rare. Thank you for loving me. Near mint, sleeved since pull.'),
    ('Shanks — Red-Haired Emperor', 'OP', 'L', 'Kingdoms of Intrigue', 'OP04-119', 329.00, 1, True, 'crown',
     'The man who bet an arm on the new era. Legendary rarity, conqueror\'s haki foil.'),
    ('Going Merry — Beloved Ship', 'OP', 'U', 'Romance Dawn', 'OP01-121', 15.50, 8, False, 'anchor',
     'The ship that flew. A crew\'s first true friend. Uncommon with lamb figurehead art.'),
    ('Trafalgar Law — Surgeon of Death', 'OP', 'SR', 'Kingdoms of Intrigue', 'OP04-069', 95.00, 3, False, 'skull',
     'ROOM. The Heart Pirates\' captain, super rare with Ope Ope no Mi accents.'),
    ('Mickey Mouse — Brave Little Tailor', 'DI', 'L', 'The First Chapter', 'TFC-088', 289.00, 1, True, 'ears',
     'The mouse who started it all, in his most heroic role. Legendary enchanted-style foil.'),
    ('Elsa — Spirit of Winter', 'DI', 'SEC', 'Rise of the Floodborn', 'ROF-041', 219.99, 2, True, 'snowflake',
     'The Snow Queen unleashed. Secret rare with deep-ice foil that shimmers blue-white.'),
    ('Simba — Rightful King', 'DI', 'SR', 'The First Chapter', 'TFC-114', 79.00, 4, False, 'crown',
     'Remember who you are. Pride Rock super rare, savanna sunset holo.'),
    ('Stitch — Experiment 626', 'DI', 'R', 'The First Chapter', 'TFC-125', 39.99, 7, False, 'paw',
     'Ohana means family. Small, blue, and capable of lifting 3,000 times his weight. Rare.'),
    ('Buzz Lightyear — Space Ranger', 'DI', 'R', 'Into the Inklands', 'ITI-052', 36.00, 6, False, 'star',
     'To infinity and beyond! Star Command rare with wing-pop foil panel.'),
    ('Maleficent — Mistress of All Evil', 'DI', 'SEC', 'Rise of the Floodborn', 'ROF-113', 189.00, 2, True, 'bolt',
     'The dark fairy in dragon-flame glory. Secret rare, green-fire etched foil.'),
    ('Ariel — Voice of the Sea', 'DI', 'SR', 'Into the Inklands', 'ITI-006', 69.50, 3, False, 'trident',
     'Part of your world. Under-the-sea super rare with pearlescent shimmer.'),
    ('Genie — Cosmic Phenomenal Power', 'DI', 'L', 'The First Chapter', 'TFC-046', 259.00, 1, True, 'lamp',
     'Itty bitty living space, legendary rarity. Ten thousand years of foil in one card.'),
    ('Donald Duck — Musketeer of the King', 'DI', 'U', 'Rise of the Floodborn', 'ROF-070', 11.99, 12, False, 'ears',
     'All for one and one for... aw, phooey. Uncommon with tabard crest art.'),
    ('Cinderella — Midnight Gown', 'DI', 'R', 'Into the Inklands', 'ITI-093', 44.00, 5, False, 'castle',
     'A dream is a wish your heart makes. Rare with glass-slipper sparkle finish.'),
]

RARITY_LABEL = dict(Card.Rarity.choices)
FRANCHISE_LABEL = dict(Card.Franchise.choices)


def wrap(text, width=42):
    words, lines, cur = text.split(), [], ''
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = f'{cur} {w}'.strip()
    lines.append(cur)
    return (lines + ['', ''])[:2]


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


class Command(BaseCommand):
    help = 'Seed the database with sample cards and generated card art.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='Allow seeding demo cards even when DEBUG is off (production).')

    def handle(self, *args, **options):
        from django.conf import settings
        if not settings.DEBUG and not options['force']:
            self.stderr.write('Refusing to add DEMO cards to a production site. Use --force if you really mean it.')
            return
        created = 0
        for (name, fr, rarity, cset, number, price, stock, featured, emblem, desc) in CARDS:
            if Card.objects.filter(name=name).exists():
                continue
            bg1, bg2, accent = OP_PALETTE if fr == 'OP' else DI_PALETTE
            line1, line2 = wrap(desc)
            display_name = name.split(' — ')[0]
            svg = CARD_SVG.format(
                bg1=bg1, bg2=bg2, accent=accent,
                emblem=EMBLEMS[emblem].format(bg1=bg1, bg2=bg2, accent=accent),
                name=esc(display_name.upper()[:26]),
                franchise=FRANCHISE_LABEL[fr],
                rarity=RARITY_LABEL[rarity],
                line1=esc(line1), line2=esc(line2),
                number=number,
            )
            card = Card(
                name=name, franchise=fr, rarity=rarity, card_set=cset,
                card_number=number, price=price, stock=stock,
                featured=featured, description=desc,
            )
            card.image.save(f'{slugify(name)}.svg', ContentFile(svg.encode()), save=False)
            card.save()
            created += 1
        self.stdout.write(self.style.SUCCESS(f'Seeded {created} cards ({Card.objects.count()} total).'))
