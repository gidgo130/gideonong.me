// about-data.js — the About page's three lists, read by js/about.js:
//   ABOUT_BOOKS  §3 "What have I been reading?"   { id, coverSrc, titleEN, titleES, descEN, descES, visible }
//   ABOUT_FAQ    §4 Interview FAQ                  { id, questionEN, questionES, answerEN, answerES, visible }
//   ABOUT_SITES  §6 Interesting sites              { id, url, internal, labelEN, labelES, descEN, descES, visible }
// Text is inline EN/ES here (plan.md's page spec for about.html), not translations.js keys.
// `visible: false` keeps an entry in the file but off the page. Each block is shown or hidden as a
// whole by the `hidden` attribute on its element in about.html (§3 and §4 are hidden until their
// placeholder content is replaced). `internal: true` opens a site in the same tab (site-relative url).
// The local editor (scripts/editor, Content › About) edits this file in place; ids never change.

const ABOUT_BOOKS = [
  { id: "book-1", coverSrc: "assets/images/book-placeholder-1.jpg", titleEN: "[Book title 1 — EN]", titleES: "[Título del libro 1 — ES]", descEN: "[Book description 1 — EN]", descES: "[Descripción del libro 1 — ES]", visible: true },
  { id: "book-2", coverSrc: "assets/images/book-placeholder-2.jpg", titleEN: "[Book title 2 — EN]", titleES: "[Título del libro 2 — ES]", descEN: "[Book description 2 — EN]", descES: "[Descripción del libro 2 — ES]", visible: true },
  { id: "book-3", coverSrc: "assets/images/book-placeholder-3.jpg", titleEN: "[Book title 3 — EN]", titleES: "[Título del libro 3 — ES]", descEN: "[Book description 3 — EN]", descES: "[Descripción del libro 3 — ES]", visible: true },
  { id: "book-4", coverSrc: "assets/images/book-placeholder-4.jpg", titleEN: "[Book title 4 — EN]", titleES: "[Título del libro 4 — ES]", descEN: "[Book description 4 — EN]", descES: "[Descripción del libro 4 — ES]", visible: true },
  { id: "book-5", coverSrc: "assets/images/book-placeholder-5.jpg", titleEN: "[Book title 5 — EN]", titleES: "[Título del libro 5 — ES]", descEN: "[Book description 5 — EN]", descES: "[Descripción del libro 5 — ES]", visible: true }
];

const ABOUT_FAQ = [
  { id: "faq-1", questionEN: "[FAQ question 1 — EN]", questionES: "[Pregunta 1 — ES]", answerEN: "[FAQ answer 1 — EN]", answerES: "[Respuesta 1 — ES]", visible: true },
  { id: "faq-2", questionEN: "[FAQ question 2 — EN]", questionES: "[Pregunta 2 — ES]", answerEN: "[FAQ answer 2 — EN]", answerES: "[Respuesta 2 — ES]", visible: true },
  { id: "faq-3", questionEN: "[FAQ question 3 — EN]", questionES: "[Pregunta 3 — ES]", answerEN: "[FAQ answer 3 — EN]", answerES: "[Respuesta 3 — ES]", visible: true },
  { id: "faq-4", questionEN: "[FAQ question 4 — EN]", questionES: "[Pregunta 4 — ES]", answerEN: "[FAQ answer 4 — EN]", answerES: "[Respuesta 4 — ES]", visible: true }
];

const ABOUT_SITES = [
  { id: "atomic-rockets", url: "https://projectrho.com/public_html/rocket/", internal: false, labelEN: "Atomic Rockets", labelES: "Atomic Rockets", descEN: "A really cool science fiction website by Winchell Chung.", descES: "Un sitio web de ciencia ficción realmente genial de Winchell Chung.", visible: true }
];
