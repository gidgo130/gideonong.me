"""Phase 5: image import — metadata stripped, orientation applied, sizes by
preset; the service side (field set, alt keys, preview, save, delete)."""

import io
import unittest

from _helpers import REPO_ROOT, TempRepo
from app import EditorState, create_app
from core.site import images

TOKEN = "test-token-123"
HOST = "127.0.0.1:5510"


def hdr():
    return {"Host": HOST, "X-Editor-Token": TOKEN}


def phone_jpeg(width=4000, height=2000, orientation=6, gps=True, icc=True) -> bytes:
    """A JPEG the way a phone writes it: EXIF with camera fields, GPS IFD, orientation tag, ICC profile."""
    from PIL import Image, ImageCms

    im = Image.new("RGB", (width, height), (200, 120, 60))
    exif = Image.Exif()
    exif[0x010F] = "TestPhone Inc."  # Make
    exif[0x0110] = "Phone 12"  # Model
    exif[0x0132] = "2026:09:29 10:00:00"  # DateTime
    exif[0x0112] = orientation
    if gps:
        from PIL.TiffImagePlugin import IFDRational

        gps_ifd = exif.get_ifd(0x8825)
        gps_ifd[1] = "N"
        gps_ifd[2] = (IFDRational(36, 1), IFDRational(9, 1), IFDRational(1234, 100))
        gps_ifd[3] = "W"
        gps_ifd[4] = (IFDRational(95, 1), IFDRational(58, 1), IFDRational(0, 1))
    buf = io.BytesIO()
    kw = {"exif": exif.tobytes(), "quality": 95}
    if icc:
        kw["icc_profile"] = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    im.save(buf, "JPEG", **kw)
    return buf.getvalue()


def png_rgba(width=500, height=300) -> bytes:
    from PIL import Image, PngImagePlugin

    im = Image.new("RGBA", (width, height), (10, 20, 30, 128))
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Comment", "made on a phone")
    buf = io.BytesIO()
    im.save(buf, "PNG", pnginfo=meta)
    return buf.getvalue()


def opened(data: bytes):
    from PIL import Image

    im = Image.open(io.BytesIO(data))
    im.load()
    return im


class ProcessTests(unittest.TestCase):
    def test_phone_jpeg_comes_out_clean_upright_and_sized(self):
        src = phone_jpeg()
        im = opened(src)
        self.assertTrue(len(im.getexif()) > 0 and im.getexif().get_ifd(0x8825) and im.info.get("icc_profile"))
        out, info = images.process(src, "main")
        im = opened(out)
        self.assertEqual(im.format, "JPEG")
        self.assertEqual(len(im.getexif()), 0)
        self.assertFalse(im.getexif().get_ifd(0x8825))
        self.assertIsNone(im.info.get("icc_profile"))
        self.assertNotIn("comment", im.info)
        self.assertEqual(im.size, (800, 1600))  # orientation 6 → rotated; long edge 1600
        self.assertTrue(im.info.get("progressive") or im.info.get("progression"))
        self.assertEqual((info["hadExif"], info["hadGps"], info["hadIcc"], info["transposed"]), (True, True, True, True))
        self.assertEqual((info["width"], info["height"], info["format"]), (800, 1600, "jpg"))
        self.assertEqual(images.check(images_info(out)), [])

    def test_presets(self):
        src = phone_jpeg(4000, 2000, orientation=1, gps=False, icc=False)
        out, info = images.process(src, "thumb")
        self.assertEqual(opened(out).size, (800, 600))
        out, info = images.process(src, "wide")
        self.assertEqual(opened(out).size, (1600, 900))
        out, info = images.process(src, "portrait")
        self.assertEqual(opened(out).size, (1250, 625))
        small = phone_jpeg(300, 200, orientation=1, gps=False, icc=False)
        out, info = images.process(small, "main")
        self.assertEqual(opened(out).size, (300, 200))  # never upscaled
        out, info = images.process(small, "thumb")
        self.assertEqual(opened(out).size, (266, 200))  # 4:3 crop, no upscale
        with self.assertRaises(images.ImageError):
            images.process(src, "asis")  # 4000 px wide
        out, info = images.process(small, "asis")
        self.assertEqual(opened(out).size, (300, 200))
        with self.assertRaises(images.ImageError):
            images.process(src, "bogus")

    def test_png_stays_png_without_text_chunks(self):
        out, info = images.process(png_rgba(), "asis")
        im = opened(out)
        self.assertEqual((im.format, im.mode, im.size), ("PNG", "RGBA", (500, 300)))
        self.assertNotIn("Comment", im.info)
        self.assertEqual(info["format"], "png")
        out, info = images.process(png_rgba(3000, 1000), "main")
        self.assertEqual(opened(out).size, (1600, 533))

    def test_refusals_and_names(self):
        with self.assertRaises(images.ImageError):
            images.process(b"not an image", "main")
        from PIL import Image

        buf = io.BytesIO()
        Image.new("RGB", (10, 10)).save(buf, "GIF")
        with self.assertRaises(images.ImageError):
            images.process(buf.getvalue(), "main")
        with self.assertRaises(images.ImageError):
            images.process(b"\xff" * (images.MAX_INPUT + 1), "main")
        self.assertEqual(images.output_name("IMG_2041 (1).JPG", "main", "jpg"), "img-2041-1.jpg")
        self.assertEqual(images.output_name("Shop Photo", "thumb", "jpg"), "shop-photo-thumb.jpg")
        self.assertEqual(images.output_name("plot.png", "asis", "png"), "plot.png")
        self.assertEqual(images.output_name("???", "main", "jpg"), "image.jpg")

    @unittest.skipUnless((REPO_ROOT / "assets" / "images").is_dir(), "no images in the repo")
    def test_repo_images_are_already_clean(self):
        rows = images.scan(REPO_ROOT)
        self.assertGreater(len(rows), 20)
        self.assertEqual([(r["path"], r["warnings"]) for r in rows if r["warnings"]], [])


