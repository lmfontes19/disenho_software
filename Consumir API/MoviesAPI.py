import os
import requests

from dataclasses import dataclass
from typing import List, Optional
from dotenv import load_dotenv

TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"

@dataclass
class Movie:
    id: int
    title: str
    original_title: str
    release_date: Optional[str]
    overview: str
    popularity: float
    vote_average: float
    poster_path: Optional[str]

    def short_str(self) -> str:
        year = self.release_date.split("-")[0] if self.release_date else "s/f"
        return f"[{year}] {self.title} ( - {self.vote_average:.1f}, pop {self.popularity:.0f})"

class TMDBClient:
    def __init__(self, bearer_token: Optional[str] = None, lang: str = "es-MX") -> None:
        self.bearer_token = bearer_token or os.getenv("TMDB_BEARER_TOKEN")
        if not self.bearer_token:
            raise RuntimeError(
                "Falta TMDB_BEARER_TOKEN en ambiente o no se paso el token al constructor"
            )

        self.lang = lang
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self.bearer_token}",
            "accept": "application/json",
        })

    def search_movies(self, query: str, page: int = 1, include_adult: bool = False) -> dict:
        params = {
            "query": query,
            "include_adult": str(include_adult).lower(),
            "language": self.lang,
            "page": page,
        }

        resp = self._session.get(TMDB_SEARCH_URL, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

class MovieService:
    def __init__(self, client: TMDBClient) -> None:
        self.client = client

    def find_by_title(self, title: str, page: int = 1) -> List[Movie]:
        payload = self.client.search_movies(title, page=page)
        movies: List[Movie] = []

        for item in payload.get("results", []):
            movies.append(
                Movie(
                    id=item.get("id"),
                    title=item.get("title", ""),
                    original_title=item.get("original_title", ""),
                    release_date=item.get("release_date"),
                    overview=item.get("overview", ""),
                    popularity=float(item.get("popularity", 0.0)),
                    vote_average=float(item.get("vote_average", 0.0)),
                    poster_path=item.get("poster_path"),
                )
            )

        return movies

class ConsoleUI:
    def __init__(self, service: MovieService) -> None:
        self.service = service

    def run(self) -> None:
        try:
            title = input("Ingresa el titulo a buscar: ")
            if not title.strip():
                print("Debes ingresar un texto de busqueda.")
                return

            movies = self.service.find_by_title(title)
            if not movies:
                print("No se encontraron resultados.")
                return

            print(f"\nResultados para '{title}':\n")
            for i, m in enumerate(movies, start=1):
                print(f"{i:2d}. {m.short_str()}")

            print("\n(Primera pagina de resultados)")
        except requests.HTTPError as http_err:
            print(f"Error HTTP: {http_err}")
        except Exception as ex:
            print(f"Ocurrio un error: {ex}")

if __name__ == "__main__":
    load_dotenv()
    client = TMDBClient()
    service = MovieService(client)
    app = ConsoleUI(service)
    app.run()

#########################################
## Reflexion:
#########################################
# Primero que nada, me gustaria destacar que los diagramas de clases UML son muy utiles cuando
# se trata de disenhar una clase, ya que te permite definir atributos y metodos que lo van a
# consumir. Una vez que se tiene definido el diagrama de clases. Es sumamente facil desarrollar
# las clases en codigo. Sobre el codigo, la separacion clara entre TMDBClient y MovieService
# permite realizar pruebas mas seguras y facilita futuras modificaciones sin afectar el resto
# del sistema. Mientras que contar con un modelo/clase Movie ayuda a reducir el acoplamiento
# con el JSON externo. Ademas, el patron propuesto tiene una evolución natural y sencilla hacia
# una API REST sin necesidad de reescribir el cliente.
