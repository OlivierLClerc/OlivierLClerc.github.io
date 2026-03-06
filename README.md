# Personal Website (GitHub Pages + Jekyll Theme)

This site uses GitHub Pages' native Jekyll build with a custom two-column layout:
- left sidebar: profile image + icon links
- right column: section panels generated from `main.md`

## Edit content

1. Update [`main.md`](./main.md) for all page sections.
2. Update [`index.md`](./index.md) if you want to change sidebar links or profile text.
3. Replace `ressources/profil.png` for a new portrait.
4. Replace `ressources/CV_Olivier_Clerc.pdf` when your CV changes.

## Publish on GitHub Pages

1. Push this folder to a GitHub repository.
2. In GitHub: `Settings` -> `Pages`.
3. Under `Build and deployment`, choose:
   - `Source`: `Deploy from a branch`
   - `Branch`: `main` (or `master`) and `/ (root)`
4. Save. GitHub Pages will build and publish automatically.

## Notes

- No Node.js setup is required for deployment.
- If you use a project repository URL (`username.github.io/repo-name`), relative links in this site already handle it.
