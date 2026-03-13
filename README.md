# Personal Website (GitHub Pages + Jekyll)

This site uses GitHub Pages' native Jekyll build with a custom two-column layout:
- left sidebar: profile image, page navigation, and social links
- right column: the content of the current page

## Edit content

1. Update [`main.md`](./main.md) for the homepage sections: About, Current Work, and Previous Research.
2. Update [`publications.md`](./publications.md) for publications.
3. Update [`teaching.md`](./teaching.md) for teaching activities.
4. Update [`gallery.md`](./gallery.md) for the gallery page shell and controls.
5. Add or replace square images in `photos/`, then rebuild the gallery metadata:
   - `python -m pip install -r requirements-gallery.txt`
   - `python scripts/build_gallery_metadata.py`
6. Update [`other-stuff.md`](./other-stuff.md) for personal projects and interests.
7. Update [`_layouts/default.html`](./_layouts/default.html) if you want to change the sidebar links or social icons.
8. Replace `ressources/profil.png` for a new portrait.
9. Replace `ressources/CV_Olivier_Clerc.pdf` when your CV changes.

## Similarity-aware gallery

The gallery is static on GitHub Pages, but the photo grouping is precomputed locally:
- [`scripts/build_gallery_metadata.py`](./scripts/build_gallery_metadata.py) extracts handcrafted visual features from every image in `photos/`
- the script reduces those features to 2D with UMAP
- it writes [`_data/gallery_metadata.json`](./_data/gallery_metadata.json)
- the site then uses that JSON to build "random anchor + nearest neighbors" photo groups in the browser

If you change the photos, run:

```powershell
python scripts/build_gallery_metadata.py
python local_tools/build_umap_viewer.py
```

Re-run the metadata builder whenever you add, remove, or replace files in `photos/`.

## External photo hosting with Cloudflare R2

You can keep the site code on GitHub Pages and host the gallery images outside the repo.

This project now supports an optional external image origin through [`_config.yml`](./_config.yml):

```yml
photo_asset_origin: ""
```

- leave it empty to keep using local repo images from `photos/`
- set it to a public Cloudflare origin such as `https://media.example.com` to load gallery images from there instead

Important:
- the metadata file stores image paths as `/photos/<filename>`
- your Cloudflare bucket must therefore expose the files under a `photos/` prefix, not at the bucket root
- example object key: `photos/20251206_161513.jpg`

Suggested workflow:
1. Keep your originals locally and/or on Google Drive.
2. Keep a local `photos/` folder with the web-ready images used for metadata extraction.
3. Upload those web-ready images to Cloudflare R2 under the `photos/` prefix.
4. Set `photo_asset_origin` in [`_config.yml`](./_config.yml) to your public R2 domain.
5. Push the site code and metadata to GitHub Pages.

Role of `rclone`:
- `rclone` is the command-line tool that copies or synchronizes your local `photos/` folder with the Cloudflare R2 bucket
- the site itself does not upload anything; it only reads the public image URLs
- `copy` adds or updates files on the bucket
- `sync` makes the bucket match your local folder exactly, including deletions

If you change the photo set:

```powershell
python scripts/build_gallery_metadata.py
python local_tools/build_umap_viewer.py
```

Then update the bucket contents:

```powershell
rclone sync .\photos r2:photos/photos --exclude "archive/**" --dry-run
rclone sync .\photos r2:photos/photos --exclude "archive/**"
```

Use `--dry-run` first to preview which files would be uploaded, replaced, or deleted without changing the bucket.

Then push the updated metadata/site code.

## Local preview

1. Install Ruby + Bundler if they are not already available.
2. Install the Jekyll gems:
   - `bundle.bat install`
3. Start the local site:
   - `bundle.bat exec jekyll serve`
4. Open `http://127.0.0.1:4000`

## Publish on GitHub Pages

1. Push this folder to a GitHub repository.
2. In GitHub: `Settings` -> `Pages`.
3. Under `Build and deployment`, choose:
   - `Source`: `Deploy from a branch`
   - `Branch`: `main` (or `master`) and `/ (root)`
4. Save. GitHub Pages will build and publish automatically.

## Notes

- No Node.js setup is required for deployment.
- The gallery metadata must be rebuilt locally before you push new photos.
- If you use a project repository URL (`username.github.io/repo-name`), relative links in this site already handle it.
- If `photo_asset_origin` is set, the gallery loads its images from that external host while the rest of the site still stays on GitHub Pages.
