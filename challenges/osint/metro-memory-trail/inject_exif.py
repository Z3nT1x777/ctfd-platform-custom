"""
Inject EXIF metadata into OSINT challenge images.
Run once to prepare the assets.

clue.jpg  → GPS coordinates: Place de la Bastille, Paris (48.8533° N, 2.3692° E)
final.jpg → DateTimeOriginal: 1989:07:14 12:00:00
"""

import piexif
from PIL import Image
import struct
import os

BASE = os.path.join(os.path.dirname(__file__), "resources", "assets")


def to_dms_rational(degrees_float):
    """Convert decimal degrees to EXIF rational DMS tuples."""
    d = int(degrees_float)
    m_float = (degrees_float - d) * 60
    m = int(m_float)
    s_float = (m_float - m) * 60
    # Store seconds as rational: numerator / 10000 to preserve 4 decimal places
    s_num = int(round(s_float * 10000))
    return ((d, 1), (m, 1), (s_num, 10000))


def inject_gps(path, lat, lon):
    """Inject GPS coordinates into a JPEG."""
    img = Image.open(path)

    # Build GPS IFD
    gps_ifd = {
        piexif.GPSIFD.GPSVersionID: (2, 2, 0, 0),
        piexif.GPSIFD.GPSLatitudeRef:  b"N" if lat >= 0 else b"S",
        piexif.GPSIFD.GPSLatitude:     to_dms_rational(abs(lat)),
        piexif.GPSIFD.GPSLongitudeRef: b"E" if lon >= 0 else b"W",
        piexif.GPSIFD.GPSLongitude:    to_dms_rational(abs(lon)),
    }

    # Preserve existing EXIF if any, or start fresh
    try:
        exif_dict = piexif.load(img.info.get("exif", b""))
    except Exception:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}

    exif_dict["GPS"] = gps_ifd
    exif_bytes = piexif.dump(exif_dict)
    img.save(path, exif=exif_bytes, quality=92)
    print(f"[OK] GPS injected into {os.path.basename(path)}: {lat}N {lon}E")


def inject_date(path, date_str):
    """Inject DateTimeOriginal into a JPEG.  date_str = '1989:07:14 12:00:00'"""
    img = Image.open(path)

    try:
        exif_dict = piexif.load(img.info.get("exif", b""))
    except Exception:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}

    encoded = date_str.encode("ascii")
    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = encoded
    exif_dict["0th"][piexif.ImageIFD.DateTime] = encoded

    exif_bytes = piexif.dump(exif_dict)
    img.save(path, exif=exif_bytes, quality=92)
    print(f"[OK] Date injected into {os.path.basename(path)}: {date_str}")


if __name__ == "__main__":
    clue_path  = os.path.join(BASE, "clue.jpg")
    final_path = os.path.join(BASE, "final.jpg")

    # Place de la Bastille, Paris
    inject_gps(clue_path, lat=48.8533, lon=2.3692)

    # Bicentenaire de la Révolution française — 14 juillet 1989
    inject_date(final_path, "1989:07:14 12:00:00")

    print("\nVerification:")
    for f in [clue_path, final_path]:
        ed = piexif.load(f)
        gps = ed.get("GPS", {})
        exif = ed.get("Exif", {})
        date0th = ed.get("0th", {}).get(piexif.ImageIFD.DateTime, b"")
        print(f"  {os.path.basename(f)}")
        if gps:
            print(f"    GPS LatRef={gps.get(piexif.GPSIFD.GPSLatitudeRef)} "
                  f"Lat={gps.get(piexif.GPSIFD.GPSLatitude)} "
                  f"LonRef={gps.get(piexif.GPSIFD.GPSLongitudeRef)} "
                  f"Lon={gps.get(piexif.GPSIFD.GPSLongitude)}")
        if exif.get(piexif.ExifIFD.DateTimeOriginal):
            print(f"    DateTimeOriginal={exif[piexif.ExifIFD.DateTimeOriginal].decode()}")
        if date0th:
            print(f"    DateTime={date0th.decode()}")
