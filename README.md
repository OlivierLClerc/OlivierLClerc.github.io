# Personal Website (GitHub Pages + Jekyll)

This site uses GitHub Pages' native Jekyll build with a custom two-column layout:
- left sidebar: profile image, page navigation, and social links
- right column: the content of the current page

## Edit content

1. Update [`main.md`](./main.md) for the homepage sections: About, Current Work, and Previous Research.
2. Update [`publications.md`](./publications.md) for publications.
3. Update [`teaching.md`](./teaching.md) for teaching activities.
4. Update [`other-stuff.md`](./other-stuff.md) for personal projects and interests.
5. Update [`_layouts/default.html`](./_layouts/default.html) if you want to change the sidebar links or social icons.
6. Replace `ressources/profil.png` for a new portrait.
7. Replace `ressources/CV_Olivier_Clerc.pdf` when your CV changes.

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
