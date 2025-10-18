import os
import json
import requests

class SpotifyAPIExtractor:

    def __init__(self, query, s_type, market, limit, output_dir="case_grpboticario/results_spotify_grpboticario"):
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
    
    def create_url_datahackers(self):
        return (
            f"https://api.spotify.com/v1/shows/1oMIHOXsrLFENAeM743g93"
            f"?market={self.market}"
        )

    def fetch_data(self):
        response = requests.get(self.create_url(), headers=self.headers)
        self.json_response = response.json()

        output_path = os.path.join(self.output_dir, "all_raw_data.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.json_response, f, indent=4, sort_keys=True, ensure_ascii=False)

        print(f"Dados brutos salvos em {output_path}")
        
        # filtrando dados incluindo somente name, description and id
        shows = self.json_response.get('shows', {}).get('items', [])
        self.filtered_data = [
            {
                'id': show['id'],
                'name': show['name'],
                'description': show['description']
            }
            for show in shows
        ]
        
        output_path = os.path.join(self.output_dir, "filtered_spotify_api_result.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.filtered_data, f, indent=4, sort_keys=True, ensure_ascii=False)

        print(f"Resultado salvo em {output_path}")

    # id_show = 1oMIHOXsrLFENAeM743g93
    def fetch_data_datahackers(self):

        response = requests.get(self.create_url_datahackers(), headers=self.headers)
        self.json_response = response.json()

        # acessando items dos episodios do json_response
        episodes = self.json_response.get('episodes', {}).get('items', [])

        # mantendo somente campos requisitados de cada episodio
        filtered_episodes = [
            {
                'id': ep.get('id'),
                'name': ep.get('name'),
                'description': ep.get('description'),
                'release_date': ep.get('release_date'),
                'duration_ms': ep.get('duration_ms'),
                'language': ep.get('language'),
                'explicit': ep.get('explicit'),
                'type': ep.get('type')
            }
            for ep in episodes
        ]

        output_path = os.path.join(self.output_dir, "datahackers_filtered_episodes.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(filtered_episodes, f, indent=4, sort_keys=True, ensure_ascii=False)

        print(f"Episódios do Data Hackers salvos em {output_path}")

    def fetch_data_datahackers_grupoboticario(self):

        response = requests.get(self.create_url_datahackers(), headers=self.headers)
        self.json_response = response.json()

        # acessando items dos episodios do json_response
        episodes = self.json_response.get('episodes', {}).get('items', [])

        # filtrando episodios contendo "Grupo Boticário" na descrição
        filtered_episodes = [
            {
                'id': ep['id'],
                'name': ep['name'],
                'description': ep['description'],
                'release_date': ep['release_date'],
                'duration_ms': ep['duration_ms'],
                'language': ep['language'],
                'explicit': ep['explicit'],
                'type': ep['type']
            }
            for ep in episodes
            if 'Grupo Boticário' in str(ep['description'])
        ]

        output_path = os.path.join(self.output_dir, "datahackers_grupoboticario_filtered_data.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(filtered_episodes, f, indent=4, sort_keys=True, ensure_ascii=False)

        print(f"Episódios filtrados do Data Hackers (Grupo Boticário) salvos em {output_path}")

if __name__ == "__main__":
    
    extractor = SpotifyAPIExtractor(
        query="data hackers",
        s_type="show",
        market="BR",
        limit=50
    )

    extractor.fetch_data()
    extractor.fetch_data_datahackers()
    extractor.fetch_data_datahackers_grupoboticario()