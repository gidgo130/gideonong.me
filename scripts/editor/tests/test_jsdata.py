import unittest

from _helpers import REPO_ROOT, TempRepo
from core.jsdata import Document, JsDataError, decode_string, encode_string


class RoundTrip(unittest.TestCase):
    def test_every_real_data_file_round_trips_byte_for_byte(self):
        for rel in ("js/translations.js", "js/projects-data.js", "js/experience-data.js", "js/tags-data.js", "js/docs-data.js"):
            p = REPO_ROOT / rel
            if not p.is_file():
                continue
            data = p.read_bytes()
            doc = Document.from_bytes(data, source=rel)
            self.assertEqual(doc.to_bytes({}), data, rel)

    def test_no_edit_render_equals_copy_of_real_translations(self):
        with TempRepo() as t:
            data = t.translations.read_bytes()
            doc = Document.load(t.translations)
            self.assertEqual(doc.to_bytes({}), data)
            self.assertEqual(doc.render({}), doc.text)

    def test_single_edit_changes_exactly_one_line(self):
        with TempRepo() as t:
            doc = Document.load(t.translations)
            root = doc.const("translations")
            es = root.value("es")
            prop = es.get("navAbout")
            self.assertIsNotNone(prop)
            new = doc.to_bytes({prop.value.tok: "Sobre mí (editado)"})
            old_lines = t.translations.read_bytes().split(b"\n")
            new_lines = new.split(b"\n")
            self.assertEqual(len(old_lines), len(new_lines))
            changed = [i for i, (a, b) in enumerate(zip(old_lines, new_lines)) if a != b]
            self.assertEqual(len(changed), 1)
            self.assertIn('navAbout: "Sobre mí (editado)",'.encode("utf-8"), new_lines[changed[0]])
            # re-parse the result: still in the subset, and the value reads back
            doc2 = Document.from_bytes(new)
            self.assertEqual(doc2.const("translations").value("es").value("navAbout").value, "Sobre mí (editado)")


class Subset(unittest.TestCase):
    def _err(self, text):
        with self.assertRaises(JsDataError) as cm:
            Document(text)
        return cm.exception

    def test_template_literal_refused_with_line(self):
        e = self._err('const x = {\n  a: "ok",\n  b: `nope`,\n};\n')
        self.assertEqual(e.line, 3)
        self.assertIn("template literal", str(e))

    def test_spread_refused_with_line(self):
        e = self._err("const x = {\n  a: 1,\n  ...other,\n};\n")
        self.assertEqual(e.line, 3)

    def test_function_call_refused_with_line(self):
        e = self._err('const x = {\n  a: "ok",\n  b: make("x"),\n};\n')
        self.assertEqual(e.line, 3)

    def test_identifier_value_refused(self):
        e = self._err("const x = { a: someConst };\n")
        self.assertEqual(e.line, 1)
        self.assertIn("identifier", str(e))

    def test_non_declaration_statement_refused(self):
        e = self._err('const x = {};\nconsole.log("hi");\n')
        self.assertEqual(e.line, 2)

    def test_string_concatenation_refused(self):
        e = self._err('const x = { a: "a" + "b" };\n')
        self.assertEqual(e.line, 1)

    def test_accepts_the_subset(self):
        doc = Document(
            "// header\nconst X = {\n  a: 'single',\n  \"b\": -1.5e3,\n  c: [true, false, null, { d: 0x1f }],\n  /* block */ e: \"esc \\\" \\\\ \\u00e9\", // trailing\n};\nlet Y = [];\n"
        )
        x = doc.const("X")
        self.assertEqual(x.value("a").value, "single")
        self.assertEqual(x.value("b").value, -1500.0)
        self.assertEqual(x.value("e").value, 'esc " \\ é')
        self.assertEqual(doc.const_names(), ["X", "Y"])

    def test_crlf_and_bom_preserved(self):
        data = b"\xef\xbb\xbfconst A = {\r\n  k: \"v\",\r\n};\r\n"
        doc = Document.from_bytes(data)
        self.assertEqual(doc.to_bytes({}), data)
        tok = doc.const("A").value("k").tok
        self.assertEqual(doc.to_bytes({tok: "w"}), b"\xef\xbb\xbfconst A = {\r\n  k: \"w\",\r\n};\r\n")


class Codecs(unittest.TestCase):
    def test_encode_decode_symmetry(self):
        for v in ['plain', 'quote " inside', "back \\ slash", "tab\tnew\nline", "ñ é — ✕ “quotes”", "\u2028 sep"]:
            self.assertEqual(decode_string(encode_string(v)), v)
            self.assertEqual(decode_string(encode_string(v, "'"), None), v)

    def test_quote_style_of_the_original_token_is_kept(self):
        doc = Document("const A = { k: 'v' };\n")
        tok = doc.const("A").value("k").tok
        self.assertEqual(doc.render({tok: "it's"}), "const A = { k: 'it\\'s' };\n")


if __name__ == "__main__":
    unittest.main()
