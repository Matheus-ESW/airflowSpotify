from airflow.providers.http.hooks.http import HttpHook
from airflow.exceptions import AirflowException
from datetime import datetime, timedelta
import requests
import json

class SpotifyHook(HttpHook):

    def __init__(self, query, s_type, market, limit, conn_id=None):
        self.query = query
        self.s_type = s_type
        self.market = market
        self.limit = limit
        self.conn_id = conn_id or "spotify_default"
        super().__init__(http_conn_id=self.conn_id)

    def create_url(self):
        url_raw = (
            f"{self.base_url}/v1/search?"
            f"q={self.query}&type={self.s_type}&market={self.market}&limit={self.limit}"
        )
        return url_raw

    def conn_to_endpoint(self, url, session):
        request = requests.Request("GET", url)
        prep = session.prepare_request(request)
        self.log.info(f"Requisição: {url}")

        return self.run_and_check(session, prep, {})
    
    def pagination(self, url_raw, session):
        list_json_response = []
        response = self.conn_to_endpoint(url_raw, session)
        json_response = response.json()
        list_json_response.append(json_response)

        cont = 1

        # Paginação (até 10 páginas por padrão)
        while "next_token" in json_response.get("meta",{}):
            next_token = json_response['meta']['next_token']
            url = f"{url_raw}&next_token={next_token}"
            response = self.conn_to_endpoint(url, session)
            json_response = response.json()
            list_json_response.append(json_response)
            cont += 1

        return list_json_response

    def run(self):
        url_raw = self.create_url()
        session = self.get_conn()

        return self.pagination(url_raw, session)

if __name__ == "__main__":
    # Exemplo de uso do SpotifyHook
    query = "data hackers"  # primeiros 50 resultados
    s_type = "show"
    market = "BR"
    limit = 50

    for pg in SpotifyHook(query, s_type, market, limit).run():
        print(json.dumps(pg, indent=4, ensure_ascii=False))