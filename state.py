from datetime import datetime

def default_job():
    return {
        "meta": {
            "name": None,
            "last_modified": datetime.utcnow().isoformat()
        },
        "ct": {
            "strings": [],
            "active_index": None
        },
        "well": {
            "tvd": None,
            "kop": None,
            "td": None,
            "casing": [],
            "restrictions": [],
            "schematic": None
        },
        "fluids": {
            "base": None,
            "density": None,
            "chemicals": []
        },
        "settings": {
            "units": "metric",
            "flow_unit": "m/min",
            "force_unit": "daN",
            "theme": "dark"
        }
    }

