import os
import json
import requests
from datetime import datetime, timedelta

class SpotifyAPIExtractor:

    def __init__(self, query, s_type, market, limit, output_dir="results"):
        self.query = query
        self.s_type = s_type
        self.market = market
        self.limit = limit
        self.output_dir = output_dir
        self.bearer_token = os.getenv("BEARER_TOKEN_SPOTIFY")
        self.headers = {"Authorization": f"Bearer {self.bearer_token}"}
        os.makedirs(self.output_dir, exist_ok=True)
        self.json_response = None
        self.filtered_data = None

    def create_url(self):
        return (
            f"https://api.spotify.com/v1/search?"
            f"q={self.query}&type={self.s_type}&market={self.market}&limit={self.limit}"
        )

    def create_url_without_limit(self):
        return (
            f"https://api.spotify.com/v1/search?"
            f"q={self.query}&type={self.s_type}&market={self.market}"
        )

    def fetch_all_data(self):

        response = requests.get(self.create_url_without_limit(), headers=self.headers)
        self.json_response = response.json()
        output_path = os.path.join(self.output_dir, "all_spotify_api_result.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.json_response, f, indent=4, sort_keys=True, ensure_ascii=False)

        print(f"Resultado salvo em {output_path}")

    def filter_data(self):

        self.filtered_data = []

        for item in self.json_response.get("shows", {}).get("items", []):
            self.filtered_data.append({
                "name": item.get("name"),
                "description": item.get("description"),
                "id": item.get("id")
            })
        
        filtered_output_path = os.path.join(self.output_dir, "spotify_api_filtered.json")

        with open(filtered_output_path, "w", encoding="utf-8") as f:
            json.dump(self.filtered_data, f, indent=4, ensure_ascii=False)

        print(f"Total de registros filtrados: {len(self.filtered_data)}")
        print(f"Arquivo filtrado salvo em {filtered_output_path}")
        
    # def save_filtered_data(self):

    #     filtered_output_path = os.path.join(self.output_dir, "spotify_api_filtered.json")

    #     with open(filtered_output_path, "w", encoding="utf-8") as f:
    #         json.dump(self.filtered_data, f, indent=4, ensure_ascii=False)

    #     print(f"Arquivo filtrado salvo em {filtered_output_path}")

if __name__ == "__main__":

    extractor = SpotifyAPIExtractor(
        query="data hackers",
        s_type="show",
        market="BR",
        limit=50
    )

    extractor.fetch_all_data()
    extractor.filter_data()
        
    # extractor.save_filtered_data()