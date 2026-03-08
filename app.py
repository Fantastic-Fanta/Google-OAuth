import os
import asyncio
from dotenv import load_dotenv as load; load()
from quart import *
from quart_authlib import OAuth
from hypercorn.config import Config
from hypercorn.asyncio import serve

app = Quart(__name__)
app.secret_key = os.getenv("SECRET")

oa = OAuth()
oa.init_app(app)
oa.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

@app.get("/")
async def index():
    return """<a href="/login">Login</a> | <a href="/profile">Profile</a> | <a href="/logout">Logout</a>"""

@app.get("/login")
async def login():
    redirect_uri = url_for("auth", _external=True)
    return oa.google.authorize_redirect(redirect_uri)

@app.get("/auth")
async def auth():
    token = await oa.google.authorize_access_token()
    user = token.get("userinfo") or await oa.google.userinfo(token=token)
    session["user"] = dict(user)
    session["token"] = token
    return redirect("/")

@app.get("/logout")
async def logout():
    session.pop("user", None)
    session.pop("token", None)
    return redirect("/")

@app.get("/profile")
async def profile():
    token = session.get("token")
    try:
        user = oa.google.userinfo(token=token)
        return dict(user)
    except:
        return "Invalid"

if __name__ == "__main__":
    config = Config()
    config.bind = ["0.0.0.0:8000"]
    asyncio.run(serve(app, config))