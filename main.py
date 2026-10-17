import csv
import asyncio
import aiohttp
import time
from bs4 import BeautifulSoup

URL = "https://havokkmorands.github.io/movie-catalog/"
BASE_URL = "https://havokkmorands.github.io"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}


async def extract_movie_details(session, movie_link):
    try:
        async with session.get(movie_link) as response:
            response.raise_for_status()
            html = await response.text()

        movie_soup = BeautifulSoup(html, "html.parser")

        detail_container = movie_soup.find(
            "section",
            attrs={"data-testid": "movie-detail"}
        )

        if detail_container is None:
            print(f"Detalhes não encontrados: {movie_link}")
            return None

        title_tag = detail_container.find(
            attrs={"data-testid": "movie-title"}
        )
        release_tag = detail_container.find(
            attrs={"data-testid": "movie-release"}
        )
        rating_tag = detail_container.find(
            attrs={"data-testid": "movie-rating"}
        )
        synopsis_tag = detail_container.find(
            attrs={"data-testid": "movie-synopsis"}
        )

        title = title_tag.get_text(strip=True) if title_tag else None

        date = (
            release_tag.get_text(strip=True)
            .replace("Lançamento:", "")
            .strip()
            if release_tag else None
        )

        rating = (
            rating_tag.get_text(strip=True)
            .replace("Nota:", "")
            .strip()
            if rating_tag else None
        )

        plot_text = (
            synopsis_tag.get_text(strip=True)
            .replace("Sinopse:", "")
            .strip()
            if synopsis_tag else None
        )

        if all([title, date, rating, plot_text]):
            movie = {
                "titulo": title,
                "lancamento": date,
                "nota": rating,
                "sinopse": plot_text
            }

            print(movie)
            return movie

        print(f"Algum dado está faltando: {movie_link}")
        return None

    except (aiohttp.ClientError, asyncio.TimeoutError) as error:
        print(f"Erro ao acessar {movie_link}: {error}")
        return None


async def main():
    timeout = aiohttp.ClientTimeout(total=20)

    async with aiohttp.ClientSession(
        headers=headers,
        timeout=timeout
    ) as session:
        async with session.get(URL) as response:
            response.raise_for_status()
            html = await response.text()

        start_time = time.perf_counter()
        soup = BeautifulSoup(html, "html.parser")

        container = soup.find(
            "section",
            attrs={"data-testid": "movies-list"}
        )

        if container is None:
            print("Container principal não encontrado.")
            return

        movies = container.find_all(
            "article",
            attrs={"data-testid": "movie-item"}
        )

        movie_links = []

        for movie in movies:
            link_tag = movie.find(
                "a",
                attrs={"data-testid": "movie-link"},
                href=True
            )

            if link_tag:
                movie_links.append(
                    f"{BASE_URL}{link_tag['href']}"
                )

        print(f"Filmes encontrados: {len(movie_links)}")
        print("Buscando os detalhes...")

        tasks = [
            extract_movie_details(session, link)
            for link in movie_links
        ]

        results = await asyncio.gather(*tasks)

        successful_movies = [
            movie for movie in results if movie is not None
        ]

        with open("movies.csv", "w", newline="", encoding="utf-8") as file:
            fieldnames = ["titulo", "lancamento", "nota", "sinopse"]

            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(successful_movies)

            end_time = time.perf_counter()

        print(f"Tempo total: {end_time - start_time: .2f} segundos")

        print(
            f"\nExtração concluída: "
            f"{len(successful_movies)} filmes com detalhes completos."
        )
        print("Arquivo movies.csv criado com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())