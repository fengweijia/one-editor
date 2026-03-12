from typing import Dict, Any

class MemoryRepo:
    def __init__(self):
        self.articles_by_checksum: Dict[str, Dict[str, Any]] = {}
        self.assets: Dict[str, Any] = {"points": [], "cases": [], "quotes": [], "structures": []}

    def has_article(self, checksum: str) -> bool:
        return checksum in self.articles_by_checksum

    def save_article(self, checksum: str, article: Dict[str, Any]) -> None:
        self.articles_by_checksum[checksum] = article

    def save_assets(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        ids = {"points": [], "cases": [], "quotes": [], "structures": []}
        for t in ["points", "cases", "quotes"]:
            for item in analysis.get(t, []):
                ids[t].append(len(self.assets[t]))
                self.assets[t].append(item)
        structure = analysis.get("structure")
        if structure:
            ids["structures"].append(len(self.assets["structures"]))
            self.assets["structures"].append(structure)
        return ids
