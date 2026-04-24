import requests
import time


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def validate_address(address):
    """
    Validate an address using OpenStreetMap Nominatim API.

    Parameters
    ----------
    address : str
        Hospital address to validate

    Returns
    -------
    dict
        {
            "valid": bool,
            "display_name": str or None,
            "lat": float or None,
            "lon": float or None
        }
    """

    if not address or not isinstance(address, str):
        return {
            "valid": False,
            "display_name": None,
            "lat": None,
            "lon": None
        }

    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "hospital-intelligence-project"
    }

    try:
        response = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        # Respect rate limits (important for Nominatim)
        time.sleep(1)

        if len(data) == 0:
            return {
                "valid": False,
                "display_name": None,
                "lat": None,
                "lon": None
            }

        result = data[0]

        return {
            "valid": True,
            "display_name": result.get("display_name"),
            "lat": float(result.get("lat")),
            "lon": float(result.get("lon"))
        }

    except requests.exceptions.RequestException:
        return {
            "valid": False,
            "display_name": None,
            "lat": None,
            "lon": None
        }