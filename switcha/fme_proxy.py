from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins = [
        'http://localhost.fans656.me',
    ],
    allow_credentials = True,
    allow_methods = ['*'],
    allow_headers = ['*'],
)


@app.post('/api/set-current')
def set_current(data: dict = Body(...)):
    print(data)


def main():
    uvicorn.run(app, port = 9000)


if __name__ == '__main__':
    main()
