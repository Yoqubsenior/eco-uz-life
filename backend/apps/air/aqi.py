"""AQI categories (US EPA scale, which WAQI also uses).

A pure function of the AQI number — it is computed, never stored (decision DB3).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AqiCategory:
    key: str
    label: str
    color: str  # official EPA colour, used on the map and in the app
    max_aqi: int  # inclusive upper bound
    advice: str
    sensitive_advice: str  # children, elderly, people with asthma / heart or lung disease


CATEGORIES: tuple[AqiCategory, ...] = (
    AqiCategory(
        "good",
        "Yaxshi",
        "#00E400",
        50,
        "Havo toza. Ochiq havoda faollik uchun qulay.",
        "Cheklov yo'q.",
    ),
    AqiCategory(
        "moderate",
        "O'rtacha",
        "#FFFF00",
        100,
        "Havo sifati qoniqarli.",
        "Juda sezgir odamlar uzoq va og'ir jismoniy faollikni kamaytirgani ma'qul.",
    ),
    AqiCategory(
        "unhealthy_sensitive",
        "Sezgir guruhlar uchun zararli",
        "#FF7E00",
        150,
        "Ko'pchilik uchun xavf past, lekin uzoq vaqt tashqarida bo'lmang.",
        "Bolalar, keksalar va astma bilan og'riganlar tashqaridagi faollikni kamaytirsin.",
    ),
    AqiCategory(
        "unhealthy",
        "Zararli",
        "#FF0000",
        200,
        "Tashqaridagi og'ir jismoniy faollikni kamaytiring.",
        "Bolalar va sezgir guruhlar tashqarida bo'lmasin, derazalarni yopiq tuting.",
    ),
    AqiCategory(
        "very_unhealthy",
        "Juda zararli",
        "#8F3F97",
        300,
        "Hamma uchun xavfli. Imkon qadar uyda qoling.",
        "Sezgir guruhlar uydan chiqmasin; havo tozalagich yoki niqob ishlating.",
    ),
    AqiCategory(
        "hazardous",
        "Xavfli",
        "#7E0023",
        999,
        "Favqulodda holat: tashqariga chiqmang.",
        "Tashqariga chiqmang; nafas olishda qiyinchilik bo'lsa shifokorga murojaat qiling.",
    ),
)


def categorize(aqi: int) -> AqiCategory:
    if aqi < 0:
        raise ValueError(f"AQI cannot be negative: {aqi}")
    for category in CATEGORIES:
        if aqi <= category.max_aqi:
            return category
    return CATEGORIES[-1]  # above the scale is still "hazardous"
