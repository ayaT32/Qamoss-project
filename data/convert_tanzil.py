"""
Convert a Tanzil quran-simple.xml (or quran-uthmani.xml) export into the
quran.json schema used by app/build_index.py.

Usage:
    python data/convert_tanzil.py path/to/quran-simple.xml data/quran_full.json

Tanzil format (what you downloaded) looks like:
    <quran>
      <sura index="1" name="الفاتحة">
        <aya index="1" text="بسم الله الرحمن الرحيم" />
        ...
      </sura>
      ...
    </quran>

IMPORTANT: this script copies `text` verbatim from the XML — it must never
reformat, re-diacritize, or "correct" the Quranic text itself. Tanzil's
license requires verbatim copies and attribution; see TANZIL_LICENSE below.
"""
import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

TANZIL_LICENSE = (
    "Tanzil Quran Text — verbatim copies permitted, modification not allowed. "
    "Source must be clearly indicated and a link to tanzil.net included. "
    "See http://tanzil.net/docs/Quran_Text_Copyright"
)


def convert(xml_path: str, out_path: str) -> None:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    chunks = []
    for sura in root.findall("sura"):
        sura_index = sura.get("index")
        sura_name = sura.get("name")
        for aya in sura.findall("aya"):
            aya_index = aya.get("index")
            text = aya.get("text")
            chunks.append({
                "id": f"quran_{sura_index}_{aya_index}",
                "text": text,
                "source": "القرآن الكريم",
                "reference": f"سورة {sura_name}: {aya_index}",
                "narrator": None,
                "grade": None,
                "url": f"https://tanzil.net/#{sura_index}:{aya_index}",
                "license": TANZIL_LICENSE,
            })

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"Converted {len(chunks)} ayat -> {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python data/convert_tanzil.py <input.xml> <output.json>")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
