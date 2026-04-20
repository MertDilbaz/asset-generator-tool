import numpy as np

# ENDESGA 64 (EDG64) Tam Palet
EDG64_PALETTE = [
    (255, 0, 64), (19, 19, 19), (27, 27, 27), (39, 39, 39), (61, 61, 61), (93, 93, 93),
    (133, 133, 133), (180, 180, 180), (255, 255, 255), (199, 207, 221), (146, 161, 185), (101, 115, 146),
    (66, 76, 110), (42, 47, 78), (26, 25, 50), (14, 7, 27), (28, 18, 28), (57, 31, 33),
    (93, 44, 40), (138, 72, 54), (191, 111, 74), (230, 156, 105), (246, 202, 159), (249, 230, 207),
    (237, 171, 80), (224, 116, 56), (198, 69, 36), (142, 37, 29), (255, 80, 0), (237, 118, 20),
    (255, 162, 20), (255, 200, 37), (255, 235, 87), (211, 252, 126), (153, 230, 95), (90, 197, 79),
    (51, 152, 75), (30, 111, 80), (19, 76, 76), (12, 46, 68), (0, 57, 109), (0, 105, 170),
    (0, 152, 220), (0, 205, 249), (12, 241, 255), (148, 253, 255), (253, 210, 237), (243, 137, 245),
    (219, 63, 253), (122, 9, 250), (48, 3, 217), (12, 2, 147), (3, 25, 63), (59, 20, 67),
    (98, 36, 97), (147, 56, 143), (202, 82, 201), (200, 80, 134), (246, 129, 135), (245, 85, 93),
    (234, 50, 60), (196, 36, 48), (137, 30, 43), (87, 28, 39)
]

# Çiftçilik, Tarım ve Doğa için Özel Alt Palet (26 Renk)
# Bu palet AI'ın kafasının karışmasını önlemek için sadece gerekli renkleri içerir.
CROPS_PALETTE = [
    # Temel Işık/Gölge (Keskin kontrastlar için)
    (28, 18, 28),     # Çok Koyu Gölge
    (255, 255, 255),  # Saf Beyaz (Parlamalar)
    (249, 230, 207),  # Sıcak Açık Vurgu
    
    # Toprak, Tohum ve Kökler (Kahverengi Rampası)
    (57, 31, 33), (93, 44, 40), (138, 72, 54), (191, 111, 74), (230, 156, 105),
    
    # Yapraklar ve Gövdeler (Erken, Orta ve Hasat Aşaması Yeşilleri)
    (211, 252, 126),  # Filiz / Açık Yeşil
    (153, 230, 95),   # Taze Yaprak
    (90, 197, 79),    # Olgun Yaprak
    (51, 152, 75),    # Koyu Yeşil
    (30, 111, 80),    # Derin Gölge Yeşili
    
    # Buğday, Mısır ve Samanlar (Sarılar)
    (255, 235, 87), (255, 200, 37), (255, 162, 20),
    
    # Havuç, Balkabağı (Turuncular)
    (237, 171, 80), (224, 116, 56), (198, 69, 36), (255, 80, 0),
    
    # Domates, Turp, Elma, Çilek (Kırmızılar)
    (142, 37, 29), (196, 36, 48), (234, 50, 60),
    
    # Patlıcan, Üzüm, Böğürtlen (Morlar)
    (59, 20, 67), (98, 36, 97), (147, 56, 143)
]

# Diğer kategorileri şimdilik EDG64'ün geneline bağlıyoruz. İleride madenler veya binalar için 
# tıpkı CROPS_PALETTE gibi özel listeler oluşturabilirsin.
PALETTE_SUBSETS = {
    "default": EDG64_PALETTE,
    "crops": CROPS_PALETTE,
    "ground": CROPS_PALETTE, # Toprak da aynı renkleri kullanabilir
    "water": EDG64_PALETTE,  # İleride sadece mavi tonlarını filtreleyebilirsin
    "magic": EDG64_PALETTE,
    "objects": EDG64_PALETTE
}

def get_palette_for_category(category):
    return PALETTE_SUBSETS.get(category, PALETTE_SUBSETS["default"])