def images_info(data: bytes) -> dict:
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "x.jpg"
        p.write_bytes(data)
        return images.inspect(p)


class ServiceImageTests(unittest.TestCase):
    def test_import_sets_field_alt_preview_and_saves(self):
        with TempRepo() as t:
            st = EditorState(t.root, t.local, TOKEN, 5510, 5501)
            c = st.content
            c.add_entry("projects", "test-editor", "Test", "Prueba")
            with self.assertRaises(ValueError):
                c.import_image(phone_jpeg(), "IMG_1.jpg", "projects", "test-editor", "imageAlt", "main", "A photo", "")
            with self.assertRaises(ValueError):
                c.import_image(phone_jpeg(), "IMG_1.jpg", "projects", "test-editor", "bogus", "main", "A photo", "Una foto")
            r = c.import_image(phone_jpeg(), "IMG_1.jpg", "projects", "test-editor", "imageAlt", "main", "A photo", "Una foto")
            self.assertEqual(r["path"], "assets/images/projects/test-editor/img-1.jpg")
            self.assertEqual(r["key"], "projTestEditorAlt")
            e = c.entry("projects", "test-editor")
            self.assertEqual((e["imageSrc"], e["imageAlt"]), (r["path"], "projTestEditorAlt"))
            self.assertEqual(c.drafts["newKeys"]["projTestEditorAlt"], {"en": "A photo", "es": "Una foto"})
            ov = c.preview_overrides()
            self.assertIn(r["path"], ov)
            self.assertEqual(opened(ov[r["path"]]).size, (800, 1600))
            self.assertFalse((t.root / r["path"]).exists())
            # the dev check sees the pending file as present (no missing-file error)
            self.assertNotIn("missing-file", [i.code for i in c.gate().blocking])
            rev = c.review()
            self.assertEqual(rev["assets"], [{"path": r["path"], "action": "add", "kb": r["kb"], "size": "800 × 1600"}])
            # a thumbnail and a photo (creates the photos list item)
            c.set_field("projects", "test-editor", ["page"], {"sections": [], "facts": [], "photos": [], "reportPdf": "", "creditKey": ""})
            c.create_shell("test-editor")
            r2 = c.import_image(phone_jpeg(orientation=1), "IMG_1.jpg", "projects", "test-editor", "thumbAlt", "thumb", "Thumb", "Miniatura")
            self.assertEqual(r2["path"], "assets/images/projects/test-editor/img-1-thumb.jpg")
            r3 = c.import_image(png_rgba(), "Plot Final.png", "projects", "test-editor", "page.photos.1.alt", "asis", "A plot", "Una gráfica")
            e = c.entry("projects", "test-editor")
            self.assertEqual(e["page"]["photos"], [{"src": "assets/images/projects/test-editor/plot-final.png", "altKey": "projTestEditorPhoto1Alt"}])
            with self.assertRaises(ValueError):
                c.import_image(png_rgba(), "x.png", "projects", "test-editor", "page.photos.3.alt", "asis", "a", "b")  # gap in the list
            # the same name again while still pending simply replaces the pending file (nothing is on disk yet)
            n_staged = len(list(c.image_staging.glob("*")))
            c.import_image(phone_jpeg(), "img-1.jpg", "projects", "test-editor", "imageAlt", "main", "A photo", "Una foto")
            self.assertEqual(len(list(c.image_staging.glob("*"))), n_staged)
            self.assertEqual(len(c.drafts["images"]), 3)
            self.assertTrue(c.gate().ok(), c.gate().to_json())
            res = c.save()
            self.assertTrue(res["ok"], res)
            for rel in (r["path"], r2["path"], r3["path"]):
                self.assertTrue((t.root / rel).is_file(), rel)
                self.assertEqual(images.check(images.inspect(t.root / rel)), [])
            self.assertEqual(c.draft_count(), 0)
            self.assertEqual(list(c.image_staging.glob("*")), [])
            # the files now exist on disk: replace flow backs the old one up
            before = (t.root / r["path"]).read_bytes()
            r4 = c.import_image(phone_jpeg(1000, 1000, orientation=1, gps=False, icc=False), "img-1.jpg", "projects", "test-editor", "imageAlt", "main", "A photo", "Una foto", replace=True)
            self.assertTrue(r4["replace"])
            self.assertEqual(c.review()["assets"][0]["action"], "replace")
            res = c.save()
            self.assertTrue(res["ok"], res)
            self.assertNotEqual((t.root / r["path"]).read_bytes(), before)
            self.assertEqual(st.backups.read_file(res["backup"], r["path"]), before)
            # delete: refused while used, then allowed; removed on save into the backup set
            with self.assertRaises(ValueError):
                c.delete_image(r2["path"])
            c.set_field("projects", "test-editor", ["thumbSrc"], "")
            self.assertEqual(c.delete_image(r2["path"]), {"pending": False})
            self.assertIn(r2["path"], [x["path"] for x in c.images_state()["images"] if x["removed"]])
            res = c.save()
            self.assertTrue(res["ok"], res)
            self.assertFalse((t.root / r2["path"]).exists())
            self.assertIsNotNone(st.backups.read_file(res["backup"], r2["path"]))
            with self.assertRaises(ValueError):
                c.delete_image("../secret.txt")
            # the headshot is protected by about.html's reference
            (t.root / "about.html").write_text('<img src="assets/images/about/headshot.jpg">', encoding="utf-8")
            (t.root / "assets/images/about").mkdir(parents=True, exist_ok=True)
            (t.root / "assets/images/about/headshot.jpg").write_bytes(b"")
            with self.assertRaises(ValueError):
                c.delete_image("assets/images/about/headshot.jpg")
            # discard drops staged bytes
            c.import_image(phone_jpeg(), "IMG_9.jpg", "projects", "test-editor", "imageAlt", "main", "x", "y", replace=True)
            self.assertEqual(len(list(c.image_staging.glob("*"))), 1)
            c.discard_drafts()
            self.assertEqual(list(c.image_staging.glob("*")), [])

    def test_multipart_endpoint(self):
        with TempRepo() as t:
            st = EditorState(t.root, t.local, TOKEN, 5510, 5501)
            app = create_app(st)
            app.testing = True
            cl = app.test_client()
            st.content.add_entry("projects", "test-editor", "Test", "Prueba")
            data = {"image": (io.BytesIO(phone_jpeg()), "IMG_2041.jpg"), "file": "projects", "slug": "test-editor", "field": "imageAlt", "preset": "main", "altEn": "A photo", "altEs": "Una foto", "name": ""}
            r = cl.post("/api/content/images/import", headers=hdr(), data=data, content_type="multipart/form-data")
            self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
            j = r.get_json()
            self.assertEqual(j["result"]["path"], "assets/images/projects/test-editor/img-2041.jpg")
            self.assertTrue(j["result"]["hadGps"])
            self.assertIn("assets/images/projects/test-editor/img-2041.jpg", j["pendingImages"])
            data = {"image": (io.BytesIO(phone_jpeg()), "IMG_2041.jpg"), "file": "projects", "slug": "test-editor", "field": "imageAlt", "preset": "main", "altEn": "A photo", "altEs": ""}
            r = cl.post("/api/content/images/import", headers=hdr(), data=data, content_type="multipart/form-data")
            self.assertEqual(r.status_code, 400)
            r = cl.post("/api/content/images/import", headers={"Host": HOST}, data={"file": "projects"}, content_type="multipart/form-data")
            self.assertEqual(r.status_code, 403)
            r = cl.get("/api/content/images", headers=hdr())
            self.assertEqual(r.status_code, 200)
            self.assertTrue(any(x["pending"] == "add" for x in r.get_json()["images"]))


if __name__ == "__main__":
    unittest.main()
