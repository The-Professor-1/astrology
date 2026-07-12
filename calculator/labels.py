"""Calculator display titles — single source for list tiles, form pages, and admin."""

# Admin / CalculationRecord keys → short label
CALCULATOR_LABELS = {
    'kokeb_calculator': 'ኮከብ ስሌት',
    'wealth_calculator': 'የሀብት እጣ ፈንታ',
    'behavior_calculator': 'የግል ጸባይ ስሌት',
    'place_calculator': 'የመኖሪያ ቦታ ምቹነት',
    'marriage_luck': 'የትዳር በረከት',
    'servant_behavior': 'የሰራተኛ ጸባይ',
    'born_prophecy_calculator': 'ለምወልድ ልጅ ትንቢት',
    'love_prophecy_calculator': 'የፍቅር ትንቢት',
    'pregnancy_prophecy_calculator': 'የፅንስ ትንቢት',
    'military_prophecy_calculator': 'የጦርነት ትንቢት',
    'life_luck_calculator': 'የራስ ኑሮ እድል',
    'patient_prophecy_calculator': 'የበሽተኛ ውጤት',
    'legal_calculator': 'የፍርድ ውሳኔ',
    'enemy_behavior_calculator': 'የጠላት ጸባይ',
    'marriage_length': 'የትዳር ቆይታ',
}

# Form page titles (address key → heading on general.html)
PAGE_TITLES = {
    'kokeb_calculator': '⭐ ኮከብ ስሌት — ኮከብዎን ለማወቅ',
    'wealth_calculator': '💰 የሀብት እጣ ፈንታ — ሀብት እና የስጦታ ጊዜ',
    'behavior_calculator': '🧠 የግል ጸባይ — ባህሪዎን ለማወቅ',
    'place_calculator': '🏠 የመኖሪያ ቦታ — ምቹነት ለማወቅ',
    'marriage_luck': '💍 የትዳር በረከት — ማን በረከት እንዳለው',
    'servant_behavior': '👤 የሰራተኛ ጸባይ — ስለሰራተኛ ለማወቅ',
    'born_prophecy_calculator': '👶 ለምወልድ ልጅ — ጾታ እና ባህሪ ትንቢት',
    'love_prophecy_calculator': '❤️ የፍቅር ትንቢት — ፍቅር ለማወቅ',
    'pregnancy_prophecy_calculator': '🤰 የፅንስ ትንቢት — የፅንስ እጣ ፈንታ',
    'military_prophecy_calculator': '🛡️ የጦርነት ትንቢት — ጉዞ/ጦርነት ውጤት',
    'life_luck_calculator': '🌟 የራስ ኑሮ እድል — የህይወት እድል',
    'patient_prophecy_calculator': '🏥 የበሽተኛ ትንቢት — ጤና/ውጤት ለማወቅ',
    'legal_calculator': '⚖️ የፍርድ ትንቢት — ፍርድ ውጤት ለማወቅ',
    'enemy_behavior_calculator': '⚔️ የጠላት ጸባይ — ጠላት ለማወቅ',
    'marriage_length': '⏳ የትዳር ቆይታ — ትዳር ለምን ያህል',
}

# Calculator list grid (url name, tile label, image)
CALCULATOR_LIST = [
    ('calculate', 'ኮከብ ስሌት — ኮከብዎን ለማወቅ', 'home-big-image.png'),
    ('wealth_calculator', 'የሀብት እጣ ፈንታ — ሀብት እና የስጦታ ጊዜ', 'home-big-image.png'),
    ('behavior_calculator', 'የግል ጸባይ — ባህሪዎን ለማወቅ', 'home-big-image.png'),
    ('place_calculator', 'የመኖሪያ ቦታ — ምቹነት ለማወቅ', 'home-big-image.png'),
    ('marriage_luck_calculator', 'የትዳር በረከት — ማን በረከት እንዳለው', 'home-big-image.png'),
    ('birth_prophecy', 'ለምወልድ ልጅ — ጾታ እና ባህሪ ትንቢት', 'home-big-image.png'),
    ('pregnancy_prophecy', 'የፅንስ ትንቢት — የፅንስ እጣ ፈንታ', 'home-big-image.png'),
    ('love_prophecy', 'የፍቅር ትንቢት — ፍቅር ለማወቅ', 'home-big-image.png'),
    ('patient_prophecy', 'የበሽተኛ ትንቢት — ጤና/ውጤት ለማወቅ', 'home-big-image.png'),
    ('legal_prophecy', 'የፍርድ ትንቢት — ፍርድ ውጤት ለማወቅ', 'home-big-image.png'),
    ('marriage_length_prophecy', 'የትዳር ቆይታ — ትዳር ለምን ያህል', 'home-big-image.png'),
    ('enemy_behavior', 'የጠላት ጸባይ — ጠላት ለማወቅ', 'home-big-image.png'),
    ('life_luck', 'የራስ ኑሮ እድል — የህይወት እድል', 'home-big-image.png'),
    ('military_prophecy', 'የጦርነት ትንቢት — ጉዞ/ጦርነት ውጤት', 'home-big-image.png'),
    ('servant_behavior', 'የሰራተኛ ጸባይ — ስለሰራተኛ ለማወቅ', 'home-big-image.png'),
]

