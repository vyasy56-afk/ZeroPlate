# ZeroPlate deployment

ZeroPlate is a Flask application with server-rendered pages, Python APIs, machine-learning models, and a SQLite database. Netlify does not run Flask/Python web servers, so this setup deploys the application server on Render and configures Netlify to proxy all requests to it. This keeps the existing pages, assets, and API routes working under the Netlify domain.

## Deploy

1. Push this branch to GitHub and merge it into the branch Netlify/Render should deploy (normally `main`).
2. In Render, create a **Blueprint** from this repository and deploy `render.yaml`. The service is named `zeroplate`, so its default origin URL is `https://zeroplate.onrender.com`.
3. In Netlify, link the same repository and deploy with the included `netlify.toml`. The forced proxy rule forwards every request to the Render service, including `/api/*`, `/static/*`, and Flask page routes. Do not configure a separate Netlify build command or publish directory.
4. Open the Netlify site URL. The first request may take a little while if the free Render service has gone to sleep.

If Render gives the service a different hostname, update the `to` URL in `netlify.toml` to that exact HTTPS origin, then redeploy Netlify.

## Database persistence

The Render Blueprint starts from the checked-in demo database and places its working copy at `/tmp/zeroplate.db`. This works for a demo, but the free service's local filesystem is ephemeral: changes made through the app can be lost when Render restarts or redeploys the service. For durable production data, attach persistent storage and set `DATABASE_PATH` to a file on that mounted disk, or move the database to a managed database and adapt the database layer.

## Local run

```bash
pip install -r requirements.txt
python run.py
```

The development server listens on `0.0.0.0` and uses the `PORT` environment variable when provided. Production runs under Gunicorn via `Procfile` / `render.yaml`.
