# BA Founder Portfolio Website

Static portfolio website for BA, ActiView, BlinkClip, and related project pages.

## Tech Stack

- Plain HTML
- CSS
- Vanilla JavaScript

## Project Structure

- `index.html` - main landing page
- `about/` - background and story page
- `projects/` - individual project pages
- `styles.css` - shared site styles
- `script.js` - shared site interactions

## Run Locally

This site does not require a build step. Serve the repository as static files:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000`.

## Build

No build process is currently required. The repository is ready to deploy as a static site.

## Deploy

You can deploy this site to any static host, including GitHub Pages:

1. Push the repository to GitHub.
2. In the GitHub repository settings, enable GitHub Pages.
3. Set the source to the root of the default branch.

## Publishing Notes

- Replace `YOUR_EMAIL_HERE` in the contact links with a public email address before launch.
- Review the ignored local-only media in `.gitignore` if you later decide to publish additional assets.
