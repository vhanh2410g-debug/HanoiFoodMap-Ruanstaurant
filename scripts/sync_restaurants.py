import json
import re
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / 'data' / 'HanoiFoodPlaces.xlsx'
OUTPUT = ROOT / 'src' / 'restaurants.generated.json'
NS = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
GROUPS = {
    'Món Việt': 'vietnamese', 'Món gà': 'chicken', 'Lẩu': 'hotpot',
    'Nướng': 'grill', 'Món Á': 'asian', 'Đồ ăn nhanh': 'fast',
    'Ăn vặt': 'snacks', 'Tráng miệng': 'dessert', 'Café & đồ uống': 'drinks',
}
TYPE_BY_GROUP = {
    'Món Việt': 'Noodles', 'Món gà': 'Chicken', 'Lẩu': 'Hotpot',
    'Nướng': 'BBQ', 'Món Á': 'Noodles', 'Đồ ăn nhanh': 'Banh Mi',
    'Ăn vặt': 'Snacks', 'Tráng miệng': 'Dessert', 'Café & đồ uống': 'Cafe',
}

def column_index(cell_ref):
    letters = ''.join(c for c in cell_ref if c.isalpha())
    number = 0
    for char in letters:
        number = number * 26 + ord(char.upper()) - 64
    return number - 1

def read_rows():
    with zipfile.ZipFile(BOOK) as book:
        shared = []
        if 'xl/sharedStrings.xml' in book.namelist():
            strings = ET.fromstring(book.read('xl/sharedStrings.xml'))
            for si in strings.findall('x:si', NS):
                shared.append(''.join(t.text or '' for t in si.findall('.//x:t', NS)))
        root = ET.fromstring(book.read('xl/worksheets/sheet1.xml'))
        rows = []
        for row in root.findall('.//x:sheetData/x:row', NS):
            cells = []
            for cell in row.findall('x:c', NS):
                idx = column_index(cell.attrib['r'])
                while len(cells) <= idx:
                    cells.append('')
                value = cell.find('x:v', NS)
                text = value.text if value is not None and value.text else ''
                if cell.attrib.get('t') == 's' and text:
                    text = shared[int(text)]
                elif cell.attrib.get('t') == 'inlineStr':
                    text = ''.join(t.text or '' for t in cell.findall('.//x:t', NS))
                cells[idx] = text
            rows.append(cells)
        return rows

def num(value, default=0):
    try:
        return float(value) if value != '' else default
    except ValueError:
        return default

def slug(value):
    value = unicodedata.normalize('NFD', value)
    value = ''.join(c for c in value if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-') or 'place'

rows = read_rows()
if not rows:
    raise SystemExit('Workbook is empty; no restaurant header row found.')
headers = [str(value).strip() for value in rows[0]]
places = []
used_ids = set()
for row in rows[1:]:
    row += [''] * (len(headers) - len(row))
    item = dict(zip(headers, row))
    name = str(item.get('Tên quán', '')).strip()
    if not name:
        continue
    main = str(item.get('Danh mục chính', '')).strip()
    sub = str(item.get('Danh mục phụ', '')).strip()
    food_group = GROUPS.get(main)
    if not food_group:
        raise SystemExit(f"Danh mục chính không hợp lệ ở quán '{name}': {main}")
    place_id = str(item.get('ID (để trống nếu quán mới)', '')).strip()
    if not place_id:
        base = slug(name)
        place_id = base
        suffix = 2
        while place_id in used_ids:
            place_id = f'{base}-{suffix}'
            suffix += 1
    if place_id in used_ids:
        raise SystemExit(f"ID bị trùng: {place_id}")
    used_ids.add(place_id)
    category = str(item.get('Loại món', '')).strip() or TYPE_BY_GROUP[main]
    cuisine_region = sub if food_group == 'asian' else 'Việt Nam'
    address = str(item.get('Địa chỉ', '')).strip()
    area = str(item.get('Khu vực', '')).strip()
    map_url = str(item.get('Link Google Maps', '')).strip()
    if not map_url:
        query = quote(f'{name}, {address}, {area}, Hanoi')
        map_url = f'https://www.google.com/maps/search/?api=1&query={query}'
    tags = [x.strip() for x in str(item.get('Tags', '')).split(',') if x.strip()]
    situations = [x.strip() for x in str(item.get('Dịp phù hợp', '')).split(',') if x.strip()]
    index = len(places)
    places.append({
        'id': place_id, 'name': name, 'category': category, 'foodGroup': food_group,
        'cuisineRegion': cuisine_region,
        'form': 'water' if main == 'Món Việt' and sub == 'Món nước' else 'dry',
        'address': address, 'area': area,
        'latitude': num(item.get('Vĩ độ')), 'longitude': num(item.get('Kinh độ')),
        'priceMin': num(item.get('Giá từ (VNĐ)')), 'priceMax': num(item.get('Giá đến (VNĐ)')),
        'rating': num(item.get('Điểm demo'), 4.5), 'tags': tags, 'situations': situations,
        'moods': list(dict.fromkeys(tags + situations)),
        'description': str(item.get('Mô tả', '')).strip(),
        'image': str(item.get('Emoji', '🍽️')).strip() or '🍽️',
        'popularity': 92 - index * 1.2,
        'openingHours': str(item.get('Giờ mở cửa', '')).strip() or '10:00–22:00',
        'mapUrl': map_url,
    })

OUTPUT.write_text(json.dumps(places, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Synced {len(places)} restaurants from {BOOK.name} to src/restaurants.generated.json')
