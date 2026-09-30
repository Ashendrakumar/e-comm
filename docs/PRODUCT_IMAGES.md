# Product photos from Google Drive

Keep product photos in a Google Drive folder and import them in bulk instead of
uploading them one by one in the admin.

## One-time setup (≈10 minutes)

1. **Install Google Drive for desktop** on the computer that runs the site
   (<https://www.google.com/drive/download/>) and sign in with the account that owns the photos.
   Drive appears as a normal drive in File Explorer, e.g. `G:\My Drive`.
2. **Make a folder** in Drive, e.g. `My Drive\Product Images`. Share it with whoever takes the photos.
3. **Tell the site where it is** — add this line to `.env` in the project folder:

   ```
   PRODUCT_IMAGES_DIR=G:\My Drive\Product Images
   ```

   Restart the server after editing `.env`.
4. **Create the folder tree** — Admin → *Products* → **Import images from Drive** →
   **Create product folders**, or double-click `scripts\create_product_folders.bat`, or:

   ```
   python manage.py create_product_folders              # every active product
   python manage.py create_product_folders --dry-run    # just list what it would make
   python manage.py create_product_folders --only-missing   # skip products that have photos
   ```

   You get `Product Images\Category\SKU - Product name\` for every active product; the
   `Product Images` folder itself is created too (only `My Drive` must already exist).
   A product that already has a folder — matched by SKU, slug or name, even if you renamed
   or moved it — is left alone. Nothing is renamed or deleted, so re-run it after adding products.

   > In Drive for desktop settings, choose **Mirror files** (or mark the folder
   > *Available offline*) so the photos are really on this computer when importing.

## Everyday use

1. Drop each product's photos into its folder (from your phone's Drive app, a laptop, anywhere).
   - A file named **`main`**, **`cover`** or **`front`** becomes the primary photo; otherwise the first one.
   - Order follows the numbers: `2.jpg` comes before `10.jpg`.
   - Any size is fine — photos are resized to 1600 px and saved as WebP.
2. Admin → *Products* → **Import images from Drive** → **Preview** → check the table → **Import now**.

   Or double-click `scripts\import_product_images.bat` (preview, then asks before importing), or:

   ```
   python manage.py import_product_images            # preview
   python manage.py import_product_images --apply    # import
   ```

### What the statuses mean

| Status | Meaning | What to do |
|---|---|---|
| ready / done | Photos will be / were attached | — |
| skipped | The product already has photos | Choose *Add after them* or *Replace* if you meant to change them |
| unmatched | No product has that folder's SKU, slug or name | Rename the folder to start with the product's SKU (shown in the admin) |
| error | A file couldn't be read (corrupt, not an image) | Re-export or remove that file |

### Folder naming rules

Folders (or loose files) are matched to products by, in order: **SKU** (`TZ-32E6AADD`),
**slug** (`canon-eos-r50`) or **product name** (`Canon EOS R50`), case-insensitively.
`SKU - anything` works too — only the part before ` - ` is used. Category folders are optional.

```
Product Images\
  Cameras\
    TZ-32E6AADD - Canon EOS R50\
      main.jpg
      2.jpg
  canon-eos-r50\          (slug works)
  Canon EOS R50\          (name works)
  TZ-55F23A1E-1.jpg       (loose files: SKU-1, SKU-2 …)
```

## Try it with the sample

`samples/product-images/` holds placeholder photos for the demo catalogue, laid out
exactly like a real Drive folder:

```
python manage.py import_product_images samples/product-images            # preview
python manage.py import_product_images samples/product-images --apply    # import
```

## Command options

| Option | Default | |
|---|---|---|
| `source` | `PRODUCT_IMAGES_DIR` | A folder or a `.zip` (e.g. a folder downloaded from Drive) |
| `--apply` | off (preview) | Save the images |
| `--mode skip\|append\|replace` | `skip` | What to do with products that already have photos |
| `--create-folders` | | Same as `create_product_folders` (add `--only-missing` to skip products with photos) |
| `--max-px` | `1600` | Longest side after resizing |
| `--format webp\|jpeg` | `webp` | Output format |
| `--no-resize` | | Keep originals (must be under 5 MB) |
| `--report file.csv` | | Save the result table |

## On a hosted (Linux) server

Drive for desktop only runs on Windows/macOS. On a server, either run the import on your
computer against the production database, upload a ZIP of the folder and run
`import_product_images photos.zip --apply`, or sync the Drive folder with
[rclone](https://rclone.org/drive/) (`rclone sync drive:"Product Images" /srv/product-images`)
and point `PRODUCT_IMAGES_DIR` there.
