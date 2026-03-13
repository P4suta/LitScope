"""Tests for text normalizer."""

import pytest

from litscope.ingestion.text_normalizer import (
    NormalizedChapter,
    NormalizedSentence,
    NormalizedToken,
    TextNormalizer,
)


@pytest.fixture(scope="module")
def normalizer() -> TextNormalizer:
    return TextNormalizer()


class TestTextNormalizer:
    def test_strip_html(self, normalizer: TextNormalizer) -> None:
        html = "<html><body><p>Hello <b>world</b>.</p></body></html>"
        result = normalizer.normalize(html)
        assert result.sentences
        assert "<" not in result.sentences[0].text

    def test_sentences_extracted(self, normalizer: TextNormalizer) -> None:
        html = "<p>First sentence. Second sentence.</p>"
        result = normalizer.normalize(html)
        assert result.sent_count >= 2

    def test_tokens_have_pos(self, normalizer: TextNormalizer) -> None:
        html = "<p>The cat sat on the mat.</p>"
        result = normalizer.normalize(html)
        tokens = result.sentences[0].tokens
        pos_tags = {t.pos for t in tokens}
        assert len(pos_tags) > 1

    def test_tokens_have_lemma(self, normalizer: TextNormalizer) -> None:
        html = "<p>The dogs were running quickly.</p>"
        result = normalizer.normalize(html)
        lemmas = {t.lemma for t in result.sentences[0].tokens}
        assert "dog" in lemmas

    def test_space_tokens_filtered(self, normalizer: TextNormalizer) -> None:
        html = "<p>Hello   world.</p>"
        result = normalizer.normalize(html)
        for sent in result.sentences:
            assert all(t.text.strip() for t in sent.tokens)

    def test_empty_sentences_filtered(self, normalizer: TextNormalizer) -> None:
        html = "<p>   </p><p>Real sentence here.</p>"
        result = normalizer.normalize(html)
        for sent in result.sentences:
            assert sent.tokens

    def test_unicode_normalization(self, normalizer: TextNormalizer) -> None:
        # NFKC normalizes ﬁ ligature to "fi"
        html = "<p>The ﬁrst oﬃce.</p>"
        result = normalizer.normalize(html)
        text = " ".join(t.text for sent in result.sentences for t in sent.tokens)
        assert "fi" in text

    def test_word_count(self, normalizer: TextNormalizer) -> None:
        html = "<p>One two three.</p>"
        result = normalizer.normalize(html)
        assert result.word_count >= 3

    def test_chapter_sent_count(self, normalizer: TextNormalizer) -> None:
        html = "<p>Sentence one. Sentence two.</p>"
        result = normalizer.normalize(html)
        assert result.sent_count >= 2

    def test_sentence_char_count(self, normalizer: TextNormalizer) -> None:
        html = "<p>Hello world.</p>"
        result = normalizer.normalize(html)
        assert result.sentences[0].char_count > 0

    def test_is_stop_annotation(self, normalizer: TextNormalizer) -> None:
        html = "<p>The cat is on the mat.</p>"
        result = normalizer.normalize(html)
        stop_tokens = [t for t in result.sentences[0].tokens if t.is_stop]
        assert len(stop_tokens) > 0


class TestNormalizedDataclasses:
    def test_normalized_token(self) -> None:
        t = NormalizedToken(text="cat", lemma="cat", pos="NOUN", is_stop=False)
        assert t.text == "cat"
        assert t.pos == "NOUN"

    def test_normalized_sentence_empty(self) -> None:
        s = NormalizedSentence(text="")
        assert s.word_count == 0
        assert s.char_count == 0

    def test_normalized_chapter_empty(self) -> None:
        ch = NormalizedChapter()
        assert ch.word_count == 0
        assert ch.sent_count == 0
