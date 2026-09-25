# Personal Website (GitHub Pages + Jekyll)

This site uses GitHub Pages' native Jekyll build with a custom two-column layout:
- left sidebar: profile image, page navigation, and social links
- right column: the content of the current page

## Edit content

1. Update [`main.md`](./main.md) for the homepage sections: About, Current Work, and Previous Research.
2. Update [`publications.md`](./publications.md) for publications.
3. Update [`teaching.md`](./teaching.md) for teaching activities.
4. Update [`gallery.md`](./gallery.md) for the gallery page shell and controls.
5. Add or replace framed square images in `photos/Selection/`, then prepare them and rebuild the gallery metadata:
   - `python -m pip install -r requirements-gallery.txt`
   - `python scripts/prepare_gallery_photos.py`
   - `python scripts/build_gallery_metadata.py`
6. Update [`other-stuff.md`](./other-stuff.md) for personal projects and interests.
7. Update [`_layouts/default.html`](./_layouts/default.html) if you want to change the sidebar links or social icons.
8. Replace `ressources/profil.png` for a new portrait.
9. Replace `ressources/CV_Olivier_Clerc.pdf` when your CV changes.

## Similarity-aware gallery

### Prepare the photo selection

Photos in `photos/Selection/` have a white frame. To create borderless copies at the same 2048x2048 pixel dimensions, run:

```powershell
python scripts/prepare_gallery_photos.py
```

The script detects the shared frame width from a sample of the photos, crops it, and enlarges the cropped image back to its input dimensions. Copies are written to `photos/Selection_processed/`; the originals remain untouched. Existing processed files are skipped. Use `--overwrite` after changing source photos or the crop settings, and `--border PIXELS` if you need to override the automatic detection.

The metadata builder reads only `photos/Selection_processed/`. The website loads those files from R2 when `photo_asset_origin` is set.

The gallery is static on GitHub Pages, but the photo grouping is precomputed locally:
- [`scripts/build_gallery_metadata.py`](./scripts/build_gallery_metadata.py) extracts color/tone and geometry features from every image in `photos/Selection_processed/`
- it projects each feature space onto one display axis
- it writes [`_data/gallery_metadata.json`](./_data/gallery_metadata.json)
- the site uses the JSON to select photos around a starting image using the gallery controls

Run the metadata builder in a Python environment with the packages in `requirements-gallery.txt`. On this computer, the existing `llm4h` Conda environment has the required packages; the base environment currently does not.

If you change the original photos, run:

```powershell
conda activate llm4h
python scripts/prepare_gallery_photos.py --overwrite
python scripts/build_gallery_metadata.py
python local_tools/build_umap_viewer.py
```

If you remove or rename an original, remove its old copy from `photos/Selection_processed/` before rebuilding. The preparation script does not delete existing processed files. Archived processed photos in `photos/Selection_processed/archive/` are ignored by the metadata builder.

## External photo hosting with Cloudflare R2

You can keep the site code on GitHub Pages and host the gallery images outside the repo.

This project now supports an optional external image origin through [`_config.yml`](./_config.yml):

```yml
photo_asset_origin: ""
```

- leave it empty for a local Jekyll preview that reads photos from your local folder; `photos/` is ignored by Git
- set it to a public Cloudflare origin such as `https://media.example.com` to load gallery images from there instead

Important:
- the metadata file stores image paths as `/photos/Selection_processed/<filename>`
- your Cloudflare bucket must therefore contain objects under the `photos/Selection_processed/` prefix
- example object key: `photos/Selection_processed/1778423887065.jpg`

Suggested workflow:
1. Keep your originals locally and/or on Google Drive.
2. Prepare web-ready images in `photos/Selection_processed/` and build the metadata.
3. Upload those processed images to Cloudflare R2 under `photos/Selection_processed/`.
4. Set `photo_asset_origin` in [`_config.yml`](./_config.yml) to your public R2 domain.
5. Push the site code and metadata to GitHub Pages.

Role of `rclone`:
- `rclone` copies or synchronizes `photos/Selection_processed/` with the matching prefix in the Cloudflare R2 bucket
- the site itself does not upload anything; it only reads the public image URLs
- `copy` adds or updates files on the bucket
- `sync` makes the bucket match your local folder exactly, including deletions

If you change the photo set, prepare the images and rebuild the metadata as above. On Windows, the upload helper reads `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_ACCESS_KEY_IDS3`, and `CLOUDFLARE_SECRET_ACCESS_KEY_S3` from your ignored `.env` file. It uses `rclone` from `PATH` or the ignored `.tools/rclone/` folder. Preview the upload, then run it:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\upload_gallery_photos.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\upload_gallery_photos.ps1 -Execute
```

This copies only processed photos and excludes `archive/`. Existing objects elsewhere in the bucket are left alone. If you later want to remove processed files that no longer exist locally, preview a sync before running it. `-Sync` affects only the `photos/Selection_processed/` prefix:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\upload_gallery_photos.ps1 -Sync
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\upload_gallery_photos.ps1 -Sync -Execute
```

The helper previews changes by default. Only `-Execute` changes the bucket.

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
