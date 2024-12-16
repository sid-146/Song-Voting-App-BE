from fastapi import FastAPI, status, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy import Spotify
from json import loads, dumps, load, dump

from dotenv import load_dotenv

print(f"Env Loaded : {load_dotenv()}")

app = FastAPI(
    title="DB API",
    description="API TO INTERACT WITH DATABASE",
    # lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(mf_router)


@app.get("/health")
def health():
    content = {"detail": "UP AND RUNNING"}
    return JSONResponse(content=content, status_code=status.HTTP_200_OK)


def connect_to_spotify() -> Spotify:
    """
    Connect to Spotify using client credentials.

    Args:
        client_id (str): Your Spotify client ID.
        client_secret (str): Your Spotify client secret.

    Returns:
        Spotify: An authenticated Spotify client.
    """
    credentials = SpotifyClientCredentials(
        # client_id=client_id, client_secret=client_secret
    )
    return Spotify(client_credentials_manager=credentials)


def extract_required_data(client: Spotify, data) -> list:
    # track = {
    #     "track": {
    #         "artists": [{"name": "Stellar"}],
    #         "href": "https://api.spotify.com/v1/tracks/3Pj6u2KTgepyyidp5xfbHp",
    #         "name": "Ashes",
    #     },
    #     "added_by": {"id": "lzq1fptz2dgchro68nxzg1uot"},
    # }
    name = data["name"]
    tracks = list()
    with open("users.json", "r") as file:
        users = load(file)

    for track in data["tracks"]["items"]:
        added_by_id = track["added_by"]["id"]
        if added_by_id in users:
            added_by = users[added_by_id]
        else:
            user = client.user(added_by_id)
            added_by = user["display_name"]
            users[added_by_id] = added_by
            with open("users.json", "w") as file:
                dump(users, file)

            del users

            with open("users.json", "r") as file:
                users = load(file)

        temp = {
            "name": track["track"]["name"],
            "artists": track["track"]["artists"],
            "added_by": added_by,
        }
        tracks.append(temp)

    final = {"name": name, "tracks": tracks}
    return final


@app.get("/api/songs")
def songs(client: Spotify = Depends(connect_to_spotify)):
    if client is None:
        # Handle the case where the client is not available
        return JSONResponse(
            content={"detail": "Spotify client could not be created."},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    try:
        data = client.playlist(
            playlist_id="0oSHuUe3Y2qHED6IsLPJlq",
            fields="id,name,tracks(items(added_by.id,track(name,href,artists(name))))",
        )
        data: list = extract_required_data(client, data)
        return JSONResponse(
            content=data,
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return JSONResponse(
            content={"detail": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app="app:app", reload=True)