# Locked-tile popup descriptions (key = list tile label)
CALCULATOR_DESCRIPTIONS = {
    'የሀብት እጣ ፈንታ — ሀብት እና የስጦታ ጊዜ': 'የእርስዎን የሀብት እድል፣ የገቢ ሁኔታ እና ጥሩ ጊዜዎችን ለማወቅ።',
    'የግል ጸባይ — ባህሪዎን ለማወቅ': 'የግል ጸባይዎን፣ የሰዎች ጋር ግንኙነት እና ባህሪዎን ለመተንበይ።',
    'የመኖሪያ ቦታ — ምቹነት ለማወቅ': 'መኖሪያ ቦታ፣ ከተማ ወይም አካባቢ ለእርስዎ ተስማሚ መሆኑን ለማወቅ።',
    'የትዳር በረከት — ማን በረከት እንዳለው': 'በትዳር ውስጥ ማን በረከት እንዳለው እና ግንኙነቱን ለመተንበይ።',
    'ለምወልድ ልጅ — ጾታ እና ባህሪ ትንቢት': 'ምን አይነት ልጅ ሊወለድ እንደሚችል — ጾታ እና ባህሪ ለመተንበይ።',
    'የፅንስ ትንቢት — የፅንስ እጣ ፈንታ': 'የፅንስ እጣ ፈንታ፣ ጤና እና ውጤት ለማወቅ።',
    'የፍቅር ትንቢት — ፍቅር ለማወቅ': 'የሁለት ሰዎች ፍቅር ጥሩ መሆን አለመሆኑን ለመተንበይ።',
    'የበሽተኛ ትንቢት — ጤና/ውጤት ለማወቅ': 'የበሽተኛ ጤና ሁኔታ እና ውጤት ለመተንበይ።',
    'የፍርድ ትንቢት — ፍርድ ውጤት ለማወቅ': 'የፍርድ ቤት ጉዳይ ውጤት እና የተሟጋቾች ሁኔታ ለመተንበይ።',
    'የትዳር ቆይታ — ትዳር ለምን ያህል': 'የትዳር ህይወት ቆይታ እና የህይወት ገጾች ለመተንበይ።',
    'የጠላት ጸባይ — ጠላት ለማወቅ': 'ጠላትዎ ባህሪ፣ ግንኙነት እና ተጽዕኖ ለመተንበይ።',
    'የራስ ኑሮ እድል — የህይወት እድል': 'የራስዎ ኑሮ፣ እድል እና የህይወት አቅጣጫ ለማወቅ።',
    'የጦርነት ትንቢት — ጉዞ/ጦርነት ውጤት': 'ወደ ጦርነት፣ ጉዞ ወይም አደገኛ ሁኔታ ውጤት ለመተንበይ።',
    'የሰራተኛ ጸባይ — ስለሰራተኛ ለማወቅ': 'ሰራተኛ ጸባይ፣ ግንኙነት እና ታማኝነት ለመተንበይ።',
}


def get_page_title(address):
    return PAGE_TITLES.get(address, 'ስሌት')


def general_context(address, **extra):
    """Standard context for calculator/general.html."""
    return {'address': address, 'page_title': get_page_title(address), **extra}
