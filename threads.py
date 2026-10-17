import requests
import time
import csv
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup

URL = "https://havokkmorands.github.io/movie-catalog/"
BASE_URL = "https://havokkmorands.github.io"

MAX_THREADS = 10

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9"
}


def extract_movie_details(movie_link):
    try:
        response = requests.get(
            movie_link,
            headers=headers,
            timeout=20
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        container = soup.find(
            "section",
            attrs={"data-testid": "movie-detail"}
        )

        if container is None:
            print(f"Detalhes não encontrados: {movie_link}")
            return None

        title_tag = container.find(
            attrs={"data-testid": "movie-title"}
        )
        release_tag = container.find(
            attrs={"data-testid": "movie-release"}
        )
        rating_tag = container.find(
            attrs={"data-testid": "movie-rating"}
        )
        synopsis_tag = container.find(
            attrs={"data-testid": "movie-synopsis"}
        )

        title = title_tag.get_text(strip=True) if title_tag else None

        date = (
            release_tag.get_text(strip=True)
            .replace("Lançamento:", "").strip()
            if release_tag else None
        )

        rating = (
            rating_tag.get_text(strip=True)
            .replace("Nota:", "").strip()
            if rating_tag else None
        )

        synopsis = (
            synopsis_tag.get_text(strip=True)
            .replace("Sinopse:", "").strip()
            if synopsis_tag else None
        )

        if all([title, date, rating, synopsis]):
            return {
                "titulo": title,
                "lancamento": date,
                "nota": rating,
                "sinopse": synopsis
            }

        print(f"Dados incompletos: {movie_link}")
        return None

    except (requests.RequestException, ValueError) as error:
        print(f"Erro ao acessar {movie_link}: {error}")
        return None


def main():
    start_time = time.perf_counter()

    response = requests.get(URL, headers=headers, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    container = soup.find(
        "section",
        attrs={"data-testid": "movies-list"}
    )

    if container is None:
        print("Lista de filmes não encontrada.")
        return

    movie_items = container.find_all(
        "article",
        attrs={"data-testid": "movie-item"}
    )

    movie_links = []

    for item in movie_items:
        link_tag = item.find(
            "a",
            attrs={"data-testid": "movie-link"},
            href=True
        )

        if link_tag:
            movie_links.append(BASE_URL + link_tag["href"])

    print(f"Filmes encontrados: {len(movie_links)}")
    print(f"Usando até {min(MAX_THREADS, len(movie_links))} threads...")
    print("Buscando os detalhes...")

    with ThreadPoolExecutor(
        max_workers=MAX_THREADS
    ) as executor:
        results = list(
            executor.map(extract_movie_details, movie_links)
        )

    successful_movies = [
        movie for movie in results if movie is not None
    ]

    with open(
        "movies_threads.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        fields = ["titulo", "lancamento", "nota", "sinopse"]
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(successful_movies)

    elapsed = time.perf_counter() - start_time

    print(
        f"\nExtração concluída: {len(successful_movies)} "
        "filmes com detalhes completos."
    )
    print("Arquivo criado: movies_threads.csv")
    print(f"Tempo total com threads: {elapsed:.2f} segundos")


if __name__ == "__main__":
    main()