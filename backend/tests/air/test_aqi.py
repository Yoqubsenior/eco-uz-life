import pytest

from apps.air.aqi import categorize


@pytest.mark.parametrize(
    "aqi, expected",
    [
        # Boundaries are where off-by-one bugs live, so test both sides of each.
        (0, "good"),
        (50, "good"),
        (51, "moderate"),
        (100, "moderate"),
        (101, "unhealthy_sensitive"),
        (150, "unhealthy_sensitive"),
        (151, "unhealthy"),
        (200, "unhealthy"),
        (201, "very_unhealthy"),
        (300, "very_unhealthy"),
        (301, "hazardous"),
        (999, "hazardous"),
        (1500, "hazardous"),
    ],
)
def test_categorize_boundaries(aqi, expected):
    assert categorize(aqi).key == expected


def test_categorize_rejects_negative():
    with pytest.raises(ValueError):
        categorize(-1)
